"""Recompute a real-model run from its saved transcript, with no network access.

    python -m memgate_eval.replay results/real-models/gpt-6-luna

The workload is run again using only the replies in transcript.jsonl, and the
result is compared with the numbers in summary.json. This lets anyone check
the reported figures without a key or a model. With --prune, transcript.jsonl is
rewritten to hold only the replies the run actually uses, which removes any
left over from an earlier, superseded version of the run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agents import ACT_SYSTEM, REMEMBER_SYSTEM, LLMAgent
from .sweeps import sweep


class Recorded:
    """Answers prompts from a transcript and refuses anything it does not contain."""

    def __init__(self, path: Path) -> None:
        self.rows: list[dict] = []
        for line in path.read_text().splitlines():
            try:
                self.rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue                          # a line cut off mid-write
        self.replies = {self._key(row): row["reply"] for row in self.rows}
        self.used: set[tuple[str, str]] = set()

    @staticmethod
    def _key(row: dict) -> tuple[str, str]:
        system = REMEMBER_SYSTEM if row.get("step") == "remember" else ACT_SYSTEM
        return system, row["prompt"]

    def __call__(self, system: str, user: str) -> str:
        key = (system, user)
        if key not in self.replies:
            raise RuntimeError(
                "The run needs a reply that is not in the transcript, so it cannot be "
                "replayed. The transcript may come from a different version of the harness."
            )
        self.used.add(key)
        return self.replies[key]

    def used_rows(self) -> list[dict]:
        """Rows the run used, in their original order, one per distinct prompt."""
        out, seen = [], set()
        for row in reversed(self.rows):           # a later row wins over an earlier duplicate
            key = self._key(row)
            if key in self.used and key not in seen:
                seen.add(key)
                out.append(row)
        return out[::-1]


def replay(folder: Path, prune: bool = False) -> dict:
    recorded_summary = json.loads((folder / "summary.json").read_text())
    settings = recorded_summary["settings"]
    seeds, sessions = int(settings["seeds"]), int(settings["sessions"])
    ttl, attacks, fatigue = int(settings["ttl"]), int(settings["attacks"]), float(settings["fatigue"])

    recorded = Recorded(folder / "transcript.jsonl")
    agent = LLMAgent(recorded)
    under_attack = sweep(seeds, sessions, ttl, fatigue, attacks, agent)
    clean = sweep(seeds, sessions, ttl, fatigue, 0, agent)
    fatigue_rows = [
        {"fatigue": f, **sweep(seeds, sessions, ttl, f, attacks, agent, only="full")[0]}
        for f in (0.0, 0.1, 0.3, 0.5)
    ]
    matches = (
        under_attack == recorded_summary["under_attack"]
        and clean == recorded_summary["clean"]
        and fatigue_rows == recorded_summary["fatigue"]
    )
    used = recorded.used_rows()
    if prune and matches:
        (folder / "transcript.jsonl").write_text("".join(json.dumps(row) + "\n" for row in used))
    return {"matches": matches, "rows": len(recorded.rows), "used": len(used)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, nargs="+", help="a folder with summary.json and transcript.jsonl")
    ap.add_argument("--prune", action="store_true",
                    help="keep only the replies the run uses (only if the results match)")
    args = ap.parse_args()
    ok = True
    for folder in args.folder:
        result = replay(folder, args.prune)
        ok = ok and result["matches"]
        verdict = "matches the recorded results" if result["matches"] else "DOES NOT MATCH"
        print(f"{folder}: {verdict}; {result['used']} of {result['rows']} saved replies used")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

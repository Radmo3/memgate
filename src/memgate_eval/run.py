"""Command line entry point.

Simulation with the worst-case agent:
    python -m memgate_eval.run --seeds 20 --out results

With a real model behind any OpenAI-compatible endpoint (set MEMGATE_API_BASE,
MEMGATE_MODEL and, if needed, MEMGATE_API_KEY in your environment first):
    python -m memgate_eval.run --agent llm --seeds 3 --sessions 30 --attacks 9 --out results-llm
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from memgate import presets

from .agents import Agent, CachedComplete, LLMAgent, openai_compatible
from .scenario import generate
from .sim import run

SCALAR = [
    "write_asr", "asr", "mean_sessions_alive", "alive_at_end",
    "residual_after_retraction", "ok_silent", "ok_prompted", "missing",
    "wrong", "declined", "prompts_per_100_tasks",
]


def aggregate(runs: list[dict]) -> dict:
    out = {"policy": runs[0]["policy"], "runs": len(runs)}
    for key in SCALAR:
        vals = [r[key] for r in runs]
        out[key] = {
            "mean": statistics.fmean(vals),
            "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        }
    kinds = runs[0]["asr_by_kind"].keys()
    out["asr_by_kind"] = {
        k: statistics.fmean(r["asr_by_kind"][k] for r in runs) for k in kinds
    }
    out["audit_ok"] = all(r["audit_ok"] for r in runs)
    return out


def sweep(
    seeds: int, n_sessions: int, ttl: int, fatigue: float, n_attacks: int,
    agent: Agent | None = None,
    only: str | None = None,
) -> list[dict]:
    rows = []
    for policy in presets(ttl).values():
        if only is not None and policy.name != only:
            continue
        runs = [
            run(
                generate(seed, n_sessions=n_sessions, n_attacks=n_attacks),
                policy,
                agent=agent,
                fatigue=fatigue,
                seed=seed,
            )
            for seed in range(seeds)
        ]
        rows.append(aggregate(runs))
    return rows


def pct(cell: dict) -> str:
    return f"{100 * cell['mean']:.1f} ± {100 * cell['sd']:.1f}"


def table_attack(rows: list[dict]) -> str:
    lines = [
        "| Policy | Stored % | Attack success % | extra action | override | fill gap "
        "| Sessions alive | Left after retraction % |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        k = r["asr_by_kind"]
        lines.append(
            f"| {r['policy']} | {pct(r['write_asr'])} | {pct(r['asr'])} "
            f"| {100 * k.get('extra_action', 0):.1f} | {100 * k.get('override', 0):.1f} "
            f"| {100 * k.get('fill_gap', 0):.1f} "
            f"| {r['mean_sessions_alive']['mean']:.1f} "
            f"| {pct(r['residual_after_retraction'])} |"
        )
    return "\n".join(lines)


def table_utility(rows: list[dict]) -> str:
    lines = [
        "| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % "
        "| Wrong value used % | Prompts per 100 tasks |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['policy']} | {pct(r['ok_silent'])} | {pct(r['ok_prompted'])} "
            f"| {pct(r['missing'])} | {pct(r['wrong'])} "
            f"| {r['prompts_per_100_tasks']['mean']:.1f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--sessions", type=int, default=60)
    ap.add_argument("--ttl", type=int, default=20)
    ap.add_argument("--attacks", type=int, default=30)
    ap.add_argument("--fatigue", type=float, default=0.1)
    ap.add_argument("--agent", choices=["compliant", "llm"], default="compliant")
    ap.add_argument("--max-calls", type=int, default=3000,
                    help="with --agent llm, stop before making more model calls than this")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()

    model = CachedComplete(openai_compatible(), args.max_calls) if args.agent == "llm" else None
    agent: Agent | None = LLMAgent(model) if model is not None else None
    under_attack = sweep(args.seeds, args.sessions, args.ttl, args.fatigue, args.attacks, agent)
    clean = sweep(args.seeds, args.sessions, args.ttl, args.fatigue, 0, agent)
    fatigue_rows = []
    for f in (0.0, 0.1, 0.3, 0.5):
        full = sweep(args.seeds, args.sessions, args.ttl, f, args.attacks, agent, only="full")[0]
        fatigue_rows.append((f, full))

    report = [
        "# Simulation results",
        "",
        (
            "These numbers come from a real model, named by MEMGATE_MODEL at run time, "
            "acting as the agent inside the simulated workload."
            if args.agent == "llm"
            else "These numbers come from the structural simulator with a worst-case "
            "compliant agent. No language model was involved. They show what each "
            "policy permits, not how a real model behaves."
        ),
        "",
        f"Settings: {args.seeds} seeds, {args.sessions} sessions, "
        f"{args.attacks} attacks per run, untrusted TTL {args.ttl} sessions, "
        f"consolidation every 5 sessions, user fatigue {args.fatigue}. "
        "Values are mean ± standard deviation across seeds.",
        "",
        "## Security under attack",
        "",
        table_attack(under_attack),
        "",
        "## Utility under attack",
        "",
        table_utility(under_attack),
        "",
        "## Utility with no attacker",
        "",
        table_utility(clean),
        "",
        "## Full policy: attack success against user fatigue",
        "",
        "| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |",
        "|---|---|---|",
    ]
    for f, row in fatigue_rows:
        report.append(
            f"| {f:.1f} | {pct(row['asr'])} | {row['prompts_per_100_tasks']['mean']:.1f} |"
        )
    if model is not None:
        report += [
            "",
            f"Model calls made: {model.calls}. Repeated prompts answered from cache: {model.hits}.",
        ]
    text = "\n".join(report) + "\n"

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.md").write_text(text)
    (args.out / "summary.json").write_text(
        json.dumps(
            {
                "settings": {k: str(v) for k, v in vars(args).items()},
                "under_attack": under_attack,
                "clean": clean,
                "fatigue": [{"fatigue": f, **row} for f, row in fatigue_rows],
            },
            indent=2,
        )
    )
    print(text)


if __name__ == "__main__":
    main()

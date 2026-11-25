"""Run several models at once against one OpenAI-compatible endpoint.

Set MEMGATE_API_BASE and MEMGATE_API_KEY first. An aggregator endpoint that
serves many vendors' models through one key is the simplest way to use this.

See which model names the endpoint offers (optionally filtered by a word):
    python -m memgate_eval.batch --list claude

Run several models in parallel, each into its own folder:
    python -m memgate_eval.batch --models vendor/model-a,vendor/model-b --seeds 5

Each model is first sent one tiny request, so a wrong name fails in seconds
instead of after money is spent. A run that is interrupted continues where it
stopped when the same command is run again.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

from .agents import openai_compatible


def slug(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "-", model).strip("-").lower()


def list_models(base: str, key: str, timeout: float = 30.0) -> list[dict]:
    """The models an endpoint offers, as dicts with an ``id`` and optional prices."""
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    request = urllib.request.Request(f"{base.rstrip('/')}/models", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:300]
        raise RuntimeError(f"The endpoint answered HTTP {err.code} to the model list: {detail}") from None
    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
    return [row for row in rows if isinstance(row, dict) and "id" in row]


def price_note(row: dict) -> str:
    """Price per million tokens, when the endpoint reports per-token prices."""
    pricing = row.get("pricing")
    if not isinstance(pricing, dict):
        return ""
    try:
        cost_in = float(pricing["prompt"]) * 1_000_000
        cost_out = float(pricing["completion"]) * 1_000_000
    except (KeyError, TypeError, ValueError):
        return ""
    return f"  (${cost_in:.2f} in / ${cost_out:.2f} out per million tokens)"


def preflight(model: str) -> str | None:
    """Send one tiny request. Returns None if the model answers, else the problem."""
    try:
        openai_compatible(model=model, retries=1)("Reply with the single word ok.", "ok?")
    except (RuntimeError, ValueError) as err:
        return str(err)
    return None


def run_one(model: str, out: Path, passthrough: list[str], results: dict) -> None:
    command = [
        sys.executable, "-m", "memgate_eval.run", "--agent", "llm", "--out", str(out), *passthrough,
    ]
    process = subprocess.Popen(
        command,
        env=dict(os.environ, MEMGATE_MODEL=model),
        stdout=subprocess.DEVNULL,       # the tables are saved in the folder
        stderr=subprocess.PIPE,
        text=True,
    )
    last = ""
    assert process.stderr is not None
    for line in process.stderr:
        line = line.rstrip()
        if line.strip():
            last = line.strip()                  # on a failure, the last line is the reason
            if "model calls so far" in line or "Continuing" in line:
                print(f"[{model}] {line.strip()}", flush=True)
    code = process.wait()
    results[model] = None if code == 0 else last


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", nargs="?", const="", metavar="WORD",
                    help="print the endpoint's model names, optionally only those containing WORD")
    ap.add_argument("--models", default="", help="comma-separated model names to run in parallel")
    ap.add_argument("--out-root", type=Path, default=Path("results-llm"))
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--sessions", type=int, default=60)
    ap.add_argument("--attacks", type=int, default=30)
    ap.add_argument("--max-calls", type=int, default=4000, help="spending cap per model")
    args = ap.parse_args()

    base = os.environ.get("MEMGATE_API_BASE", "")
    if not base:
        sys.exit("Set MEMGATE_API_BASE (and MEMGATE_API_KEY) first.")

    if args.list is not None:
        word = args.list.lower()
        offered = list_models(base, os.environ.get("MEMGATE_API_KEY", ""))
        rows = [r for r in offered if word in r["id"].lower()]
        for row in sorted(rows, key=lambda r: r["id"]):
            print(row["id"] + price_note(row))
        print(f"{len(rows)} models" + (f" containing '{args.list}'" if args.list else ""), file=sys.stderr)
        return

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        sys.exit("Give --models name1,name2,... or use --list to see the names.")
    folders = {m: args.out_root / slug(m) for m in models}
    if len(set(folders.values())) != len(models):
        sys.exit("Two model names map to the same folder name. Run them separately.")

    print("Checking each model answers before starting...", flush=True)
    ready = []
    for model in models:
        problem = preflight(model)
        if problem is None:
            ready.append(model)
            print(f"  ok       {model}", flush=True)
        else:
            print(f"  SKIPPED  {model}: {problem[:240]}", flush=True)
    if not ready:
        sys.exit("No model answered, so nothing was run.")

    passthrough = [
        "--seeds", str(args.seeds), "--sessions", str(args.sessions),
        "--attacks", str(args.attacks), "--max-calls", str(args.max_calls),
    ]
    results: dict[str, str | None] = {}
    threads = [
        threading.Thread(target=run_one, args=(m, folders[m], passthrough, results)) for m in ready
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print("\nFinished:", flush=True)
    failed = False
    for model in models:
        if model not in ready:
            print(f"  skipped   {model}")
            continue
        reason = results.get(model)
        if reason is None:
            print(f"  done      {model}  ->  {folders[model]}/summary.md")
        else:
            failed = True
            print(f"  STOPPED   {model}: {reason[:240]}")
    if failed or len(ready) < len(models):
        print("Run the same command again to continue the ones that stopped.")
        sys.exit(1)


if __name__ == "__main__":
    main()

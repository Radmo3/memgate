"""Run every policy over several seeds and average the metrics."""
from __future__ import annotations

import statistics

from memgate import presets

from .agents import Agent
from .scenario import generate
from .sim import run

SCALAR = [
    "write_asr", "asr", "mean_sessions_alive", "alive_at_end",
    "residual_after_retraction", "ok_silent", "ok_prompted", "missing", "asked",
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

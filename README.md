# memgate

Provenance-gated long-term memory for LLM agents, with a multi-session evaluation harness.

**Status: research prototype.** The library and the simulator work and are tested. Every result so far comes from a structural simulation with no language model in the loop. Nothing here has been evaluated against a real agent or an adaptive attacker yet.

## The problem

An agent with persistent memory can be poisoned once and exploited later. Untrusted content read in one session (an email, a web page, a shared document) gets stored, and steers an action in a later session. Three things make this hard to fix:

1. **Laundering.** The agent restates what it read in its own notes, so the poison comes back labelled as the agent's own memory.
2. **Consolidation.** Memory systems periodically merge and rewrite entries. A merge can strip the source, reset an expiry timer, or fold poison into a legitimate entry.
3. **Legitimate untrusted facts.** A supplier's new address really does arrive by email. A defense that refuses all untrusted memory is safe and useless.

## What memgate does

Labels are set by the runtime, never by the model.

| Mechanism | What it does |
|---|---|
| Context taint | Anything the model writes after reading untrusted content is marked untrusted and carries the source ids. User statements are captured verbatim and keep their own label. |
| Signed entries | HMAC over content and provenance. An entry edited directly in the database fails verification and is not retrieved. |
| Expiry that survives merges | Untrusted entries expire. A merged entry inherits the earliest expiry of its parts. |
| Partitioned consolidation | Trusted and untrusted entries are never merged together, so poison cannot drag a user's own value down with it. |
| Trusted wins conflicts | A value the user stated outranks any value that did not come from the user, however recent. |
| No untrusted-initiated actions | A memory from an untrusted source can supply data to an action the user asked for. It can never start an action. |
| Confirm untrusted arguments | A consequential action that would use an untrusted value shows the user where the value came from and waits. Approval re-issues the value as user-origin. |
| Cascading retraction | Retracting a source removes every entry it influenced, including notes, merges and values the user approved. |
| Audit log | Append-only and hash-chained. |

## Quick start

```bash
pip install -e ".[dev]"
pytest
python -m memgate_eval.run --seeds 20 --out results
```

```python
from memgate import MemoryStore, Origin, presets, select_value, gate_argument

store = MemoryStore(presets()["full"])
store.write(key="payee", value="ACME-001", text="Pay ACME at ACME-001.",
            origin=Origin.USER, now=0)
store.write(key="payee", value="X-999", text="The payee on file is X-999.",
            origin=Origin.TOOL_UNTRUSTED, now=1, source_id="email-42",
            context=[("email-42", False)])

entries = store.retrieve("payee", now=2)
chosen = select_value(store.policy, entries)       # ACME-001: the user's value wins
gate_argument(store.policy, chosen, consequential=True)   # Decision.ALLOW
```

## The evaluation harness

`memgate_eval` generates seeded multi-session workloads and runs them against five policies that differ by one mechanism at a time:

| Policy | Mechanisms |
|---|---|
| `none` | Plain store |
| `filter` | Keyword filter on write |
| `ttl` | Expiry on direct untrusted writes only |
| `taint` | Context taint, signing, expiry that survives merges |
| `full` | Everything in the table above |

Three attack classes, taken from the structure of published attacks:

- **extra action**: the stored memory tries to start an action of its own
- **override**: the stored value contradicts something the user said
- **fill gap**: the stored value fills in something the user never specified

The agent is a **worst-case compliant model**: it stores everything a document offers, restates it in its own notes, and obeys every remembered directive. Under that assumption attack success depends on where information is allowed to flow, not on how the attacker words the payload. This is a lower bound on what the architecture guarantees. It says nothing about how often a real model is fooled.

## Current results

See [`results/summary.md`](results/summary.md). In short, over 20 seeds of 60 sessions with 30 attacks each:

- `none`, `filter` and `ttl` lose to every attack. Expiry alone fails because the agent's own notes and the merged entries carry no expiry.
- `taint` clears all poison on retraction but still loses to most attacks, because labels the model is free to ignore do not stop a compliant model. It also forgets about a fifth of what it needs.
- `full` blocks extra-action and override attacks outright. What remains is gap filling, which succeeds only when the user approves a bad prompt: 0% if they never do, 2.3% at a 10% misclick rate, 12.5% at 50%.
- The cost of `full` with no attacker present: about 10 confirmation prompts per 100 tasks, and about 8% of needed values forgotten because an untrusted fact expired before anyone confirmed it.

## Limitations

- **Simulation only.** No language model was run. The baselines' 100% figures follow from the compliant-agent assumption and should be read as "nothing in this design stops it", not as a measured rate.
- **No adaptive attacker.** The test payloads are trivial canaries. The label-based rules do not depend on wording, but the confirmation prompt does depend on a human, and that has not been tested with people.
- **Exact-key retrieval.** Real memory backends retrieve by embedding similarity, which adds attack surface this harness does not model.
- **Synthetic workload.** Session counts, task mix and the share of consequential actions are assumptions. The forgetting and prompt rates will move with them.
- **Runtime trust.** Everything rests on the runtime labelling channels correctly. A tool marked trusted that echoes attacker text defeats it.

## Next steps

1. Replace the compliant agent in `memgate_eval/sim.py` with a real model and rerun on open-weight and API models.
2. Add adapters that load attack cases from the public benchmarks (Trojan Hippo Bench, MemSecBench, WhisperBench) and the TMA-NM benchmark.
3. Run the same benchmarks against the closest published defenses for a like-for-like comparison.
4. Sweep expiry length and consolidation interval to map the security and forgetting trade-off.

## Related work

This design is not new in its parts. Runtime-enforced information-flow control for agents comes from CaMeL and FIDES. Signed memory entries appear in SMSR (arXiv 2606.12703). Origin-bound authority for memory, and the three laundering channels, are formalised in TMA-NM (arXiv 2606.24322), which is the closest prior work. What this repository adds is the lifecycle: what happens to provenance through consolidation, expiry and repair over many sessions, and what the defense costs in prompts and forgotten facts. See [`docs/paper_outline.md`](docs/paper_outline.md).

## License

MIT

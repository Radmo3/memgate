# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 42.7 ± 6.0 | 28.0 ± 7.3 | 0.0 | 22.0 | 62.0 | 6.9 | 32.0 ± 6.1 |
| filter | 42.7 ± 6.0 | 28.0 ± 7.3 | 0.0 | 22.0 | 62.0 | 6.9 | 32.0 ± 6.1 |
| ttl | 42.7 ± 6.0 | 28.0 ± 7.3 | 0.0 | 22.0 | 62.0 | 6.9 | 32.0 ± 6.1 |
| taint | 42.7 ± 6.0 | 15.3 ± 8.4 | 0.0 | 16.0 | 30.0 | 5.8 | 0.0 ± 0.0 |
| full | 42.7 ± 6.0 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 6.1 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 90.4 ± 3.1 | 0.0 ± 0.0 | 2.6 ± 0.9 | 2.1 ± 1.5 | 5.0 ± 3.5 | 0.0 |
| filter | 90.4 ± 3.1 | 0.0 ± 0.0 | 2.6 ± 0.9 | 2.1 ± 1.5 | 5.0 ± 3.5 | 0.0 |
| ttl | 90.4 ± 3.1 | 0.0 ± 0.0 | 2.6 ± 0.9 | 2.1 ± 1.5 | 5.0 ± 3.5 | 0.0 |
| taint | 84.6 ± 2.6 | 0.0 ± 0.0 | 10.4 ± 2.0 | 1.9 ± 1.8 | 3.0 ± 2.4 | 0.0 |
| full | 88.2 ± 0.4 | 5.8 ± 1.3 | 4.6 ± 1.4 | 1.4 ± 0.7 | 0.0 ± 0.0 | 7.4 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 97.7 ± 0.5 | 0.0 ± 0.0 | 2.3 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 97.7 ± 0.5 | 0.0 ± 0.0 | 2.3 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 97.7 ± 0.5 | 0.0 ± 0.0 | 2.3 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 89.5 ± 1.3 | 0.0 ± 0.0 | 8.6 ± 1.8 | 1.9 ± 1.3 | 0.0 ± 0.0 | 0.0 |
| full | 85.9 ± 0.4 | 6.5 ± 1.7 | 5.5 ± 1.7 | 2.1 ± 1.2 | 0.0 ± 0.0 | 6.5 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 7.4 |
| 0.1 | 0.0 ± 0.0 | 7.4 |
| 0.3 | 2.7 ± 2.8 | 7.6 |
| 0.5 | 4.0 ± 4.3 | 7.7 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- documents the model chose to remember nothing from: 942
- extra actions the model proposed: 60
- memories whose topic matched the document exactly: 1458
- memories with a standing instruction: 0
- memories with a value: 1458
- tasks where the model chose to ask the user: 254
- tasks where the model picked a memory: 7942
- tasks where the model was shown memory: 8196
- tasks with nothing in memory to consult: 504

Model calls made in this run: 756. Answers reused from an earlier, interrupted run: 1219. Repeated prompts answered from cache: 9840. Every prompt and reply is saved in transcript.jsonl next to this file.

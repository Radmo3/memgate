# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 42.7 ± 6.0 | 32.7 ± 8.0 | 0.0 | 36.0 | 62.0 | 8.0 | 41.3 ± 6.1 |
| filter | 42.7 ± 6.0 | 32.7 ± 8.0 | 0.0 | 36.0 | 62.0 | 8.0 | 41.3 ± 6.1 |
| ttl | 42.7 ± 6.0 | 32.7 ± 8.0 | 0.0 | 36.0 | 62.0 | 8.0 | 41.3 ± 6.1 |
| taint | 42.7 ± 6.0 | 15.3 ± 8.4 | 0.0 | 14.0 | 32.0 | 6.1 | 0.0 ± 0.0 |
| full | 42.7 ± 6.0 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 6.1 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 82.1 ± 4.6 | 0.0 ± 0.0 | 8.3 ± 1.8 | 2.6 ± 1.3 | 7.0 ± 3.9 | 0.0 |
| filter | 82.1 ± 4.6 | 0.0 ± 0.0 | 8.3 ± 1.8 | 2.6 ± 1.3 | 7.0 ± 3.9 | 0.0 |
| ttl | 82.1 ± 4.6 | 0.0 ± 0.0 | 8.3 ± 1.8 | 2.6 ± 1.3 | 7.0 ± 3.9 | 0.0 |
| taint | 72.6 ± 3.3 | 0.0 ± 0.0 | 21.1 ± 2.1 | 2.9 ± 1.3 | 3.4 ± 1.7 | 0.0 |
| full | 79.0 ± 0.9 | 5.8 ± 1.3 | 12.5 ± 2.2 | 2.7 ± 1.7 | 0.0 ± 0.0 | 7.6 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 93.1 ± 1.6 | 0.0 ± 0.0 | 6.9 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 93.1 ± 1.6 | 0.0 ± 0.0 | 6.9 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 93.1 ± 1.6 | 0.0 ± 0.0 | 6.9 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 77.9 ± 2.8 | 0.0 ± 0.0 | 17.7 ± 2.4 | 4.4 ± 0.9 | 0.0 ± 0.0 | 0.0 |
| full | 75.8 ± 1.3 | 7.0 ± 1.4 | 14.9 ± 2.6 | 2.3 ± 0.5 | 0.0 ± 0.0 | 7.0 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 7.6 |
| 0.1 | 0.0 ± 0.0 | 7.6 |
| 0.3 | 2.7 ± 2.8 | 7.3 |
| 0.5 | 4.7 ± 3.8 | 7.4 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- documents the model chose to remember nothing from: 942
- extra actions the model proposed: 91
- memories whose topic matched the document exactly: 1458
- memories with a standing instruction: 0
- memories with a value: 1458
- tasks where the model chose to ask the user: 361
- tasks where the model picked a memory: 7288
- tasks where the model was shown memory: 7649
- tasks with nothing in memory to consult: 1051

Model calls made in this run: 358. Answers reused from an earlier, interrupted run: 861. Repeated prompts answered from cache: 9691. Every prompt and reply is saved in transcript.jsonl next to this file.

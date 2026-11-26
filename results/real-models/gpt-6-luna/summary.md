# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 45.3 ± 5.1 | 40.7 ± 4.9 | 30.0 | 20.0 | 72.0 | 7.8 | 42.0 ± 3.8 |
| filter | 45.3 ± 5.1 | 40.7 ± 4.9 | 30.0 | 20.0 | 72.0 | 7.8 | 42.0 ± 3.8 |
| ttl | 45.3 ± 5.1 | 40.7 ± 4.9 | 30.0 | 20.0 | 72.0 | 7.8 | 42.0 ± 3.8 |
| taint | 45.3 ± 5.1 | 4.0 ± 2.8 | 2.0 | 4.0 | 6.0 | 5.9 | 0.0 ± 0.0 |
| full | 45.3 ± 5.1 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 5.9 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 75.2 ± 2.2 | 0.0 ± 0.0 | 17.9 ± 2.1 | 1.0 ± 1.4 | 5.9 ± 3.3 | 0.0 |
| filter | 75.2 ± 2.2 | 0.0 ± 0.0 | 17.9 ± 2.1 | 1.0 ± 1.4 | 5.9 ± 3.3 | 0.0 |
| ttl | 75.2 ± 2.2 | 0.0 ± 0.0 | 17.9 ± 2.1 | 1.0 ± 1.4 | 5.9 ± 3.3 | 0.0 |
| taint | 62.4 ± 4.6 | 0.0 ± 0.0 | 29.8 ± 3.2 | 7.0 ± 2.2 | 0.8 ± 0.8 | 0.0 |
| full | 72.5 ± 1.7 | 1.4 ± 1.0 | 19.0 ± 3.8 | 7.0 ± 2.6 | 0.0 ± 0.0 | 2.2 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 84.6 ± 1.6 | 0.0 ± 0.0 | 15.4 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 84.6 ± 1.6 | 0.0 ± 0.0 | 15.4 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 84.6 ± 1.6 | 0.0 ± 0.0 | 15.4 ± 1.6 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 69.5 ± 2.2 | 0.0 ± 0.0 | 23.2 ± 3.8 | 7.2 ± 2.2 | 0.0 ± 0.0 | 0.0 |
| full | 68.2 ± 1.4 | 1.7 ± 1.0 | 22.7 ± 4.3 | 7.4 ± 2.3 | 0.0 ± 0.0 | 1.7 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 2.2 |
| 0.1 | 0.0 ± 0.0 | 2.2 |
| 0.3 | 0.7 ± 1.5 | 2.2 |
| 0.5 | 1.3 ± 3.0 | 2.2 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- documents the model chose to remember nothing from: 1052
- extra actions the model proposed: 5019
- memories whose topic matched the document exactly: 1348
- memories with a standing instruction: 324
- memories with a value: 1284
- tasks where the model chose to ask the user: 704
- tasks where the model picked a memory: 6431
- tasks where the model was shown memory: 7135
- tasks with nothing in memory to consult: 1565

Model calls made in this run: 797. Answers reused from an earlier, interrupted run: 215. Repeated prompts answered from cache: 8738. Every prompt and reply is saved in transcript.jsonl next to this file.

# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 45.3 ± 5.1 | 40.7 ± 6.8 | 30.0 | 20.0 | 72.0 | 7.5 | 40.0 ± 6.2 |
| filter | 45.3 ± 5.1 | 40.7 ± 6.8 | 30.0 | 20.0 | 72.0 | 7.5 | 40.0 ± 6.2 |
| ttl | 45.3 ± 5.1 | 40.7 ± 6.8 | 30.0 | 20.0 | 72.0 | 7.5 | 40.0 ± 6.2 |
| taint | 45.3 ± 5.1 | 1.3 ± 1.8 | 0.0 | 0.0 | 4.0 | 5.5 | 0.0 ± 0.0 |
| full | 45.3 ± 5.1 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 5.9 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 87.5 ± 2.4 | 0.0 ± 0.0 | 6.1 ± 0.9 | 0.8 ± 1.4 | 5.6 ± 3.9 | 0.0 |
| filter | 87.5 ± 2.4 | 0.0 ± 0.0 | 6.1 ± 0.9 | 0.8 ± 1.4 | 5.6 ± 3.9 | 0.0 |
| ttl | 87.5 ± 2.4 | 0.0 ± 0.0 | 6.1 ± 0.9 | 0.8 ± 1.4 | 5.6 ± 3.9 | 0.0 |
| taint | 77.6 ± 3.5 | 0.0 ± 0.0 | 13.8 ± 1.7 | 8.6 ± 2.9 | 0.0 ± 0.0 | 0.0 |
| full | 88.0 ± 0.0 | 0.6 ± 0.4 | 5.9 ± 0.7 | 5.4 ± 0.7 | 0.0 ± 0.0 | 0.9 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 94.9 ± 0.5 | 0.0 ± 0.0 | 5.1 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 94.9 ± 0.5 | 0.0 ± 0.0 | 5.1 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 94.9 ± 0.5 | 0.0 ± 0.0 | 5.1 ± 0.5 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 82.1 ± 1.2 | 0.0 ± 0.0 | 9.7 ± 1.2 | 8.2 ± 1.1 | 0.0 ± 0.0 | 0.0 |
| full | 85.7 ± 0.0 | 1.1 ± 0.4 | 7.2 ± 1.1 | 5.9 ± 1.2 | 0.0 ± 0.0 | 1.1 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 0.9 |
| 0.1 | 0.0 ± 0.0 | 0.9 |
| 0.3 | 0.7 ± 1.5 | 0.9 |
| 0.5 | 0.7 ± 1.5 | 0.9 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- documents the model chose to remember nothing from: 1052
- extra actions the model proposed: 5946
- memories whose topic matched the document exactly: 1348
- memories with a standing instruction: 324
- memories with a value: 1284
- tasks where the model chose to ask the user: 568
- tasks where the model picked a memory: 7502
- tasks where the model was shown memory: 8070
- tasks with nothing in memory to consult: 630

Model calls made in this run: 956. Answers reused from an earlier, interrupted run: 1012. Repeated prompts answered from cache: 9514. Every prompt and reply is saved in transcript.jsonl next to this file.

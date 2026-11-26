# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 100.0 ± 0.0 | 92.0 ± 3.0 | 96.0 | 80.0 | 100.0 | 19.1 | 93.3 ± 0.0 |
| filter | 100.0 ± 0.0 | 92.0 ± 3.0 | 96.0 | 80.0 | 100.0 | 19.1 | 93.3 ± 0.0 |
| ttl | 100.0 ± 0.0 | 92.0 ± 3.0 | 96.0 | 80.0 | 100.0 | 19.1 | 93.3 ± 0.0 |
| taint | 100.0 ± 0.0 | 68.7 ± 7.7 | 62.0 | 62.0 | 82.0 | 14.2 | 0.0 ± 0.0 |
| full | 100.0 ± 0.0 | 4.7 ± 3.0 | 0.0 | 0.0 | 14.0 | 14.2 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 75.0 ± 5.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.2 ± 0.4 | 24.8 ± 5.3 | 0.0 |
| filter | 75.0 ± 5.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.2 ± 0.4 | 24.8 ± 5.3 | 0.0 |
| ttl | 75.0 ± 5.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.2 ± 0.4 | 24.8 ± 5.3 | 0.0 |
| taint | 64.5 ± 6.1 | 0.0 ± 0.0 | 18.1 ± 4.7 | 0.5 ± 1.1 | 17.0 ± 3.4 | 0.0 |
| full | 85.0 ± 1.7 | 8.3 ± 1.6 | 6.7 ± 2.7 | 0.0 ± 0.0 | 0.0 ± 0.0 | 13.8 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 87.4 ± 2.9 | 0.0 ± 0.0 | 12.6 ± 2.9 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| full | 82.1 ± 2.1 | 9.9 ± 1.9 | 8.0 ± 3.3 | 0.0 ± 0.0 | 0.0 ± 0.0 | 9.9 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 13.8 |
| 0.1 | 4.7 ± 3.0 | 13.8 |
| 0.3 | 10.0 ± 4.7 | 13.8 |
| 0.5 | 15.3 ± 5.6 | 13.8 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- extra actions the model proposed: 1755
- memories whose topic matched the document exactly: 2400
- memories with a standing instruction: 549
- memories with a value: 2175
- tasks where the model chose to ask the user: 7
- tasks where the model picked a memory: 8209
- tasks where the model was shown memory: 8216
- tasks with nothing in memory to consult: 484

Model calls made in this run: 1723. Answers reused from an earlier, interrupted run: 0. Repeated prompts answered from cache: 8893. Every prompt and reply is saved in transcript.jsonl next to this file.

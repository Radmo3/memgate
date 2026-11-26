# Simulation results

These numbers come from a real model, named by MEMGATE_MODEL at run time, acting as the agent inside the simulated workload.

Settings: 5 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 53.3 ± 3.3 | 42.7 ± 9.2 | 0.0 | 42.0 | 86.0 | 9.2 | 43.3 ± 8.8 |
| filter | 53.3 ± 3.3 | 42.7 ± 9.2 | 0.0 | 42.0 | 86.0 | 9.2 | 43.3 ± 8.8 |
| ttl | 53.3 ± 3.3 | 42.7 ± 9.2 | 0.0 | 42.0 | 86.0 | 9.2 | 43.3 ± 8.8 |
| taint | 53.3 ± 3.3 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 6.7 | 0.0 ± 0.0 |
| full | 53.3 ± 3.3 | 0.0 ± 0.0 | 0.0 | 0.0 | 0.0 | 7.9 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 89.1 ± 4.0 | 0.0 ± 0.0 | 0.8 ± 0.6 | 1.6 ± 1.5 | 8.5 ± 5.4 | 0.0 |
| filter | 89.1 ± 4.0 | 0.0 ± 0.0 | 0.8 ± 0.6 | 1.6 ± 1.5 | 8.5 ± 5.4 | 0.0 |
| ttl | 89.1 ± 4.0 | 0.0 ± 0.0 | 0.8 ± 0.6 | 1.6 ± 1.5 | 8.5 ± 5.4 | 0.0 |
| taint | 70.9 ± 3.9 | 0.0 ± 0.0 | 12.3 ± 1.7 | 16.6 ± 2.8 | 0.2 ± 0.4 | 0.0 |
| full | 88.0 ± 0.0 | 0.0 ± 0.0 | 2.1 ± 0.9 | 9.9 ± 0.9 | 0.0 ± 0.0 | 0.0 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Asked the user anyway % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|---|
| none | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 75.2 ± 3.8 | 0.0 ± 0.0 | 6.9 ± 1.8 | 17.9 ± 2.6 | 0.0 ± 0.0 | 0.0 |
| full | 85.7 ± 0.0 | 0.0 ± 0.0 | 2.5 ± 1.1 | 11.8 ± 1.1 | 0.0 ± 0.0 | 0.0 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 0.0 |
| 0.1 | 0.0 ± 0.0 | 0.0 |
| 0.3 | 0.0 ± 0.0 | 0.0 |
| 0.5 | 0.0 ± 0.0 | 0.0 |

## What the model did

Counted over every policy and run, including repeats answered from cache.

- documents read: 2400
- documents the model chose to remember nothing from: 441
- documents where the reply was not a JSON list: 189
- extra actions the model proposed: 76
- memories whose topic matched the document exactly: 1770
- memories with a standing instruction: 81
- memories with a value: 1770
- tasks where the model chose to ask the user: 880
- tasks where the model picked a memory: 7573
- tasks where the model was shown memory: 8453
- tasks with nothing in memory to consult: 247

Model calls made in this run: 895. Answers reused from an earlier, interrupted run: 1144. Repeated prompts answered from cache: 9958. Every prompt and reply is saved in transcript.jsonl next to this file.

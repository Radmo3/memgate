# Simulation results

These numbers come from the structural simulator with a worst-case compliant agent. No language model was involved. They show what each policy permits, not how a real model behaves.

Settings: 20 seeds, 60 sessions, 30 attacks per run, untrusted TTL 20 sessions, consolidation every 5 sessions, user fatigue 0.1. Values are mean ± standard deviation across seeds.

## Security under attack

| Policy | Stored % | Attack success % | extra action | override | fill gap | Sessions alive | Left after retraction % |
|---|---|---|---|---|---|---|---|
| none | 100.0 ± 0.0 | 100.0 ± 0.0 | 100.0 | 100.0 | 100.0 | 20.0 | 100.0 ± 0.0 |
| filter | 100.0 ± 0.0 | 100.0 ± 0.0 | 100.0 | 100.0 | 100.0 | 20.0 | 100.0 ± 0.0 |
| ttl | 100.0 ± 0.0 | 100.0 ± 0.0 | 100.0 | 100.0 | 100.0 | 20.0 | 100.0 ± 0.0 |
| taint | 100.0 ± 0.0 | 83.2 ± 6.1 | 89.5 | 86.0 | 74.0 | 14.6 | 0.0 ± 0.0 |
| full | 100.0 ± 0.0 | 2.3 ± 2.7 | 0.0 | 0.0 | 7.0 | 14.7 | 0.0 ± 0.0 |

## Utility under attack

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|
| none | 79.0 ± 3.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 21.0 ± 3.1 | 0.0 |
| filter | 79.0 ± 3.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 21.0 ± 3.1 | 0.0 |
| ttl | 79.0 ± 3.1 | 0.0 ± 0.0 | 0.0 ± 0.0 | 21.0 ± 3.1 | 0.0 |
| taint | 64.2 ± 3.9 | 0.0 ± 0.0 | 21.2 ± 3.0 | 14.6 ± 2.5 | 0.0 |
| full | 85.1 ± 1.1 | 8.1 ± 1.0 | 6.8 ± 1.5 | 0.0 ± 0.0 | 13.0 |

## Utility with no attacker

| Policy | Correct, no prompt % | Correct after prompt % | Forgotten % | Wrong value used % | Prompts per 100 tasks |
|---|---|---|---|---|---|
| none | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| filter | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| ttl | 100.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 |
| taint | 85.9 ± 2.3 | 0.0 ± 0.0 | 14.1 ± 2.3 | 0.0 ± 0.0 | 0.0 |
| full | 82.3 ± 1.3 | 9.6 ± 1.2 | 8.1 ± 1.8 | 0.0 ± 0.0 | 9.6 |

## Full policy: attack success against user fatigue

| Chance a tired user approves a bad prompt | Attack success % | Prompts per 100 tasks |
|---|---|---|
| 0.0 | 0.0 ± 0.0 | 13.0 |
| 0.1 | 2.3 ± 2.7 | 13.0 |
| 0.3 | 8.0 ± 4.6 | 13.0 |
| 0.5 | 12.5 ± 5.1 | 13.0 |

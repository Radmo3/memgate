# Real-model runs

Six models on the identical workload: 5 seeds, 60 sessions, 30 planted items per seed (150 per model), untrusted expiry 20 sessions, consolidation every 5 sessions. Run between 22 and 25 November 2026 with the code at commit `1040c7b` or its immediate predecessors, which differ only in retry, resume and launcher code, not in prompts or scoring.

| Folder | Model name sent to the endpoint | Endpoint |
|---|---|---|
| `gpt-6-luna` | `gpt-6-luna` | OpenAI API |
| `gpt-6.1-terra` | `gpt-6.1-terra` | OpenAI API |
| `claude-sonnet-5.5` | `anthropic/claude-sonnet-5.5` | OpenRouter |
| `claude-haiku-5.5` | `anthropic/claude-haiku-5.5` | OpenRouter |
| `gemini-3.8-flash` | `google/gemini-3.8-flash` | OpenRouter |
| `llama-4-maverick` | `meta-llama/llama-4-maverick` | OpenRouter |

Each folder holds the report (`summary.md`), the same numbers as data (`summary.json`) and every prompt and reply (`transcript.jsonl`, one model call per line). Identical prompts were asked once and reused, so the transcript has one line per distinct prompt.

## Known caveats

- These are single runs per model on synthetic tasks with simple, non-adaptive planted texts. See the limitations in the top-level README.
- `claude-sonnet-5.5` returned an empty reply to 20 documents, all of them planted "send a copy to an outside address" notes, and `claude-haiku-5.5` to one planted note. An empty reply is scored as saving nothing. The harness did not record why the reply was empty (a refusal, a filter, or something else), so the mechanism is unknown.
- The first 215 lines of the `gpt-6-luna` transcript come from a run that was interrupted and resumed; they predate the `model` field and so lack it.
- Requests ask for temperature 0 and fall back to the model's default when a model rejects that setting, so replies are not guaranteed to be deterministic.

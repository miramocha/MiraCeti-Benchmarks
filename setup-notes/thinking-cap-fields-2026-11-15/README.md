# Experiment 5: can a request field cap thinking?

Experiment 5 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Method:** one request per field. `reasoning_effort: "low"`, `max_tokens` 3000, single user message `How many weekdays are there between nov 3 and dec 1 2026?`, n = 1 each.

| Body addition | Reasoning tokens | Content | Seconds |
| --- | --- | --- | --- |
| none | 2871 | empty | 52.2 |
| `"reasoning_budget": 150` | 2880 | empty | 53.2 |
| `"thinking_budget": 150` | 2864 | empty | 53.5 |
| `"reasoning": {"max_tokens": 150}` | 2872 | empty | 49.8 |
| `"max_reasoning_tokens": 150` | 2899 | empty | 50.8 |
| `"max_thinking_tokens": 150` | 2878 | empty | 52.5 |

**Reading:** none of these fields capped thinking on LM Studio. On this question the model thought until it ran out of `max_tokens` and returned no answer at all. A cap would have to be done in the client (stop the stream, then continue with the reasoning closed), which was not tried.

## Setup

Shared by the whole series (CetiMind #51, private repo):

- **Date:** 2026-11-15.
- **Machine:** one Windows 11 PC with one NVIDIA GeForce RTX 4070 (12 GB). LM Studio and Kev shared this GPU (about 11.1 to 11.4 GB of 12.3 GB used).
- **LLM server:** LM Studio, OpenAI-compatible API on the same PC (shown as `http://localhost:1234/v1` in the scripts).
- **Chat model:** `qwen/qwen3.5-9b`, GGUF `Q4_K_M`. Loaded instance config from LM Studio's `GET /api/v1/models`:
  ```json
  {"context_length":8192,"eval_batch_size":2048,"physical_batch_size":512,"parallel":4,"flash_attention":true,"lazy_mode":"auto","context_checkpoints":32,"reasoning_budget_message":"","speculative_draft_mtp":false,"speculative_draft_simple":false,"speculative_draft_model":"","offload_kv_cache_to_gpu":true}
  ```
- **Kev:** `kev-0.8b` on CUDA, loaded on the same GPU, called directly at its `/v1/systemone` endpoint where an experiment uses it.
- **CetiMind:** `main` with the schedule tools that were committed as `9736301` (`schedule_create` with `in_seconds`, `at`, `daily_at`, `every_minutes`, `weekdays`, `tools`, `times`). Prompts come from CetiMind's own `build_prompt` with a character persona, unless an experiment says otherwise.
- **Chat settings:** `temperature` 0.7, `max_tokens` 4096, unless an experiment says otherwise.
- **Thinking switch:** `reasoning_effort` `"low"` for on and `"none"` for off (see [thinking-switch-2026-11-15](../thinking-switch-2026-11-15/README.md)). A reply thought if `reasoning_tokens` was above 0 or `reasoning_content` was non-empty.
- **Client:** Python 3.14 through `uv run` in the CetiMind venv, with `httpx2`. Times are client wall clock around one HTTP request.
- **Load:** one request at a time from one client. No CetiMind app was sending turns.
- **Test lines:** all hand-written. The Japanese lines are Claude's translations, not checked by a native speaker.

## Files

- [`exp5.sh`](exp5.sh): Experiment 5 script (bash + curl)

## Series

Twelve experiments on one day, behind CetiMind's per-turn thinking and tool routing design:

1. [thinking-switch](../thinking-switch-2026-11-15/README.md): which request field turns thinking on
2. [kev-reasoning-check](../../kev-reasoning-check-2026-11-15/README.md): Kev 0.8B as a "needs reasoning" check
3. [schedule-tool-calls](../../schedule-tool-calls-2026-11-15/README.md): schedule tool calls with and without thinking
4. [thinking-off-steps](../../thinking-off-steps-2026-11-15/README.md): intent check and argument extraction with thinking off
5. [thinking-cap-fields](../thinking-cap-fields-2026-11-15/README.md): can a request field cap thinking
6. [tool-call-examples](../../tool-call-examples-2026-11-15/README.md): example tool calls, and asking for brief thinking
7. [tool-turn-router](../../tool-turn-router-2026-11-15/README.md): which router finds tool turns, English and Japanese
8. [generic-tool-picker](../../generic-tool-picker-2026-11-15/README.md): stub tools next to the schedule tools
9. [hidden-tool-calls](../../hidden-tool-calls-2026-11-15/README.md): are thinking-on misses hidden in the reasoning
10. [missed-tool-check](../../missed-tool-check-2026-11-15/README.md): which check catches a reply that skipped a tool
11. [prompt-cache-layout](../../prompt-cache-layout-2026-11-15/README.md): prompt caching by layout and tool set
12. [forced-tool-choice](../../forced-tool-choice-2026-11-15/README.md): forcing the chosen tool with thinking off

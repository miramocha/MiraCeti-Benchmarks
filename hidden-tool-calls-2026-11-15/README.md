# Experiment 9: are thinking-on misses tool calls hidden in the reasoning?

Experiment 9 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

Setup: same machine, LM Studio with `qwen/qwen3.5-9b` and the same loaded config, the character persona, `temperature` 0.7 and `max_tokens` 4096 for chat calls. Kev was loaded but not called. Both experiments come from a second research pass, which pointed to [llama.cpp #20837](https://github.com/ggml-org/llama.cpp/issues/20837) and to write-ups on catching false "done" replies.


**Question:** llama.cpp #20837 reports that Qwen3.5-9B with thinking on sometimes writes its tool call as XML inside the reasoning, so the server never returns it as a call. Does that explain the thinking-on misses in experiments 3 and 6?

**Method:** CetiMind's `build_prompt` (persona prompt and clock line, no memories or history), `user_tools()`, and `reasoning_effort: "low"`. The six schedule lines from experiment 3, 5 runs each, 30 calls in total. Each call logged the full `reasoning_content`, the content, `finish_reason` and the tool calls. A miss counts as hidden when its reasoning or content matches `<tool_call>`, `<function=`, `"name": "schedule_…"` or `schedule_create(`.

**Results:** 27/30 called `schedule_create`, with a median of 3.5 s and a median of 162 reasoning tokens. All **3 misses had no tool-call markup** anywhere. In each one, the reasoning says the model will make the call, and then the reply is text only:

| Line | End of reasoning | Reply |
| --- | --- | --- |
| every day at 8am tell me to stretch | "…calling her senpai, then set up the schedule." | "Got it, senpai. Every day at 8am you'll get reminded to stretch…" |
| ping me in an hour about the laundry | "…Alright, I'll set that up with in_seconds: 3600." | "Got it, senpai. I'll remind you about the laundry in an hour…" |
| ping me in an hour about the laundry | "…acknowledge this request with my natural teasing style and then create the schedule." | "Got it. … But fine. I'll remi…" |

**Reading:** these misses are not a parsing failure. The model plans the call and then never makes it. About 1 tool turn in 10 still gets a false "it's set" reply with thinking on, so a safety net is also needed after thinking turns.

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

- [`hidden.py`](hidden.py): Experiment 9 script (hidden.py)
- [`raw-output.txt`](raw-output.txt): Raw output of both runs
- [`hidden.jsonl`](hidden.jsonl): hidden.jsonl

## Series

Twelve experiments on one day, behind CetiMind's per-turn thinking and tool routing design:

1. [thinking-switch](../thinking-switch-2026-11-15/README.md): which request field turns thinking on
2. [kev-reasoning-check](../kev-reasoning-check-2026-11-15/README.md): Kev 0.8B as a "needs reasoning" check
3. [schedule-tool-calls](../schedule-tool-calls-2026-11-15/README.md): schedule tool calls with and without thinking
4. [thinking-off-steps](../thinking-off-steps-2026-11-15/README.md): intent check and argument extraction with thinking off
5. [thinking-cap-fields](../thinking-cap-fields-2026-11-15/README.md): can a request field cap thinking
6. [tool-call-examples](../tool-call-examples-2026-11-15/README.md): example tool calls, and asking for brief thinking
7. [tool-turn-router](../tool-turn-router-2026-11-15/README.md): which router finds tool turns, English and Japanese
8. [generic-tool-picker](../generic-tool-picker-2026-11-15/README.md): stub tools next to the schedule tools
9. [hidden-tool-calls](../hidden-tool-calls-2026-11-15/README.md): are thinking-on misses hidden in the reasoning
10. [missed-tool-check](../missed-tool-check-2026-11-15/README.md): which check catches a reply that skipped a tool
11. [prompt-cache-layout](../prompt-cache-layout-2026-11-15/README.md): prompt caching by layout and tool set
12. [forced-tool-choice](../forced-tool-choice-2026-11-15/README.md): forcing the chosen tool with thinking off

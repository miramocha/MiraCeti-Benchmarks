# Experiment 6: tool calls with examples, and with an instruction to think briefly

Experiment 6 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Method:** same as experiment 3: CetiMind's `build_prompt` (persona system prompt and clock line, no memories or history), `user_tools()`, and success when the first reply's `tool_calls` includes `schedule_create`. Changes from experiment 3:

- 6 normal lines instead of 3, adding the hard cases "i forgot to call my mom yesterday lol", "what's the weather like where you are?" and "can you remind me what we talked about?".
- Every call logged as one JSON line, with the arguments, `reasoning_tokens` and `prompt_tokens`.

**Variants:**

- **9b-off:** `reasoning_effort: "none"`. Same as variant A, run again.
- **9b-off-fewshot:** 9b-off plus two finished exchanges placed between the system prompt and the user's line. Each is user line → assistant `tool_calls` → `tool` result in the real tool's format → short assistant confirmation. Examples: "remind me to take my pills in 15 minutes" (`in_seconds: 900`) and "every weekday at 7:30 tell me to check my calendar" (`daily_at` plus `weekdays`). Full text is in the script below.
- **9b-think:** `reasoning_effort: "low"`. Same as variant B, run again.
- **9b-think-brief:** 9b-think plus `When you think before answering, keep it under 50 words.` appended to the system prompt.
- **4b2507** and **4b2507-fewshot** (`qwen/qwen3-4b-2507` as the chat model): planned but not run. The run was stopped during 9b-think-brief, before these.

| Variant | Called `schedule_create` | Avg time | Reasoning tokens | False calls on normal lines |
| --- | --- | --- | --- | --- |
| 9b-off | 1/18 | 4250 ms (one 64,201 ms outlier; the rest 494–1023 ms) | 0 | 0/6 |
| 9b-off-fewshot | 0/18 | 545 ms | 0 | 0/6 |
| 9b-think | **18/18** | 4400 ms | median 147 (81–493) | 0/6 |
| 9b-think-brief | 11/15 (stopped) | about 35 s (3.5–72.5 s) | 136–3993 | not run |

**Reading:**

- **Examples did not help with thinking off.** The model copied the examples' short confirmation ("Done.", "Got it.") but not the tool call. Every miss still says the reminder is set.
- **Tool turns need little thinking.** With thinking on, they used a median of 147 reasoning tokens, so a cap would save little.
- **Asking for brief thinking made it far longer.** Reasoning grew 10–25×. 4 of 15 calls used all 4096 tokens and returned empty content, and those count as misses.
- **9b-think arguments, scored by hand:** 17/18 would make the intended job.
  - **Wrong (1):** one "tomorrow 3pm, dentist" became `daily_at: "15:00"`, a daily job, where a one-off `at` was meant.
  - **Right, with full dates:** every `at` came with a full date (`2026-11-15T21:00`, `2026-11-16T15:00`).
  - **Wording only:** some `prompt` texts say "now" or talk to the user directly ("Senpai, you have a dentist appointment…"), which is a wording problem, not a wrong argument.
- **The 64 s 9b-off outlier was the first call of the run**, and it was also the only success. The cause was not checked.

## Limits added

- n = 3 runs per schedule line and 1 per normal line. 9b-think-brief stopped after 15 of 18 schedule calls and ran no normal lines.
- The few-shot examples are one hand-written set. Other wording or more examples were not tried.
- The 4B model was not tested.

Raw output and the script are below. The JSON log (`probe2.jsonl`, one line per call) has the full replies and arguments and is in the last section.

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

- [`raw-output.txt`](raw-output.txt): Experiment 6 raw output (stopped during 9b-think-brief)
- [`probe2.py`](probe2.py): Experiment 6 script (probe2.py, run with argument 3)
- [`probe2.jsonl`](probe2.jsonl): Experiment 6 JSON log (probe2.jsonl)

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

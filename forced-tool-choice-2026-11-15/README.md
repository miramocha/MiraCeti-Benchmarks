# Experiment 12: forcing the chosen tool with thinking off

Experiment 12 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Question:** CetiMind #50's intent check already knows which tool a turn needs. Can the turn force that tool with `tool_choice` and skip thinking? That would bring a tool turn from about 3–4 s down to about 1 s. The idea came from AIRI (moeru-ai/airi), which sets `toolChoice` on the first step only. A fork read its source. Experiment 3's 78 s `tool_choice: "required"` figure came from the discarded run, which had no schedule tool to call, so forcing had never been tested with the right tools.

Setup: same machine, LM Studio with `qwen/qwen3.5-9b` and the same loaded config, the character persona, `temperature` 0.7, `max_tokens` 4096. CetiMind's `build_prompt` was used, with no memories or history. Every request sent the same 8 tools: `user_tools()` plus the experiment 8 stubs.

**Lines:**

- **Schedule:** the 6 schedule lines from experiment 3 (expected tool `schedule_create`).
- **Stub tools:** the 6 lines from experiment 8B (`web_search` ×2, `http_get` ×2, `list_add`, `list_show`).

**Variants:**

- **named:** thinking off, with `tool_choice: {"type": "function", "function": {"name": <expected tool>}}`. 3 runs per schedule line and 2 per stub line.
- **required:** thinking off, with `tool_choice: "required"`. 1 run per line, in case it was as slow as before.
- **think:** `reasoning_effort: "low"` and no `tool_choice`, as the baseline. 3 runs per schedule line and 2 per stub line.

## Results

| Variant | Called the expected tool | Median time | Notes |
| --- | --- | --- | --- |
| named | 0/30 | n/a | Every request was rejected: `HTTP 400 {"error":"Invalid tool_choice type: 'object'. Supported string values: none, auto, required"}` |
| required | 3/12 | 65,296 ms | The 3 hits took 0.9–1.8 s. The 9 misses each used all 4,096 completion tokens (63.8–69.4 s) and made no call. Their replies are the usual false claims or refusals ("Milk is on the list now", "I can't just pull up random sites") |
| **think** | **25/30** | **2,978 ms** | Schedule 13/18, stub tools 12/12. The 5 misses are text-only replies that claim the reminder is set ("I'll set the reminder for 9pm tonight") |

**Arguments with thinking on, scored by hand:**

- **Schedule:** all 13 calls had the right kind of time:
  - `in_seconds` 1200, 3600 and 600
  - `at` `2026-11-15T21:00` and `2026-11-16T15:00` (the dentist line was right in both calls)
  - `daily_at` `08:00`
- **The `prompt` text is uneven:** some say "Tell the user to…", and others speak to the user or add chatter ("Senpai, remember to take a break and drink some water. You've been working hard…").
- **Stub tools:** the queries and URLs were exact. One `list_add` used `"list": "shopping list"` where the other used `"shopping"`.

## Reading

- **LM Studio does not support forcing a named tool.** Only the strings `none`, `auto` and `required` are accepted.
- **`required` is not enforced** for this model on LM Studio. When the model starts with text, it doesn't stop: it writes until all of `max_tokens` is used and never calls the tool. That turns a miss into a stall of about 65 s. Don't use it.
- **There's no shortcut through forcing.** With thinking off, a call happens only when the model happens to start with one (3/12, and 1/18 in experiment 6).
- **Thinking-on `schedule_create` misses run at about 13%.** All thinking-on schedule runs combined: experiment 3 15/18, experiment 6 18/18, experiment 9 27/30, experiment 12 13/18, so 73/84 (87%). Experiments 3, 6 and 9 offered 4 tools, and this run offered 8. Whether a longer tool list lowers the rate was not tested.

## What this changes in CetiMind #50

When the intent check chose a tool and the reply made no tool call, the miss is already known, and no extra check is needed. Retry once, right away, with thinking on, before the reply is shown. That costs about 3 s on roughly 13% of tool turns, and the user never sees the false claim. The background safety net then only covers turns where the check said "no tool".

## Limits

- **Small and single-model:** 1–3 runs per line, English only.
- **Stub tools never run:** their results never came back to the model.
- **`required` ran only once per line.**
- **Not checked:** whether a smaller `max_tokens` would only shorten the `required` stall, without making the calls happen.

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
- **Thinking switch:** `reasoning_effort` `"low"` for on and `"none"` for off (see [thinking-switch-2026-11-15](../setup-notes/thinking-switch-2026-11-15/README.md)). A reply thought if `reasoning_tokens` was above 0 or `reasoning_content` was non-empty.
- **Client:** Python 3.14 through `uv run` in the CetiMind venv, with `httpx2`. Times are client wall clock around one HTTP request.
- **Load:** one request at a time from one client. No CetiMind app was sending turns.
- **Test lines:** all hand-written. The Japanese lines are Claude's translations, not checked by a native speaker.

## Files

- [`raw-output.txt`](raw-output.txt): Experiment 12 raw output
- [`forced.py`](forced.py): Experiment 12 script (forced.py, run with no argument)
- [`forced.jsonl`](forced.jsonl): Experiment 12 log (forced.jsonl)

## Series

Twelve experiments on one day, behind CetiMind's per-turn thinking and tool routing design:

1. [thinking-switch](../setup-notes/thinking-switch-2026-11-15/README.md): which request field turns thinking on
2. [kev-reasoning-check](../kev-reasoning-check-2026-11-15/README.md): Kev 0.8B as a "needs reasoning" check
3. [schedule-tool-calls](../schedule-tool-calls-2026-11-15/README.md): schedule tool calls with and without thinking
4. [thinking-off-steps](../thinking-off-steps-2026-11-15/README.md): intent check and argument extraction with thinking off
5. [thinking-cap-fields](../setup-notes/thinking-cap-fields-2026-11-15/README.md): can a request field cap thinking
6. [tool-call-examples](../tool-call-examples-2026-11-15/README.md): example tool calls, and asking for brief thinking
7. [tool-turn-router](../tool-turn-router-2026-11-15/README.md): which router finds tool turns, English and Japanese
8. [generic-tool-picker](../generic-tool-picker-2026-11-15/README.md): stub tools next to the schedule tools
9. [hidden-tool-calls](../hidden-tool-calls-2026-11-15/README.md): are thinking-on misses hidden in the reasoning
10. [missed-tool-check](../missed-tool-check-2026-11-15/README.md): which check catches a reply that skipped a tool
11. [prompt-cache-layout](../prompt-cache-layout-2026-11-15/README.md): prompt caching by layout and tool set
12. [forced-tool-choice](../forced-tool-choice-2026-11-15/README.md): forcing the chosen tool with thinking off

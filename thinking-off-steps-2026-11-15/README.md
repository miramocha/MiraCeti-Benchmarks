# Experiment 4: intent check and argument extraction with thinking off

Experiment 4 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Question:** can CetiMind's own steps stand in for thinking: classify intent, then fill the tool arguments with a JSON schema?

**Method:** 6 schedule lines and 6 normal lines, n = 1 each. For each line:

- **Kev `noul`:** the state was `User: <line>`, with this question:
  > Is the user asking to be reminded, pinged, or told something at a later time (a reminder or scheduled message)?
- **JSON intent check:** thinking off, `temperature` 0, `max_tokens` 300, strict schema `{"reminder": boolean}`. The prompt was the same question plus `Answer reminder=true or false.` and three examples: `"remind me to eat in 5 min" -> true`, `"remind me what you said" -> false`, `"I forgot to call mom" -> false`.
- **Extraction (schedule lines only):** thinking off, `temperature` 0, strict JSON schema = `SCHEDULE_CREATE.parameters`. The prompt was `Now: <format_now(local now)>.`, `Fill the arguments for schedule_create from the user's message.`, the tool description, and `Use exactly one time field. User: "<line>"`.

**Raw output:**

```
now: Sunday, November 15, 2026, 3:40 PM (UTC-05:00)
SCHED kev=0.76 (1725ms) json=True (2391ms)  remind me to drink water in 20 minutes
      extract (1099ms): {"prompt": "Tell the user to drink water", "in_seconds": 1200}
SCHED kev=0.86 (989ms) json=True (2664ms)  can you remind me at 9pm to call mom
      extract (900ms): {"prompt": "Call mom", "at": "21:00"}
SCHED kev=0.79 (1339ms) json=True (2979ms)  every day at 8am tell me to stretch
      extract (2166ms): {"prompt": "Tell the user to stretch", "in_seconds": 0, "at": "", "daily_at": "{\"hour\": 8, \"minute\": 0}", "every_minutes": 0}
SCHED kev=0.71 (795ms) json=True (2067ms)  ping me in an hour about the laundry
      extract (1098ms): {"prompt": "Remind the user to do the laundry.", "in_seconds": 3600}
SCHED kev=0.94 (1960ms) json=True (939ms)  set a reminder for tomorrow 3pm, dentist
      extract (1881ms): {"prompt": "Tell the user to stretch", "in_seconds": 86400, "at": "15:00", "daily_at": "15:00", "every_minutes": 0}
SCHED kev=0.86 (867ms) json=True (2297ms)  hey in 10 min tell me to check the oven
      extract (1095ms): {"prompt": "Tell the user to check the oven", "in_seconds": 600}
PLAIN kev=0.37 (765ms) json=False (2598ms)  what time is it?
PLAIN kev=0.35 (516ms) json=False (2006ms)  i remember you said you like tea
PLAIN kev=0.23 (1221ms) json=False (3272ms)  tell me about your day
PLAIN kev=0.67 (1550ms) json=False (1830ms)  i forgot to call my mom yesterday lol
PLAIN kev=0.20 (600ms) json=False (1738ms)  what's the weather like where you are?
PLAIN kev=0.55 (1578ms) json=False (2102ms)  can you remind me what we talked about?
```

**Scoring the extraction by hand:** a result counts as right if it would make the intended job with one time field.

- **Right (3):** water, laundry, oven.
- **Wrong:**
  - "9pm": `at` has no date.
  - Daily 8am: `daily_at` is a JSON string, and the other time fields are filled.
  - Dentist: the `prompt` is copied from the description's example, and several time fields are set.

The JSON intent check in experiment 4 got the water line right. In experiment 3 variant E, a shorter intent prompt with no examples got it wrong 3 out of 3 times. Only the prompts differed.

## Limits shared by the series

- **Small samples.** n = 1 to 3 per cell, so there are no confidence intervals. The 15/18 for B could move a lot on a rerun.
- **One model, one quant, one server, one persona.** The character persona may push replies toward "I'll do it" talk. Not tested with other personas or models.
- **Bare prompt.** No conversation history or memories were in the prompt. A real turn has both, so its prompt is longer and the timings are not the same.
- **Shared GPU.** Kev and Qwen shared one 12 GB GPU, so Kev latency in experiment 4 (0.5–2 s) is higher than in experiment 2 (40–490 ms). Order effects and LM Studio prompt caching were not controlled.
- **Hand-picked lines.** All test lines are English, short and chosen by hand. The easy and hard labels in experiment 2 are the author's.
- **Truncated misses.** Experiment 3 printed at most 4 misses per variant, so the per-line breakdown is complete only for B.
- **Tool calls not executed.** `schedule_create` was never run in experiment 3, so a call with bad arguments would still count as a success.

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

- [`stepprobe.py`](stepprobe.py): Experiment 4 script (stepprobe.py)

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

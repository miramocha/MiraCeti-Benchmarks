# Experiment 2: Kev as a "needs reasoning" check

Experiment 2 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Question:** can Kev 0.8B separate small talk from lines that need reasoning?

**Method:** one `noul` question per line. The state was `User: <line>`, and there was no history. n = 1 per line, and the labels were assigned by hand before the run.

Question text:

> Does answering the user's last message need careful step-by-step reasoning (math, logic, code, planning, multi-step analysis), rather than a quick conversational reply?

**Raw output** (label, `noul` yes-probability, latency, line):

```
easy 0.31   3338ms  hi ceti!
easy 0.27    430ms  lol that's funny
easy 0.32    336ms  good morning, how are you?
easy 0.36    489ms  i'm going to bed now, night
easy 0.32    459ms  what's your favorite color?
easy 0.35     46ms  thanks, that helps
easy 0.41     42ms  remind me to drink water in 20 minutes
hard 0.56     41ms  what is 17*23 minus 48?
hard 0.62    458ms  why does my python loop skip every other item when I remove from the list?
hard 0.43    279ms  plan a 3-day study schedule for my exam covering 5 chapters
hard 0.53    273ms  compare renting vs buying a car for 2 years, pros and cons
hard 0.56    371ms  if A is taller than B and B is taller than C, who is shortest?
hard 0.63    309ms  how many weekdays are there between nov 3 and dec 1?
```

The first call (3338 ms) was cold.

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
- **Thinking switch:** `reasoning_effort` `"low"` for on and `"none"` for off (see [thinking-switch-2026-11-15](../thinking-switch-2026-11-15/README.md)). A reply thought if `reasoning_tokens` was above 0 or `reasoning_content` was non-empty.
- **Client:** Python 3.14 through `uv run` in the CetiMind venv, with `httpx2`. Times are client wall clock around one HTTP request.
- **Load:** one request at a time from one client. No CetiMind app was sending turns.
- **Test lines:** all hand-written. The Japanese lines are Claude's translations, not checked by a native speaker.

## Files

- [`kevprobe.py`](kevprobe.py): Experiment 2 script (kevprobe.py)

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

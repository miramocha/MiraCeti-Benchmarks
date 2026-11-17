# Experiment 11: prompt caching by layout and tool set

Experiment 11 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Question:** how much of the prompt does LM Studio read again on each turn? Does CetiMind's prompt layout, or CetiMind #50's plan to vary the tool set per turn, break the cache?

Setup: same machine, LM Studio with `qwen/qwen3.5-9b` and the same loaded config (`parallel` 4), Kev loaded but not called.

## Cache check

The same 6,145-token system prompt was sent three times, streaming with `max_tokens` 8 and thinking off. LM Studio's `usage` has no cached-token count, so time to first token is the only signal.

| Request | Time to first token |
| --- | --- |
| Cold | 2,097 ms |
| Same prompt again | 64 ms |
| Only the last user message changed | 143 ms |

LM Studio reuses the matching start of the prompt. Cold reading ran at about 3,000 tokens/s.

## Method

- **Turns:** 8 consecutive turns of one conversation per variant, 2 rounds, with the variant order shuffled each round. Each conversation opens with a unique tag, so no earlier run's cache matches past the system prompt.
- **Context, built with CetiMind's `build_prompt`:**
  - 5 pinned facts, a profile of about 60 words and a summary of about 60 words
  - 6 memories drawn at random from a pool of 24 on every turn
  - a clock that moves 2 minutes per turn
  - 10 earlier messages, plus one exchange added per turn
- **Prompt size:** 1,750–2,225 tokens with all tools, and 810–1,281 tokens with none.
- **Requests:** streaming, `max_tokens` 1, `temperature` 0, `reasoning_effort: "none"`. Time to first token is mostly prompt reading.
- **Tools:** `user_tools()` plus the four experiment 8 stubs, 8 in total.

**Variants:**

- **A (today):** `build_prompt` as it is. The clock line and memories are in the system message, right after the persona. All 8 tools every turn.
- **B (stable start):** the system message holds only the persona, pinned facts, profile and summary. The clock and memories go in front of the newest user line. All 8 tools every turn.
- **C:** B, with the tool set changing per turn as CetiMind #50 planned: none, all, the 3 schedule tools, none, `web_search`, all, `list_add`, none.
- **D:** B, with no tools.
- **E:** B with all tools, plus a different thinking-off intent-check request (about 300 tokens) before each turn.

## Results

Turn 1 is left out of the summary, because it is cold for every variant.

| Variant | Median time to first token, turns 2–8 | Mean | Trend |
| --- | --- | --- | --- |
| A, today | 345 ms | 336 ms | Rises with history: 267 → 489 ms in round 0 |
| **B, stable start** | **181 ms** | 182 ms | Flat |
| C, tool set changes | 340 ms | 357 ms | Up to 543–555 ms on turns where the tools changed |
| D, no tools | 186 ms | 189 ms | Flat |
| E, B plus intent call | 211 ms | 212 ms | Flat. The intent call itself took 166–382 ms |

## Reading

- **Today's layout loses the cache after the persona** each turn, because the clock and memories change. Moving them next to the user line saves about 150 ms per turn at this size, and the gap grows as the prompt gets longer.
- **Changing the tool set per turn breaks the cache** back to today's cost. Qwen's template places the tool definitions near the start of the prompt.
- **Eight tool definitions add about 940 tokens,** which cost almost nothing once cached (B 181 ms against D 186 ms).
- **An extra request between turns doesn't evict the chat's cache** (E against B, about +30 ms). LM Studio has 4 parallel slots.
- **Prompt reading is not the main cost at this size.** Turns spend 0.2–0.35 s reading the prompt, against 1.5–4 s of thinking on tool turns (experiments 6, 8 and 9).

## Limits

- **Small and synthetic:** 2 rounds, English only, and invented context. The history never reached `PROMPT_TOKEN_BUDGET` (3,000 estimated tokens), so the shifting start caused by dropping old history pairs was not tested.
- **Japanese untested:** Japanese prompts can be 3–4× longer than the estimate (CetiMind #52), so caching would matter more there.
- **No real generation:** only `max_tokens` 1 with no thinking, so total turn time was not measured.
- **Layout B is a probe change:** it was built only in the probe script, not in `core/prompt.py`.

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

- [`cachecheck.py`](cachecheck.py): Cache check script (cachecheck.py)
- [`raw-output.txt`](raw-output.txt): Experiment 11 raw output
- [`cacheprobe.py`](cacheprobe.py): Experiment 11 script (cacheprobe.py, run with argument 2)
- [`cacheprobe.jsonl`](cacheprobe.jsonl): Experiment 11 log (cacheprobe.jsonl)

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

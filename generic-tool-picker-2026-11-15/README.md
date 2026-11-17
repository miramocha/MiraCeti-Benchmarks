# Experiment 8: stub tools next to the schedule tools

Experiment 8 of 12 in a one-day series on Qwen3.5-9B thinking and tool calls in CetiMind, run on 2026-11-15 and first written up in CetiMind #51 (private repo). All test lines are hand-written, so no real chat or memory is in this directory.

**Question:** does the CetiMind #50 design hold beyond the schedule tools? Two parts:

- **A:** can one generic intent check pick the right tools by name from a longer list?
- **B:** does thinking off also stop calls to other tools?

Setup: same machine, LM Studio with `qwen/qwen3.5-9b` and the same loaded config, the character persona, `temperature` 0.7 and `max_tokens` 4096 for chat calls. Kev was loaded but not called.

## Stub tools

Four tools were defined only in the probe script, never in CetiMind, and never run. Only the first reply's `tool_calls` was read. They were offered after the real `user_tools()` (`current_time`, `schedule_create`, `schedule_list`, `schedule_cancel`), for 8 tools in total.

| Tool | Description sent to the model | Parameters |
| --- | --- | --- |
| `web_search` | Search the web for current or outside information. Returns titles, links, and snippets. | `query` |
| `http_get` | Fetch one web page by URL and return its text. | `url` |
| `list_add` | Add an item to one of the user's lists, such as shopping or todo. | `list`, `item` |
| `list_show` | Show the items on one of the user's lists. | `list` |

## A: generic intent check

**Method:**

- **The call:** one `chat/completions` call to the 9B, with `reasoning_effort: "none"`, `temperature` 0 and `max_tokens` 200.
- **Schema:** strict, `{"tools": [<enum of the 8 tool names>]}`.
- **Prompt:** an instruction (below), then a line per tool (`- name: description`), then the conversation as `Assistant: …` / `User: …`:
  > Which tools does the user's last message need? Choose an empty list when a normal reply is enough. A tool is needed only when the user asks for something the tool does, not when they just mention the topic. The current time is already known.
- **Variants:**
  - **json_desc:** descriptions only.
  - **json_ex:** each tool's line also lists one or two example requests. None of them is a test line.
- **Labeled set:** 50 English lines written by hand, each run once.
  - **30 tool turns:**
    - 8 schedule
    - 8 `web_search`
    - 5 `http_get`
    - 4 `list_add`
    - 3 `list_show`
    - 2 that need two tools ("add dentist to my todo and remind me about it tomorrow at 9" and "check when the store closes today and remind me an hour before")
  - **20 normal lines,** including hard cases that mention a tool's topic without asking for it: "i already searched for it, no luck", "i googled you lol", "my shopping list is so long this week", "that website was so slow yesterday", "i added you to my list of favorite people", "i'll check the news later", and "thanks!" after "Done, I added milk to your shopping list."
- **Scoring:**
  - **Miss:** a tool turn that got no tool.
  - **Wrong tool:** a tool turn that got tools, but not every needed one.
  - **Extra tools:** every needed tool, plus others.
  - **False alarm:** a normal line that got any tool.
  - `current_time` is never required, and choosing it is never counted, because the prompt has a clock line.

**Results:**

| Variant | Misses | Wrong tool | Extra tools | False alarms | Median latency |
| --- | --- | --- | --- | --- | --- |
| json_desc | 1/30 | 0 | 0 | 1/20 | 388 ms |
| json_ex | 1/30 | 0 | 0 | 1/20 | 430 ms |

**Errors:**

- **Miss (both variants):** "find me a good recipe for chicken curry", labeled `web_search`, got no tool. The model can answer it from what it knows, so the label is debatable.
- **False alarm (json_desc):** "my shopping list is so long this week" got `list_show`.
- **False alarm (json_ex):** "every day at 8am I go for a run" got `schedule_create`.
- **Two-tool lines:** both got exactly the two needed tools in both variants.

**Latency:** this check took a median of about 0.4 s, against 1.75 s for the yes/no check in experiment 7, even though its prompt is longer. Experiment 7 interleaved Kev and embedding calls on the same GPU between checks, and this run didn't. That is the likely reason, but it was not tested.

## B: thinking off with the stub tools

**Method:** CetiMind's `build_prompt` (persona system prompt and clock line, no memories or history), with all 8 tools sent as OpenAI function tools. Six lines, 2 runs each:

| Line | Expected tool |
| --- | --- |
| "what's the latest news about the nintendo switch 2?" | `web_search` |
| "search for the best ramen places in osaka" | `web_search` |
| "what does https://example.com say?" | `http_get` |
| "summarize this page for me https://example.org/blog/post-12" | `http_get` |
| "add milk to my shopping list" | `list_add` |
| "show me my todo list" | `list_show` |

`reasoning_effort` was `"none"` or `"low"`. Success means the first reply called the expected tool.

**Results:**

| Thinking | Right tool called | Avg time | Reasoning tokens |
| --- | --- | --- | --- |
| off (`none`) | 2/12 (`list_show` both times; everything else missed) | 815 ms | 0 |
| on (`low`) | **12/12** | 1735 ms | 33–131 |

**Reading:**

- **Thinking off fails on other tools as well,** with two kinds of miss:
  - **Read tools:** a refusal or a guess, such as "I don't have access to the internet right now, so I can't fetch that l…", "I don't know enough about Osaka's ramen scene yet. Should I look it up…", or "I'll check what that page says for you, senpai. Let me fetch it and…" with no call.
  - **The write tool:** the same false claim seen with `schedule_create`, such as "Got it, Senpai. Milk is on your list now."
- **Thinking costs less for simple tools.** With these single-argument tools, thinking added about 1 s and 33–131 reasoning tokens. For `schedule_create` in experiment 6 it added about 4 s and a median of 147 tokens.
- **Arguments with thinking on were all correct:** for example `{"query":"best ramen places in osaka"}`, `{"url":"https://example.org/blog/post-12"}` and `{"list":"shopping","item":"milk"}`.

## What this changes in CetiMind #50

- **Make the intent check generic.** Send tool names and descriptions and get back the chosen tools. Only those tools are then sent on the tool turn.
- **Examples per tool are not needed.** Descriptions alone did as well.
- **The safety net only covers write tools.** It catches "claims it did it". A read-tool miss looks like "I can't access the internet" or a guess, which needs a different question. That has not been tested.

## Limits

- **Small, single runs:** one run per line in A and two in B, with 50 hand-written English lines. Japanese was not tested here.
- **Stubs never run:** their results never came back to the model, and their descriptions are invented. Real `web_search` and `http_get` specs (CetiMind #47) may differ.
- **Debatable labels:** for example the recipe line, and whether `current_time` is ever needed.

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

- [`raw-output.txt`](raw-output.txt): Experiment 8 raw output
- [`multitool.py`](multitool.py): Experiment 8 script (multitool.py, run with no argument)
- [`multitool-A.jsonl`](multitool-A.jsonl): A log (multitool-A.jsonl)
- [`multitool-B.jsonl`](multitool-B.jsonl): B log (multitool-B.jsonl)

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

# Endpoint capabilities probe

## Question

OpenAI-compatible servers differ in three ways that matter to CetiMind, and `/v1/models` does not report any of them:

- Which request field turns thinking on and off: `reasoning_effort`, `chat_template_kwargs.enable_thinking` (vLLM, llama.cpp), or `think` (Ollama).
- Whether the model returns tool calls.
- Whether a named `tool_choice` is rejected, ignored, or enforced.

Can a short probe find all three, on the real LM Studio setup, quickly enough to run on Save and on Test connection?

This run checked the probe for CetiMind issue #55 (PR #62). The broader thinking and tool-call measurements are in issue #51 and are not repeated here.

## Setup

- **Server:** LM Studio on the local network, OpenAI-compatible `/v1`. The load settings (context length, GPU offload, parallel slots) were not recorded.
- **Model:** `qwen/qwen3.5-9b`
- **Code:** CetiMind branch `claude/issue-55-capabilities-073b10`, commit `562ff70`, with `src/cetimind/llm/capabilities.py`.
- **Date:** 2026-11-15

## Method

Every request is one user message with `temperature` 0 and `max_tokens` 64. The probe question is `What is 17*23?`. Tool requests offer one tool that takes no arguments:

```json
{"type": "function", "function": {"name": "probe_ping",
  "description": "Answer a connectivity check. Takes no arguments.",
  "parameters": {"type": "object", "properties": {}, "required": []}}}
```

### Step 1: raw requests

Before the probe code was written, five single requests showed what the server sends back:

| Request | HTTP | What came back |
| --- | --- | --- |
| `reasoning_effort: "none"` | 200 | The answer in `content`. `reasoning_content` is present but `""`. |
| `reasoning_effort: "low"` | 200 | `content` is `""`. `reasoning_content` is non-empty. `finish_reason` is `length`, because thinking used all 64 tokens. |
| `chat_template_kwargs: {enable_thinking: false}` | 200 | The same as `none`: the answer, and `reasoning_content` is `""`. |
| `reasoning_effort: "none"`, the tool, and `Call the probe_ping tool now.` | 200 | One `probe_ping` call with arguments `{}`. `finish_reason` is `tool_calls`. |
| The tool and `tool_choice: {"type": "function", "function": {"name": "probe_ping"}}` | 400 | `Invalid tool_choice type: 'object'. Supported string values: none, auto, required` |

Two findings shaped the probe:

- **An empty field doesn't count.** LM Studio always sends `reasoning_content`, and when thinking is off it is `""`. The check needs a non-empty value, not just the key.
- **A 200 alone proves nothing.** `chat_template_kwargs` returned 200 and visibly did nothing. LM Studio ignores fields it doesn't know.

### Step 2: the probe

For each switch in order (`reasoning_effort` `low`/`none`, `chat_template_kwargs.enable_thinking` `true`/`false`, `think` `true`/`false`), the probe sends the question with thinking on, then with thinking off. It keeps the first switch where reasoning shows when on and not when off. Reasoning counts as shown when any one of these holds:

- `usage.completion_tokens_details.reasoning_tokens` is above 0.
- `reasoning_content` or `reasoning` is a non-empty string.
- `content` contains `<think>`.

If no switch passes, it records `none`.

Tools: it sends `Call the probe_ping tool now.` with the tool and thinking off. HTTP 400 means no tools. If no call comes back and a switch exists, it retries once with thinking on.

Named `tool_choice`: it sends the probe question with the tool forced by name. HTTP 400 means `unsupported`, a text reply means `not_enforced`, and a `probe_ping` call means `enforced`.

The run used CetiMind's `test_connection` with the Endpoint page fields for this server, which runs a chat check, an embedding check, then the probe.

## Results

| Capability | Recorded |
| --- | --- |
| Thinking switch | `reasoning_effort` |
| Tools | yes |
| Named `tool_choice` | `unsupported` (HTTP 400) |
| Chat and embedding checks | both answered |
| Wall time, whole Test connection | 3.5 s |

This matches the expected LM Studio behaviour in issue #51: only `reasoning_effort` switches thinking, and a named `tool_choice` is rejected.

Test connection made 5 chat requests: the chat check, then 4 probe requests. `reasoning_effort` passed on its first on/off pair (2 requests), so the other switches were not tried. The tool request got a call on the first try (1), and the named `tool_choice` request got HTTP 400 (1). Each request is capped at 64 tokens, so a probe can't stall on long thinking.

## What it means

- A probe of about 5 short requests is fast enough to run on every Save of a new model and on every Test connection.
- Judging thinking by visible reasoning is needed. Status codes and the presence of a key both give false positives on LM Studio.
- With thinking off, Qwen3.5-9B called the tool when asked directly. Issue #51 found it rarely calls tools with thinking off in real turns. So "tools: yes" means the endpoint and model can return tool calls. It does not mean they will in a turn without thinking.
- The probe was also checked with fake servers for vLLM, Ollama, and a no-tools server (CetiMind `tests/test_capabilities.py`). Only LM Studio was run live.

## See also

- [thinking-switch-2026-11-15](../thinking-switch-2026-11-15/README.md): the earlier experiment that found `reasoning_effort` is the only field that switches Qwen3.5 thinking in LM Studio. This probe checks for that switch.

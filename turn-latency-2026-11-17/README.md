# Turn latency from the CetiMind log

A one-off look at where CetiMind's reply time goes, taken from the timing lines in the app's own log. Only the counts and times are published.

## Setup

- The most recent turns in `cetimind.log` on 2026-11-17, about two days of use.
- Chat model `qwen3.5-4b`, tool model `nvidia/nemotron-3-nano-4b`, intent router on. `chat_thinking` and `tool_thinking` were `auto`: a turn thinks when the router picks a tool.
- The models ran in LM Studio. During part of this time a 9B judge model was loaded beside them, so some turns may have run with layers on the CPU. The log does not record load settings.

## Results

| Step | Turns | Median | Slowest |
| --- | --- | --- | --- |
| Reply with thinking | 30 | 11.6 s | 128.5 s |
| Reply without thinking | 8 | 1.1 s | 2.3 s |
| Intent check (router) | 34 | 0.6 s | |

- 20 of the 34 routed turns logged `no tool call on a routed turn, retrying`. The router picked a tool, the tool model answered without calling it, and the turn ran again with thinking on.
- The miss check (net) fired on 2 turns. Its retry took a median of 13.6 s.

## Reading

Thinking turns cost about ten times a plain turn, and most turns thought because the router picked a tool. The retry rate is the larger problem: either the router picks tools too eagerly, or the tool model ignores tools it was offered. Each retry adds a full thinking turn.

Settings to try, cheapest first: `tool_thinking` off, every model fully on the GPU with nothing else loaded, and speculative decoding with a small draft model. A fix for the retry rate is code work in CetiMind.

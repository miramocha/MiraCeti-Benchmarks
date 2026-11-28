## Accuracy

| Metric | L | LWIDE |
| --- | --- | --- |
| Errors | 0 | 0 |
| Right tools, in the turn | 157/174 (90%, 85–94) | 163/174 (94%, 89–96) |
| Right tools, after the miss check | 157/174 (90%, 85–94) | 161/174 (93%, 88–96) |
| Needed tool called (tool lines) | 105/108 (97%, 92–99) | 107/108 (99%, 95–100) |
| Stray tool call | 8/174 (5%, 2–9) | 4/174 (2%, 1–6) |
| False claim (tool line, no tool, claims done) | 0/108 (0%, 0–3) | 0/108 (0%, 0–3) |
| Grounded in the tool result | 104/123 (85%, 77–90) | 102/126 (81%, 73–87) |
| No-tool line got a late tool + follow-up | 0/42 (0%, 0–8) | 2/42 (5%, 1–16) |
| Injection followed | 1/12 (8%, 1–35) | 1/12 (8%, 1–35) |
| Stale fact (says 4.4) | 1/18 (6%, 1–26) | 0/18 (0%, 0–18) |
| Partial claim (claims the second tool) | 3/12 (25%, 9–53) | 7/12 (58%, 32–81) |
| Memories retrieved per turn (mean) | 3.6 | 3.6 |
| Reply repeats the hold | 1/129 (1%, 0–4) | 0/132 (0%, 0–3) |
| Hold spoken (tool lines) | 105/108 (97%, 92–99) | 108/108 (100%, 97–100) |
| Question on a tool turn | 3/108 (3%, 1–8) | 1/108 (1%, 0–5) |
| Emoji | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) |
| Sound tag | 3/174 (2%, 1–5) | 2/174 (1%, 0–4) |
| Tool name or JSON in the reply | 0/174 (0%, 0–2) | 1/174 (1%, 0–3) |
| **EN** | | |
| Errors | 0 | 0 |
| Right tools, in the turn | 80/87 (92%, 84–96) | 82/87 (94%, 87–98) |
| Right tools, after the miss check | 80/87 (92%, 84–96) | 82/87 (94%, 87–98) |
| Needed tool called (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) |
| Stray tool call | 4/87 (5%, 2–11) | 2/87 (2%, 1–8) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Grounded in the tool result | 56/63 (89%, 79–95) | 56/63 (89%, 79–95) |
| No-tool line got a late tool + follow-up | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) |
| Injection followed | 0/6 (0%, 0–39) | 0/6 (0%, 0–39) |
| Stale fact (says 4.4) | 1/9 (11%, 2–44) | 0/9 (0%, 0–30) |
| Partial claim (claims the second tool) | 2/6 (33%, 10–70) | 4/6 (67%, 30–90) |
| Memories retrieved per turn (mean) | 3.2 | 3.2 |
| Reply repeats the hold | 1/66 (2%, 0–8) | 0/66 (0%, 0–6) |
| Hold spoken (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) |
| Question on a tool turn | 1/54 (2%, 0–10) | 0/54 (0%, 0–7) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Sound tag | 3/87 (3%, 1–10) | 1/87 (1%, 0–6) |
| Tool name or JSON in the reply | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| **JA** | | |
| Errors | 0 | 0 |
| Right tools, in the turn | 77/87 (89%, 80–94) | 81/87 (93%, 86–97) |
| Right tools, after the miss check | 77/87 (89%, 80–94) | 79/87 (91%, 83–95) |
| Needed tool called (tool lines) | 51/54 (94%, 85–98) | 53/54 (98%, 90–100) |
| Stray tool call | 4/87 (5%, 2–11) | 2/87 (2%, 1–8) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Grounded in the tool result | 48/60 (80%, 68–88) | 46/63 (73%, 61–82) |
| No-tool line got a late tool + follow-up | 0/21 (0%, 0–15) | 2/21 (10%, 3–29) |
| Injection followed | 1/6 (17%, 3–56) | 1/6 (17%, 3–56) |
| Stale fact (says 4.4) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) |
| Partial claim (claims the second tool) | 1/6 (17%, 3–56) | 3/6 (50%, 19–81) |
| Memories retrieved per turn (mean) | 4.0 | 4.0 |
| Reply repeats the hold | 0/63 (0%, 0–6) | 0/66 (0%, 0–6) |
| Hold spoken (tool lines) | 51/54 (94%, 85–98) | 54/54 (100%, 93–100) |
| Question on a tool turn | 2/54 (4%, 1–13) | 1/54 (2%, 0–10) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Sound tag | 0/87 (0%, 0–4) | 1/87 (1%, 0–6) |
| Tool name or JSON in the reply | 0/87 (0%, 0–4) | 1/87 (1%, 0–6) |

Paired, L vs LWIDE (exact McNemar; L-only = L right, LWIDE wrong):
- ok, by turn: L-only 3, LWIDE-only 9, p = 0.146
- ok, by line (majority of repeats): L-only 0, LWIDE-only 3, p = 0.250
- ok_final, by turn: L-only 5, LWIDE-only 9, p = 0.424
- ok_final, by line (majority of repeats): L-only 0, LWIDE-only 3, p = 0.250
- false_claim, by turn: L-only 0, LWIDE-only 0, p = 1.000
- false_claim, by line (majority of repeats): L-only 0, LWIDE-only 0, p = 1.000

## Time per turn (ms, median / p90)

| Measure | Lines | L | LWIDE |
| --- | --- | --- | --- |
| first_line_ms | all | 998 / 1411 | 1048 / 1765 |
| first_line_ms | tool | 983 / 1243 | 1020 / 1261 |
| first_line_ms | no tool | 1183 / 2056 | 1505 / 2183 |
| reply_ms | all | 4570 / 7972 | 4644 / 6558 |
| reply_ms | tool | 4942 / 7613 | 4993 / 6493 |
| reply_ms | no tool | 1183 / 2056 | 1505 / 2183 |
| done_ms | all | 5349 / 7972 | 5287 / 7206 |
| done_ms | tool | 5027 / 7613 | 4993 / 6493 |
| done_ms | no tool | 5684 / 6989 | 5957 / 7209 |
| calls (mean) | all | 5.0 | 4.9 |
| prompt_tokens (mean) | all | 3937.7 | 4243.7 |
| completion_tokens (mean) | all | 418.4 | 388.7 |
| reasoning_tokens (mean) | all | 264.9 | 234.8 |

## Prompt size (prompt tokens of the first call that carries the persona prompt, median)

- L: 1602
- LWIDE: 1594

## Time per step (ms)

| Arm | Phase | Step | Calls | Median | p90 | Mean prompt tok | Mean reasoning tok |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L | net | miss | 45 | 2194 | 2437 | 224 | 134 |
| L | net | task_round | 39 | 2501 | 3359 | 900 | 128 |
| L | turn | embed | 174 | 20 | 27 | 0 | 0 |
| L | turn | hold | 129 | 596 | 762 | 315 | 0 |
| L | turn | intent | 174 | 368 | 496 | 277 | 0 |
| L | turn | miss | 9 | 2254 | 2692 | 217 | 135 |
| L | turn | persona | 54 | 849 | 3892 | 1632 | 43 |
| L | turn | say_this | 120 | 710 | 892 | 1577 | 0 |
| L | turn | task_retry | 9 | 2378 | 2988 | 899 | 132 |
| L | turn | task_round | 284 | 2017 | 2688 | 929 | 107 |
| LWIDE | net | miss | 42 | 2211 | 2581 | 300 | 134 |
| LWIDE | net | say_this | 2 | 777 | 788 | 1526 | 0 |
| LWIDE | net | task_round | 34 | 2430 | 3227 | 1104 | 122 |
| LWIDE | turn | embed | 174 | 21 | 29 | 0 | 0 |
| LWIDE | turn | hold | 132 | 631 | 783 | 315 | 0 |
| LWIDE | turn | intent | 174 | 405 | 1010 | 312 | 0 |
| LWIDE | turn | miss | 4 | 2194 | 2567 | 286 | 134 |
| LWIDE | turn | persona | 46 | 758 | 1345 | 1631 | 23 |
| LWIDE | turn | say_this | 129 | 717 | 886 | 1576 | 0 |
| LWIDE | turn | task_retry | 4 | 2562 | 3490 | 1099 | 135 |
| LWIDE | turn | task_round | 281 | 2014 | 2732 | 1087 | 103 |

## Time per turn share by step (mean ms per turn)

- L: turn:task_round 3205, net:miss 575, net:task_round 551, turn:say_this 490, turn:hold 454, turn:intent 431, turn:persona 398, turn:miss 122, turn:task_retry 120, turn:embed 22
- LWIDE: turn:task_round 3156, net:miss 549, turn:say_this 538, turn:intent 501, turn:hold 481, net:task_round 479, turn:persona 270, turn:task_retry 60, turn:miss 52, turn:embed 22, net:say_this 9

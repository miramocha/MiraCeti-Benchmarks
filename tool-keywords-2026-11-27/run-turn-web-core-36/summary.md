## Accuracy

| Metric | L | LWIDE |
| --- | --- | --- |
| Errors | 0 | 0 |
| Right tools, in the turn | 162/174 (93%, 88–96) | 152/174 (87%, 82–92) |
| Right tools, after the miss check | 161/174 (93%, 88–96) | 154/174 (89%, 83–92) |
| Needed tool called (tool lines) | 106/108 (98%, 93–99) | 102/108 (94%, 88–97) |
| Stray tool call | 9/174 (5%, 3–10) | 16/174 (9%, 6–14) |
| False claim (tool line, no tool, claims done) | 0/108 (0%, 0–3) | 0/108 (0%, 0–3) |
| Grounded in the tool result | 103/126 (82%, 74–88) | 101/123 (82%, 74–88) |
| No-tool line got a late tool + follow-up | 1/42 (2%, 0–12) | 0/42 (0%, 0–8) |
| Injection followed | 1/12 (8%, 1–35) | 1/12 (8%, 1–35) |
| Stale fact (says 4.4) | 0/18 (0%, 0–18) | 1/18 (6%, 1–26) |
| Partial claim (claims the second tool) | 2/12 (17%, 5–45) | 3/12 (25%, 9–53) |
| Memories retrieved per turn (mean) | 3.6 | 3.6 |
| Reply repeats the hold | 0/135 (0%, 0–3) | 0/135 (0%, 0–3) |
| Hold spoken (tool lines) | 108/108 (100%, 97–100) | 105/108 (97%, 92–99) |
| Question on a tool turn | 5/108 (5%, 2–10) | 0/108 (0%, 0–3) |
| Emoji | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) |
| Sound tag | 0/174 (0%, 0–2) | 2/174 (1%, 0–4) |
| Tool name or JSON in the reply | 1/174 (1%, 0–3) | 0/174 (0%, 0–2) |
| **EN** | | |
| Errors | 0 | 0 |
| Right tools, in the turn | 84/87 (97%, 90–99) | 80/87 (92%, 84–96) |
| Right tools, after the miss check | 84/87 (97%, 90–99) | 80/87 (92%, 84–96) |
| Needed tool called (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) |
| Stray tool call | 2/87 (2%, 1–8) | 4/87 (5%, 2–11) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Grounded in the tool result | 58/63 (92%, 83–97) | 55/63 (87%, 77–93) |
| No-tool line got a late tool + follow-up | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) |
| Injection followed | 0/6 (0%, 0–39) | 0/6 (0%, 0–39) |
| Stale fact (says 4.4) | 0/9 (0%, 0–30) | 1/9 (11%, 2–44) |
| Partial claim (claims the second tool) | 0/6 (0%, 0–39) | 2/6 (33%, 10–70) |
| Memories retrieved per turn (mean) | 3.2 | 3.2 |
| Reply repeats the hold | 0/66 (0%, 0–6) | 0/69 (0%, 0–5) |
| Hold spoken (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) |
| Question on a tool turn | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Sound tag | 0/87 (0%, 0–4) | 1/87 (1%, 0–6) |
| Tool name or JSON in the reply | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| **JA** | | |
| Errors | 0 | 0 |
| Right tools, in the turn | 78/87 (90%, 81–94) | 72/87 (83%, 73–89) |
| Right tools, after the miss check | 77/87 (89%, 80–94) | 74/87 (85%, 76–91) |
| Needed tool called (tool lines) | 52/54 (96%, 87–99) | 48/54 (89%, 78–95) |
| Stray tool call | 7/87 (8%, 4–16) | 12/87 (14%, 8–23) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Grounded in the tool result | 45/63 (71%, 59–81) | 46/60 (77%, 65–86) |
| No-tool line got a late tool + follow-up | 1/21 (5%, 1–23) | 0/21 (0%, 0–15) |
| Injection followed | 1/6 (17%, 3–56) | 1/6 (17%, 3–56) |
| Stale fact (says 4.4) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) |
| Partial claim (claims the second tool) | 2/6 (33%, 10–70) | 1/6 (17%, 3–56) |
| Memories retrieved per turn (mean) | 4.0 | 4.0 |
| Reply repeats the hold | 0/69 (0%, 0–5) | 0/66 (0%, 0–6) |
| Hold spoken (tool lines) | 54/54 (100%, 93–100) | 51/54 (94%, 85–98) |
| Question on a tool turn | 5/54 (9%, 4–20) | 0/54 (0%, 0–7) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Sound tag | 0/87 (0%, 0–4) | 1/87 (1%, 0–6) |
| Tool name or JSON in the reply | 1/87 (1%, 0–6) | 0/87 (0%, 0–4) |

Paired, L vs LWIDE (exact McNemar; L-only = L right, LWIDE wrong):
- ok, by turn: L-only 14, LWIDE-only 4, p = 0.031
- ok, by line (majority of repeats): L-only 4, LWIDE-only 0, p = 0.125
- ok_final, by turn: L-only 12, LWIDE-only 5, p = 0.143
- ok_final, by line (majority of repeats): L-only 3, LWIDE-only 0, p = 0.250
- false_claim, by turn: L-only 0, LWIDE-only 0, p = 1.000
- false_claim, by line (majority of repeats): L-only 0, LWIDE-only 0, p = 1.000

## Time per turn (ms, median / p90)

| Measure | Lines | L | LWIDE |
| --- | --- | --- | --- |
| first_line_ms | all | 880 / 1338 | 874 / 1201 |
| first_line_ms | tool | 859 / 1066 | 860 / 1046 |
| first_line_ms | no tool | 1227 / 1733 | 995 / 1395 |
| reply_ms | all | 4262 / 6896 | 4162 / 6055 |
| reply_ms | tool | 4368 / 6721 | 4390 / 6055 |
| reply_ms | no tool | 1293 / 1899 | 1162 / 4518 |
| done_ms | all | 4748 / 7149 | 4624 / 6293 |
| done_ms | tool | 4368 / 6721 | 4422 / 6055 |
| done_ms | no tool | 5222 / 6455 | 5110 / 6078 |
| calls (mean) | all | 5.1 | 5.0 |
| prompt_tokens (mean) | all | 4317.1 | 8080.1 |
| completion_tokens (mean) | all | 432.7 | 396.1 |
| reasoning_tokens (mean) | all | 265.9 | 239.7 |

## Prompt size (prompt tokens of the first call that carries the persona prompt, median)

- L: 1592
- LWIDE: 1588

## Time per step (ms)

| Arm | Phase | Step | Calls | Median | p90 | Mean prompt tok | Mean reasoning tok |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L | net | miss | 39 | 1907 | 2069 | 265 | 134 |
| L | net | say_this | 1 | 504 | 504 | 1509 | 0 |
| L | net | task_round | 37 | 2071 | 2773 | 1025 | 128 |
| L | turn | embed | 174 | 19 | 27 | 0 | 0 |
| L | turn | hold | 135 | 473 | 607 | 315 | 0 |
| L | turn | intent | 174 | 374 | 614 | 315 | 0 |
| L | turn | miss | 6 | 1847 | 1952 | 263 | 134 |
| L | turn | persona | 45 | 741 | 3104 | 1630 | 35 |
| L | turn | say_this | 132 | 626 | 825 | 1580 | 0 |
| L | turn | task_retry | 6 | 1771 | 2384 | 1033 | 128 |
| L | turn | task_round | 311 | 1764 | 2290 | 1011 | 107 |
| LWIDE | net | miss | 39 | 1977 | 2140 | 685 | 135 |
| LWIDE | net | say_this | 3 | 428 | 544 | 1527 | 0 |
| LWIDE | net | task_round | 39 | 1977 | 2705 | 2816 | 121 |
| LWIDE | turn | embed | 174 | 19 | 28 | 0 | 0 |
| LWIDE | turn | hold | 135 | 487 | 590 | 315 | 0 |
| LWIDE | turn | intent | 174 | 350 | 490 | 697 | 0 |
| LWIDE | turn | miss | 4 | 2028 | 2327 | 684 | 134 |
| LWIDE | turn | persona | 43 | 634 | 1029 | 1636 | 24 |
| LWIDE | turn | say_this | 132 | 633 | 812 | 1574 | 0 |
| LWIDE | turn | task_retry | 4 | 2056 | 2344 | 2811 | 121 |
| LWIDE | turn | task_round | 291 | 1762 | 2291 | 2780 | 102 |

## Time per turn share by step (mean ms per turn)

- L: turn:task_round 3039, turn:say_this 484, net:task_round 448, net:miss 434, turn:intent 432, turn:hold 377, turn:persona 263, turn:task_retry 64, turn:miss 62, turn:embed 21, net:say_this 3
- LWIDE: turn:task_round 2826, turn:say_this 496, net:miss 446, net:task_round 443, turn:intent 394, turn:hold 388, turn:persona 220, turn:miss 46, turn:task_retry 45, turn:embed 20, net:say_this 8

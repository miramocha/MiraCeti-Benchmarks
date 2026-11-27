# Memories per turn by language: tables

From `summarize.py run`. Arms A and B keep 4 memories, A1 and B1 keep 1.

## Accuracy

| Metric | A | A1 | B | B1 |
| --- | --- | --- | --- | --- |
| Errors | 0 | 0 | 0 | 1 |
| Right tools, in the turn | 162/174 (93%, 88–96) | 163/174 (94%, 89–96) | 152/174 (87%, 82–92) | 149/173 (86%, 80–90) |
| Right tools, after the miss check | 161/174 (93%, 88–96) | 161/174 (93%, 88–96) | 152/174 (87%, 82–92) | 149/173 (86%, 80–90) |
| Needed tool called (tool lines) | 106/108 (98%, 93–99) | 106/108 (98%, 93–99) | 96/108 (89%, 82–94) | 95/107 (89%, 81–93) |
| Stray tool call | 8/174 (5%, 2–9) | 7/174 (4%, 2–8) | 5/174 (3%, 1–7) | 2/174 (1%, 0–4) |
| False claim (tool line, no tool, claims done) | 0/108 (0%, 0–3) | 0/108 (0%, 0–3) | 5/108 (5%, 2–10) | 4/107 (4%, 1–9) |
| Grounded in the tool result | 95/126 (75%, 67–82) | 96/126 (76%, 68–83) | 100/117 (85%, 78–91) | 95/113 (84%, 76–90) |
| No-tool line got a late tool + follow-up | 1/42 (2%, 0–12) | 2/42 (5%, 1–16) | 0/42 (0%, 0–8) | 0/42 (0%, 0–8) |
| Injection followed | 1/12 (8%, 1–35) | 2/12 (17%, 5–45) | 0/12 (0%, 0–24) | 1/11 (9%, 2–38) |
| Stale fact (says 4.4) | 0/18 (0%, 0–18) | 0/18 (0%, 0–18) | 0/18 (0%, 0–18) | 0/17 (0%, 0–18) |
| Partial claim (claims the second tool) | 3/12 (25%, 9–53) | 4/12 (33%, 14–61) | 3/12 (25%, 9–53) | 3/12 (25%, 9–53) |
| Memories retrieved per turn (mean) | 3.6 | 1.0 | 3.6 | 1.0 |
| Reply repeats the hold | 2/132 (2%, 0–5) | 2/132 (2%, 0–5) | - | - |
| Hold spoken (tool lines) | 108/108 (100%, 97–100) | 108/108 (100%, 97–100) | 0/108 (0%, 0–3) | 0/108 (0%, 0–3) |
| Question on a tool turn | 0/108 (0%, 0–3) | 2/108 (2%, 1–7) | 6/108 (6%, 3–12) | 0/107 (0%, 0–3) |
| Emoji | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) | 0/173 (0%, 0–2) |
| Sound tag | 0/174 (0%, 0–2) | 1/174 (1%, 0–3) | 0/174 (0%, 0–2) | 0/173 (0%, 0–2) |
| Tool name or JSON in the reply | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) | 0/174 (0%, 0–2) | 0/173 (0%, 0–2) |
| **EN** | | | | |
| Errors | 0 | 0 | 0 | 0 |
| Right tools, in the turn | 82/87 (94%, 87–98) | 83/87 (95%, 89–98) | 77/87 (89%, 80–94) | 75/87 (86%, 77–92) |
| Right tools, after the miss check | 82/87 (94%, 87–98) | 83/87 (95%, 89–98) | 77/87 (89%, 80–94) | 75/87 (86%, 77–92) |
| Needed tool called (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) | 48/54 (89%, 78–95) | 48/54 (89%, 78–95) |
| Stray tool call | 3/87 (3%, 1–10) | 2/87 (2%, 1–8) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) | 3/54 (6%, 2–15) | 4/54 (7%, 3–18) |
| Grounded in the tool result | 50/63 (79%, 68–88) | 49/63 (78%, 66–86) | 51/58 (88%, 77–94) | 49/57 (86%, 75–93) |
| No-tool line got a late tool + follow-up | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) |
| Injection followed | 1/6 (17%, 3–56) | 0/6 (0%, 0–39) | 0/6 (0%, 0–39) | 1/6 (17%, 3–56) |
| Stale fact (says 4.4) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) |
| Partial claim (claims the second tool) | 2/6 (33%, 10–70) | 3/6 (50%, 19–81) | 1/6 (17%, 3–56) | 3/6 (50%, 19–81) |
| Memories retrieved per turn (mean) | 3.2 | 1.0 | 3.2 | 1.0 |
| Reply repeats the hold | 2/66 (3%, 1–10) | 2/66 (3%, 1–10) | - | - |
| Hold spoken (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Question on a tool turn | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) | 4/54 (7%, 3–18) | 0/54 (0%, 0–7) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Sound tag | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| Tool name or JSON in the reply | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) |
| **JA** | | | | |
| Errors | 0 | 0 | 0 | 1 |
| Right tools, in the turn | 80/87 (92%, 84–96) | 80/87 (92%, 84–96) | 75/87 (86%, 77–92) | 74/86 (86%, 77–92) |
| Right tools, after the miss check | 79/87 (91%, 83–95) | 78/87 (90%, 81–94) | 75/87 (86%, 77–92) | 74/86 (86%, 77–92) |
| Needed tool called (tool lines) | 52/54 (96%, 87–99) | 52/54 (96%, 87–99) | 48/54 (89%, 78–95) | 47/53 (89%, 77–95) |
| Stray tool call | 5/87 (6%, 2–13) | 5/87 (6%, 2–13) | 5/87 (6%, 2–13) | 2/87 (2%, 1–8) |
| False claim (tool line, no tool, claims done) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) | 2/54 (4%, 1–13) | 0/53 (0%, 0–7) |
| Grounded in the tool result | 45/63 (71%, 59–81) | 47/63 (75%, 63–84) | 49/59 (83%, 72–91) | 46/56 (82%, 70–90) |
| No-tool line got a late tool + follow-up | 1/21 (5%, 1–23) | 2/21 (10%, 3–29) | 0/21 (0%, 0–15) | 0/21 (0%, 0–15) |
| Injection followed | 0/6 (0%, 0–39) | 2/6 (33%, 10–70) | 0/6 (0%, 0–39) | 0/5 (0%, 0–43) |
| Stale fact (says 4.4) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) | 0/9 (0%, 0–30) | 0/8 (0%, 0–32) |
| Partial claim (claims the second tool) | 1/6 (17%, 3–56) | 1/6 (17%, 3–56) | 2/6 (33%, 10–70) | 0/6 (0%, 0–39) |
| Memories retrieved per turn (mean) | 4.0 | 1.0 | 4.0 | 1.0 |
| Reply repeats the hold | 0/66 (0%, 0–6) | 0/66 (0%, 0–6) | - | - |
| Hold spoken (tool lines) | 54/54 (100%, 93–100) | 54/54 (100%, 93–100) | 0/54 (0%, 0–7) | 0/54 (0%, 0–7) |
| Question on a tool turn | 0/54 (0%, 0–7) | 2/54 (4%, 1–13) | 2/54 (4%, 1–13) | 0/53 (0%, 0–7) |
| Emoji | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/86 (0%, 0–4) |
| Sound tag | 0/87 (0%, 0–4) | 1/87 (1%, 0–6) | 0/87 (0%, 0–4) | 0/86 (0%, 0–4) |
| Tool name or JSON in the reply | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/87 (0%, 0–4) | 0/86 (0%, 0–4) |

Paired, A vs A1 (exact McNemar; A-only = A right, A1 wrong):
- ok: A-only 3, A1-only 4, p = 1.000
- ok_final: A-only 5, A1-only 5, p = 1.000
- false_claim: A-only 0, A1-only 0, p = 1
Paired, A vs B (exact McNemar; A-only = A right, B wrong):
- ok: A-only 17, B-only 7, p = 0.064
- ok_final: A-only 17, B-only 8, p = 0.108
- false_claim: A-only 0, B-only 5, p = 0.062
Paired, A vs B1 (exact McNemar; A-only = A right, B1 wrong):
- ok: A-only 18, B1-only 6, p = 0.023
- ok_final: A-only 18, B1-only 7, p = 0.043
- false_claim: A-only 0, B1-only 4, p = 0.125

## Time per turn (ms, median / p90)

| Measure | Lines | A | A1 | B | B1 |
| --- | --- | --- | --- | --- | --- |
| first_line_ms | all | 809 / 2324 | 806 / 2320 | 2731 / 4052 | 2498 / 3942 |
| first_line_ms | tool | 760 / 929 | 751 / 938 | 3339 / 4612 | 3164 / 4527 |
| first_line_ms | no tool | 2190 / 2580 | 2245 / 2533 | 1876 / 2247 | 1812 / 2074 |
| reply_ms | all | 4741 / 6603 | 4702 / 6345 | 2731 / 4052 | 2498 / 3942 |
| reply_ms | tool | 4895 / 6620 | 4928 / 6364 | 3339 / 4612 | 3164 / 4527 |
| reply_ms | no tool | 2190 / 2580 | 2245 / 2533 | 1876 / 2247 | 1812 / 2074 |
| done_ms | all | 5145 / 6647 | 5152 / 6509 | 2731 / 4052 | 2498 / 3942 |
| done_ms | tool | 4895 / 6620 | 4928 / 6364 | 3339 / 4612 | 3164 / 4527 |
| done_ms | no tool | 5798 / 6475 | 5844 / 6478 | 1876 / 2247 | 1812 / 2074 |
| calls (mean) | all | 4.9 | 4.9 | 1.8 | 1.7 |
| prompt_tokens (mean) | all | 4248.7 | 4199.1 | 4244.7 | 4015.2 |
| completion_tokens (mean) | all | 527.1 | 539.0 | 270.6 | 263.5 |
| reasoning_tokens (mean) | all | 373.4 | 375.8 | 204.5 | 197.3 |

## Prompt size (prompt tokens of the first call that carries the persona prompt, median)

- A: 1551
- A1: 1480
- B: 2452
- B1: 2360

## Time per step (ms)

| Arm | Phase | Step | Calls | Median | p90 | Mean prompt tok | Mean reasoning tok |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | net | miss | 42 | 1707 | 1752 | 289 | 134 |
| A | net | say_this | 1 | 1727 | 1727 | 1460 | 134 |
| A | net | task_round | 39 | 1948 | 2521 | 1103 | 129 |
| A | turn | embed | 174 | 19 | 31 | 0 | 0 |
| A | turn | hold | 132 | 443 | 560 | 315 | 0 |
| A | turn | intent | 174 | 311 | 755 | 312 | 0 |
| A | turn | miss | 4 | 1690 | 1776 | 292 | 135 |
| A | turn | persona | 46 | 1639 | 1837 | 1583 | 144 |
| A | turn | say_this | 128 | 1688 | 1836 | 1531 | 133 |
| A | turn | task_retry | 4 | 1686 | 2276 | 1098 | 127 |
| A | turn | task_round | 287 | 1492 | 1938 | 1088 | 103 |
| A1 | net | miss | 42 | 1681 | 1717 | 290 | 135 |
| A1 | net | say_this | 2 | 1701 | 1724 | 1381 | 134 |
| A1 | net | task_round | 40 | 1852 | 2372 | 1103 | 130 |
| A1 | turn | embed | 174 | 19 | 30 | 0 | 0 |
| A1 | turn | hold | 132 | 429 | 576 | 315 | 0 |
| A1 | turn | intent | 174 | 308 | 768 | 312 | 0 |
| A1 | turn | miss | 4 | 1741 | 1818 | 294 | 134 |
| A1 | turn | persona | 46 | 1635 | 1885 | 1503 | 144 |
| A1 | turn | say_this | 129 | 1681 | 1847 | 1456 | 133 |
| A1 | turn | task_retry | 4 | 1789 | 1981 | 1099 | 120 |
| A1 | turn | task_round | 288 | 1490 | 1983 | 1087 | 102 |
| B | turn | embed | 174 | 8 | 11 | 0 | 0 |
| B | turn | full_round | 305 | 1654 | 2033 | 2415 | 116 |
| B | turn | persona | 1 | 1838 | 1838 | 1857 | 137 |
| B1 | turn | embed | 174 | 9 | 11 | 0 | 0 |
| B1 | turn | full_round | 300 | 1631 | 1999 | 2341 | 115 |
| B1 | turn | persona | 3 | 1559 | 1850 | 1922 | 125 |

## Time per turn share by step (mean ms per turn)

- A: turn:task_round 2377, turn:say_this 1248, turn:persona 460, net:task_round 439, net:miss 412, turn:intent 371, turn:hold 343, turn:miss 39, turn:task_retry 39, turn:embed 20, net:say_this 10
- A1: turn:task_round 2414, turn:say_this 1305, turn:persona 462, net:task_round 437, net:miss 406, turn:intent 370, turn:hold 335, turn:miss 40, turn:task_retry 39, turn:embed 20, net:say_this 20
- B: turn:full_round 2808, turn:persona 11, turn:embed 9
- B1: turn:full_round 2746, turn:persona 28, turn:embed 9

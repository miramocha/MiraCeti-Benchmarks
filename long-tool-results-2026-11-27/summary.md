Turns: 360, errors: 0

| Measure | L | L2500 | LFULL | LSUM |
| --- | --- | --- | --- | --- |
| Answer named, all | 28/90 | 62/90 | 89/90 | 77/90 |
| Answer early (under 1,000 chars) | 28/30 | 30/30 | 29/30 | 24/30 |
| Answer in the middle | 0/30 | 18/30 | 30/30 | 26/30 |
| Answer late | 0/30 | 14/30 | 30/30 | 27/30 |
| English | 15/45 | 18/45 | 44/45 | 44/45 |
| Japanese | 13/45 | 44/45 | 45/45 | 33/45 |
| Fetched pages | 22/72 | 47/72 | 71/72 | 59/72 |
| Search results | 6/18 | 15/18 | 18/18 | 18/18 |
| Distractor named instead | 23/90 | 13/90 | 0/90 | 0/90 |
| Right tools called | 90/90 | 90/90 | 90/90 | 90/90 |
| Answer time (median) | 3.78 s | 3.93 s | 4.02 s | 4.15 s |
| Say-this call (median) | 0.64 s | 0.75 s | 0.80 s | 0.53 s |
| Summary call (median) | – | – | – | 0.60 s |
| Say-this prompt tokens (median) | 1,864 | 2,402 | 2,871 | 1,539 |

Paired, answer named (exact McNemar; x-only = x right, y wrong):
- L vs LFULL: L-only 1, LFULL-only 62, p = 1.4e-17
- L vs LSUM: L-only 4, LSUM-only 53, p = 5.9e-12
- L vs L2500: L-only 0, L2500-only 34, p = 1.2e-10
- LSUM vs LFULL: LSUM-only 1, LFULL-only 13, p = 0.0018
- L2500 vs LFULL: L2500-only 1, LFULL-only 28, p = 1.1e-07

# Reminder accuracy benchmark (quick-2026-11-17)

Judge: `qwen/qwen3.5-9b`

## `7fcacca` (7fcacca)

| Metric | Value |
|---|---|
| stale_reply | 10% (3/30, CI 3%-26%) |
| stale_pair | 12% (3/24, CI 4%-31%) |
| live_recall | 88% (21/24, CI 69%-96%) |
| specific_correct | 67% (10/15, CI 42%-85%) |
| unprompted | n/a |
| judge_failed | 0% (0/30, CI 0%-11%) |
| request_leak | 50% (6/12, CI 25%-75%) |
| life_keep | 75% (9/12, CI 47%-91%) |
| kind_correct | 100% (9/9, CI 70%-100%) |

Stale replies by scenario:

- ui_cancel: 17% (1/6, CI 3%-56%)
- fired: 0% (0/6, CI 0%-39%)
- active: 0% (0/6, CI 0%-39%)
- mixed: 33% (2/6, CI 10%-70%)
- recreated: 0% (0/6, CI 0%-39%)

## `main` (141ac18)

| Metric | Value |
|---|---|
| stale_reply | 0% (0/29, CI 0%-12%) |
| stale_pair | 0% (0/22, CI 0%-15%) |
| live_recall | 79% (19/24, CI 60%-91%) |
| specific_correct | 86% (12/14, CI 60%-96%) |
| unprompted | n/a |
| judge_failed | 3% (1/30, CI 1%-17%) |
| request_leak | 0% (0/12, CI 0%-24%) |
| life_keep | 75% (9/12, CI 47%-91%) |
| kind_correct | 100% (9/9, CI 70%-100%) |

Stale replies by scenario:

- ui_cancel: 0% (0/6, CI 0%-39%)
- fired: 0% (0/6, CI 0%-39%)
- active: 0% (0/6, CI 0%-39%)
- mixed: 0% (0/5, CI 0%-43%)
- recreated: 0% (0/6, CI 0%-39%)

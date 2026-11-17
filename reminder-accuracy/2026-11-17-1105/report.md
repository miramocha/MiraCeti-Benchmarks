# Reminder accuracy benchmark (2026-11-17-1105)

Judge: `qwen/qwen3.5-9b`, thinking off

## `7fcacca` (7fcacca)

| Metric | Value |
|---|---|
| stale_reply | 7% (2/30, CI 2%-21%) |
| stale_pair | 8% (2/24, CI 2%-26%) |
| live_recall | 88% (21/24, CI 69%-96%) |
| specific_correct | 87% (13/15, CI 62%-96%) |
| unprompted | n/a |
| judge_failed | 0% (0/30, CI 0%-11%) |
| request_leak | 50% (6/12, CI 25%-75%) |
| life_keep | 75% (9/12, CI 47%-91%) |
| kind_correct | 100% (9/9, CI 70%-100%) |

Stale replies by scenario:

- ui_cancel: 17% (1/6, CI 3%-56%)
- fired: 0% (0/6, CI 0%-39%)
- active: 0% (0/6, CI 0%-39%)
- mixed: 17% (1/6, CI 3%-56%)
- recreated: 0% (0/6, CI 0%-39%)

## `main` (141ac18)

| Metric | Value |
|---|---|
| stale_reply | 4% (1/28, CI 1%-18%) |
| stale_pair | 5% (1/20, CI 1%-24%) |
| live_recall | 83% (20/24, CI 64%-93%) |
| specific_correct | 92% (12/13, CI 67%-99%) |
| unprompted | n/a |
| judge_failed | 7% (2/30, CI 2%-21%) |
| request_leak | 0% (0/12, CI 0%-24%) |
| life_keep | 75% (9/12, CI 47%-91%) |
| kind_correct | 100% (9/9, CI 70%-100%) |

Stale replies by scenario:

- ui_cancel: 17% (1/6, CI 3%-56%)
- fired: 0% (0/6, CI 0%-39%)
- active: 0% (0/6, CI 0%-39%)
- mixed: 0% (0/4, CI 0%-49%)
- recreated: 0% (0/6, CI 0%-39%)

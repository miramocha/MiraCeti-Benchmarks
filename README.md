# MiraCeti benchmarks

Published benchmark runs for the MiraCeti apps. One directory per benchmark. Each run of that benchmark is a directory inside it. The code that produces a run stays in the app repo.

## Benchmarks

| Benchmark | What it measures |
| --- | --- |
| [Reminder accuracy](reminder-accuracy/methodology.md) | Whether a CetiMind reply matches the real schedule, and whether a reminder request is stored as memory. |

## One-off experiments

Single checks that are not repeated as a benchmark. One directory each, named with the date.

| Experiment | What it checked |
| --- | --- |
| [Stale reminder fix](stale-reminder-fix-2026-11-16/README.md) | Before and after counts for the CetiMind stale-reminder fixes, run on a copy of real memory. Counts only. |
| [Turn latency](turn-latency-2026-11-17/README.md) | Where CetiMind reply time goes, from the app log: thinking turns, the router, and tool-call retries. |

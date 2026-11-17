"""Draw the README charts as plain SVG, one light and one dark file per chart.

Run from the repo root: python tools/make_charts.py

Each chart's numbers are copied from the results table in that experiment's README. Change them there and
here together. GitHub picks the light or dark file through <picture> with prefers-color-scheme.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Reference palette (validated: tools/README.md has the validator output).
THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "primary": "#0b0b0b",
        "secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834"],
    },
    "dark": {
        "surface": "#1a1a19",
        "primary": "#f0efec",
        "secondary": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "series": ["#3987e5", "#d95926"],
    },
}
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
WIDTH = 680
PAD = 20
CHAR = 6.6  # rough width of one 12px character, for layout only


@dataclass
class Value:
    """One bar. With hits/total the bar is a rate and gets a Wilson interval; with amount it is a plain number."""

    hits: int | None = None
    total: int | None = None
    amount: float | None = None
    label: str = ""
    interval: bool = True

    @property
    def x(self) -> float:
        if self.amount is not None:
            return self.amount
        return 100.0 * self.hits / self.total

    def text(self, unit: str) -> str:
        if self.label:
            return self.label
        if self.amount is not None:
            return f"{self.amount:g}{unit}"
        return f"{self.hits}/{self.total}"

    def wilson(self) -> tuple[float, float] | None:
        if not self.interval or self.hits is None or not self.total:
            return None
        z, n, p = 1.96, self.total, self.hits / self.total
        centre = (p + z * z / (2 * n)) / (1 + z * z / n)
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        return 100 * max(0.0, centre - half), 100 * min(1.0, centre + half)


@dataclass
class Series:
    name: str
    values: list[Value]


@dataclass
class Chart:
    path: str
    title: str
    subtitle: str
    categories: list[str]
    series: list[Series]
    xmax: float = 100.0
    ticks: list[float] = field(default_factory=lambda: [0, 25, 50, 75, 100])
    unit: str = "%"
    note: str = ""


def _bar(x0: float, y: float, width: float, height: float, colour: str) -> str:
    """A bar square at the baseline with a 4px rounded data end."""
    if width <= 0:
        return ""
    r = min(4.0, width, height / 2)
    return (
        f'<path d="M{x0:.1f},{y:.1f} H{x0 + width - r:.1f} Q{x0 + width:.1f},{y:.1f} {x0 + width:.1f},{y + r:.1f} '
        f"V{y + height - r:.1f} Q{x0 + width:.1f},{y + height:.1f} {x0 + width - r:.1f},{y + height:.1f} "
        f'H{x0:.1f} Z" fill="{colour}"/>'
    )


def render(chart: Chart, theme: dict[str, object]) -> str:
    many = len(chart.series) > 1
    thick = 16 if many else 20
    gap = 2
    group = len(chart.series) * thick + (len(chart.series) - 1) * gap
    row = group + 16
    label_w = max(len(name) for name in chart.categories) * CHAR + 16
    x0 = PAD + label_w
    plot_w = WIDTH - x0 - PAD - 70  # room for the value label past the longest bar
    top = PAD + 22 + 18 + (24 if many else 8)
    plot_h = row * len(chart.categories)
    height = top + plot_h + 28 + (18 if chart.note else 0) + PAD

    def sx(value: float) -> float:
        return x0 + plot_w * value / chart.xmax

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-labelledby="t d" font-family=\'{FONT}\'>',
        f"<title id=\"t\">{escape(chart.title)}</title>",
        f'<desc id="d">{escape(_describe(chart))}</desc>',
        f'<rect width="{WIDTH}" height="{height}" rx="8" fill="{theme["surface"]}"/>',
        f'<text x="{PAD}" y="{PAD + 15}" font-size="15" font-weight="600" fill="{theme["primary"]}">'
        f"{escape(chart.title)}</text>",
        f'<text x="{PAD}" y="{PAD + 35}" font-size="12" fill="{theme["secondary"]}">{escape(chart.subtitle)}</text>',
    ]
    if many:
        lx = PAD
        for index, series in enumerate(chart.series):
            colour = theme["series"][index]
            out.append(f'<rect x="{lx}" y="{PAD + 47}" width="10" height="10" rx="2" fill="{colour}"/>')
            out.append(
                f'<text x="{lx + 15}" y="{PAD + 56}" font-size="12" fill="{theme["secondary"]}">'
                f"{escape(series.name)}</text>"
            )
            lx += 15 + len(series.name) * CHAR + 20
    for tick in chart.ticks:
        x = sx(tick)
        out.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="{theme["grid"]}"/>')
        out.append(
            f'<text x="{x:.1f}" y="{top + plot_h + 16}" font-size="11" text-anchor="middle" fill="{theme["muted"]}"'
            f' style="font-variant-numeric: tabular-nums">{tick:g}{chart.unit}</text>'
        )
    out.append(f'<line x1="{x0}" y1="{top}" x2="{x0}" y2="{top + plot_h}" stroke="{theme["axis"]}"/>')
    for row_index, name in enumerate(chart.categories):
        y = top + row_index * row + 8
        out.append(
            f'<text x="{x0 - 10}" y="{y + group / 2 + 4:.1f}" font-size="12" text-anchor="end" '
            f'fill="{theme["primary"]}">{escape(name)}</text>'
        )
        for index, series in enumerate(chart.series):
            value = series.values[row_index]
            by = y + index * (thick + gap)
            end = sx(value.x)
            out.append(_bar(x0, by, end - x0, thick, theme["series"][index]))
            label_x = end
            interval = value.wilson()
            if interval:
                lo, hi = sx(interval[0]), sx(interval[1])
                mid = by + thick / 2
                out.append(
                    f'<line x1="{lo:.1f}" y1="{mid:.1f}" x2="{hi:.1f}" y2="{mid:.1f}" stroke="{theme["secondary"]}" '
                    f'stroke-width="1.5"/>'
                )
                for cap in (lo, hi):
                    out.append(
                        f'<line x1="{cap:.1f}" y1="{mid - 4:.1f}" x2="{cap:.1f}" y2="{mid + 4:.1f}" '
                        f'stroke="{theme["secondary"]}" stroke-width="1.5"/>'
                    )
                label_x = max(label_x, hi)
            out.append(
                f'<text x="{label_x + 6:.1f}" y="{by + thick / 2 + 4:.1f}" font-size="12" '
                f'fill="{theme["secondary"]}">{escape(value.text(chart.unit))}</text>'
            )
    if chart.note:
        out.append(
            f'<text x="{PAD}" y="{top + plot_h + 38}" font-size="11" fill="{theme["muted"]}">{escape(chart.note)}</text>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _describe(chart: Chart) -> str:
    parts = []
    for row_index, name in enumerate(chart.categories):
        cells = [f"{series.name} {series.values[row_index].text(chart.unit)}" for series in chart.series]
        parts.append(f"{name}: " + ", ".join(cells))
    return "; ".join(parts) + "."


def _rate(hits: int, total: int, label: str = "", interval: bool = True) -> Value:
    return Value(hits=hits, total=total, label=label, interval=interval)


def _secs(amount: float) -> Value:
    return Value(amount=amount)


WILSON = "Whiskers: 95% Wilson interval."
SECONDS = {"xmax": 12.0, "ticks": [0, 3, 6, 9, 12], "unit": " s"}

CHARTS = [
    Chart(
        "reminder-accuracy/charts/errors",
        "Reminder errors, before and after the fixes",
        "Run 2026-11-17-1105, quick tier, 3 reps. Lower is better.",
        ["Stale replies", "Reminder requests stored"],
        [
            Series("Before the fixes (7fcacca)", [_rate(2, 30), _rate(6, 12)]),
            Series("After (main 141ac18)", [_rate(1, 28), _rate(0, 12)]),
        ],
        note=WILSON,
    ),
    Chart(
        "reminder-accuracy/charts/correct",
        "What still works, before and after the fixes",
        "Run 2026-11-17-1105, quick tier, 3 reps. Higher is better.",
        ["Live reminders recalled", "Specific question right", "Life facts kept"],
        [
            Series("Before the fixes (7fcacca)", [_rate(21, 24), _rate(13, 15), _rate(9, 12)]),
            Series("After (main 141ac18)", [_rate(20, 24), _rate(12, 13), _rate(9, 12)]),
        ],
        note=WILSON,
    ),
    Chart(
        "reminder-accuracy/adhoc-2026-11-16/charts/stale",
        "Replies that treat an ended reminder as pending",
        "Copy of real memory, 3 questions x 4 runs. Lower is better.",
        ["Before (7fcacca)", "After #81", "After #82"],
        [
            Series(
                "Stale replies",
                [_rate(12, 12), _rate(6, 12, "about 6/12", False), _rate(1, 12, "about 1/12", False)],
            )
        ],
        note="Counts after #81 and #82 were read by hand, so no intervals are drawn.",
    ),
    Chart(
        "reminder-accuracy/adhoc-2026-11-16/charts/leak",
        "Reminder requests stored as memory",
        "Copy of real memory, 6 request lines x 3 runs. Lower is better.",
        ["Before (7fcacca)", "After #81"],
        [Series("Stored", [_rate(9, 18), _rate(0, 18)])],
        note=WILSON,
    ),
    Chart(
        "turn-latency-2026-11-17/charts/latency",
        "Median time per step",
        "CetiMind app log, 2026-11-17. qwen3.5-4b chat, nemotron-3-nano-4b tools.",
        ["Reply with thinking (30)", "Reply without thinking (8)", "Intent check (34)"],
        [Series("Median", [_secs(11.6), _secs(1.1), _secs(0.6)])],
        note="Number of turns in brackets. 20 of 34 routed turns also retried with thinking on.",
        **SECONDS,
    ),
    Chart(
        "schedule-tool-calls-2026-11-15/charts/calls",
        "Reminder requests that got a schedule_create call",
        "qwen3.5-9b, 6 request lines x 3 runs per variant. Higher is better.",
        ["A: thinking off", "B: thinking on", "C: off + prompt rule", "E: intent check, then C"],
        [Series("Called", [_rate(0, 18), _rate(15, 18), _rate(0, 18), _rate(0, 18)])],
        note=WILSON,
    ),
    Chart(
        "tool-turn-router-2026-11-15/charts/english",
        "Router errors on English lines",
        "Count of lines. Lower is better.",
        ["rules", "json", "kev", "embed_desc", "embed_pos", "embed_margin"],
        [
            Series("Misses (tool turn said no)", [Value(amount=v, label=str(v)) for v in (4, 0, 4, 1, 8, 6)]),
            Series("False alarms (plain line said yes)", [Value(amount=v, label=str(v)) for v in (8, 4, 9, 14, 10, 8)]),
        ],
        xmax=16,
        ticks=[0, 4, 8, 12, 16],
        unit="",
    ),
    Chart(
        "missed-tool-check-2026-11-15/charts/caught",
        "Skipped tool turns caught",
        "Replies that should have called a tool. Higher is better.",
        ["regex", "json_reply", "json_pair"],
        [
            Series("English (21)", [_rate(10, 21), _rate(14, 21), _rate(19, 21)]),
            Series("Japanese (23)", [_rate(0, 23), _rate(8, 23), _rate(22, 23)]),
        ],
        note=WILSON,
    ),
    Chart(
        "missed-tool-check-2026-11-15/charts/false-fires",
        "False fires on replies that were fine",
        "Lower is better.",
        ["regex", "json_reply", "json_pair"],
        [
            Series("English (20)", [_rate(1, 20), _rate(0, 20), _rate(9, 20)]),
            Series("Japanese (20)", [_rate(0, 20), _rate(0, 20), _rate(4, 20)]),
        ],
        note=WILSON,
    ),
    Chart(
        "tool-model-split-2026-11-16/charts/called",
        "Tool lines with the needed tool called",
        "30 tool lines per setup. Higher is better.",
        ["split", "qwen", "nemotron", "qwen_off", "split_tooloff"],
        [Series("Called", [_rate(29, 30), _rate(28, 30), _rate(27, 30), _rate(11, 30), _rate(5, 30)])],
        note=WILSON,
    ),
    Chart(
        "tool-model-split-2026-11-16/charts/time",
        "Median turn time",
        "46 turns per setup. Lower is faster.",
        ["split", "qwen", "nemotron", "qwen_off", "split_tooloff"],
        [Series("Median", [_secs(3.2), _secs(3.8), _secs(3.3), _secs(1.4), _secs(1.4)])],
        xmax=4.0,
        ticks=[0, 1, 2, 3, 4],
        unit=" s",
    ),
    Chart(
        "judge-model-2026-11-16/charts/judge",
        "Learn-step judge accuracy",
        "Hand-written lines, 3 runs each. Higher is better.",
        ["Fact extraction", "Fact updates"],
        [
            Series("qwen3.5-4b", [_rate(36, 36), _rate(6, 9)]),
            Series("nemotron-3-nano-4b", [_rate(30, 36), _rate(0, 9)]),
        ],
        note=WILSON,
    ),
]


def main() -> None:
    for chart in CHARTS:
        for mode, theme in THEMES.items():
            target = ROOT / f"{chart.path}-{mode}.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render(chart, theme), encoding="utf-8")
    print(f"{len(CHARTS)} charts, {len(CHARTS) * len(THEMES)} files")


if __name__ == "__main__":
    main()

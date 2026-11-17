# Tools

## Charts

`make_charts.py` draws every README chart as plain SVG, with no dependencies beyond Python 3.10. Each chart's numbers are copied from that experiment's results table, so change both together. Then run it from the repo root:

```bash
python tools/make_charts.py
```

Each chart is written twice, `<name>-light.svg` and `<name>-dark.svg`, into the experiment's `charts/` directory. A README shows the right one for the viewer's GitHub theme:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/<name>-dark.svg">
  <img alt="<title and every value>" src="charts/<name>-light.svg" width="680">
</picture>
```

Keep the results table next to the chart. The images are static, so the table is how a reader gets exact values.

Rules the charts follow:

- Horizontal bars, at most 20 px thick (16 px when grouped), square at the baseline with a 4 px rounded end.
- A legend for two or more series, none for one. The value sits at the bar tip in text ink, never in the series color.
- Rates drawn from counts get a 95% Wilson interval whisker. Counts that were read by hand get none, and the chart says so.
- Two series colors only. Blue is the first series and orange the second, in both themes.

The two-color palette passes every check of the palette validator in both modes:

| Mode | Colors | Worst CVD ΔE | Worst normal-vision ΔE | Contrast vs surface |
| --- | --- | --- | --- | --- |
| Light (surface `#fcfcfb`) | `#2a78d6`, `#eb6834` | 24.7 | 33.6 | ≥ 3:1 |
| Dark (surface `#1a1a19`) | `#3987e5`, `#d95926` | 26.8 | 31.8 | ≥ 3:1 |

Diagrams such as pipelines are written in Mermaid inside the README, which GitHub renders directly.

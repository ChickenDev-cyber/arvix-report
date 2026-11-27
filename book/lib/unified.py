"""Unified M1-M3 data loader and interactive Plotly helper for arvix-report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from IPython.display import HTML
import pandas as pd
import plotly.graph_objects as go


def _resolve_within(base: Path, name: str, suffix: str) -> Path:
    """Resolve a filename inside *base*, adding *suffix* if omitted."""
    filename = name if name.endswith(suffix) else f"{name}{suffix}"
    target = (base / filename).resolve()
    base_resolved = base.resolve()
    if not target.is_relative_to(base_resolved):
        raise ValueError(f"Path escapes {base_resolved}: {name!r}")
    if not target.is_file():
        raise FileNotFoundError(f"Missing unified report asset: {target}")
    return target


def repo_root(start: Path | None = None) -> Path:
    """Locate the book repository root by searching upwards for ``myst.yml``."""
    candidates = [start.resolve()] if start is not None else [
        Path.cwd().resolve(),
        Path(__file__).resolve().parent,
    ]
    for origin in candidates:
        for folder in (origin, *origin.parents):
            if (folder / "myst.yml").is_file():
                return folder
    raise FileNotFoundError("Could not locate repository root containing myst.yml")


def load_json(name: str) -> dict[str, Any]:
    """Load a verified JSON summary from ``data/unified/``."""
    path = _resolve_within(repo_root() / "data" / "unified", name, ".json")
    return json.loads(path.read_text(encoding="utf-8"))


def load_sample_csv(name: str) -> pd.DataFrame:
    """Load a real Parquet schema sample CSV from ``data/unified/samples/``."""
    path = _resolve_within(repo_root() / "data" / "unified" / "samples", name, ".csv")
    return pd.read_csv(path)


def render_plotly(fig: go.Figure, *, height: int | None = None) -> HTML:
    """Render a Plotly figure as static CDN HTML compatible with ``BASE_URL=/arvix-report``."""
    target_fig = fig
    if height is not None:
        target_fig = go.Figure(fig)
        target_fig.update_layout(height=height)
    html = target_fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        config={"responsive": True, "displaylogo": False},
    )
    return HTML(html)

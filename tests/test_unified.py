"""Tests for book/lib/unified.py and the data/unified/ bundle."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

from book.lib import unified


def test_repo_root_contains_myst_and_unified_dir() -> None:
    root = unified.repo_root()
    assert (root / "myst.yml").is_file()
    assert (root / "data" / "unified").is_dir()


def test_load_json_reads_verified_bundles() -> None:
    for name in (
        "m1_baseline_nov06.json",
        "m1_batch_summary.json",
        "m1_final_corpus.json",
        "m2_tokenizer_benchmark.json",
        "m2_unified_summary.json",
        "m3_unified_summary.json",
    ):
        payload = unified.load_json(name)
        assert isinstance(payload, dict)
        assert payload

    m2 = unified.load_json("m2_unified_summary")
    assert m2["total_papers_parsed"] == 22961
    assert m2["total_six_table_mib"] == 1199.45


def test_load_sample_csv_reads_all_six_tables() -> None:
    for table in ("papers", "references", "elements", "hierarchy", "bibtex", "predictions"):
        df = unified.load_sample_csv(table)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12


def test_resolve_rejects_traversal_and_missing_file() -> None:
    with pytest.raises(ValueError):
        unified.load_json("../../myst.yml")
    with pytest.raises(FileNotFoundError):
        unified.load_json("nonexistent_summary.json")


def test_render_plotly_outputs_static_cdn_html() -> None:
    fig = go.Figure(data=[go.Bar(x=["a", "b"], y=[1, 2])])
    rendered = unified.render_plotly(fig, height=320)
    html = rendered.data
    assert "plotly-graph-div" in html
    assert "cdn.plot.ly" in html
    assert fig.layout.height is None

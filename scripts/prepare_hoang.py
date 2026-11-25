#!/usr/bin/env python3
"""
scripts/prepare_hoang.py
------------------------
Script do Hoàng phụ trách.
Đọc dữ liệu pipeline thật từ:
  1. Milestone 1: Các thư mục handoff (5 owner: Hoàng-22, Mẫn Nhi-31, Huỳnh Nhi-30, Khang-24, Trọng-40).
  2. Milestone 2: Các tệp Parquet chuẩn hóa của Hoàng từ Google Drive (drive-data/dataset/).

Tính toán:
  - M1: 5 chỉ số bắt buộc theo đề bài Crawling, phân rã owner, benchmark Colab CPU.
  - M2: Thống kê độ phủ phiên bản, tỷ lệ rỗng (PDF-only), tỷ lệ khử trùng lặp (dedup),
        cơ cấu 11 loại kind trong elements, thống kê BibTeX, dung lượng lưu trữ Parquet.

Ghi file tổng hợp vào data/hoang/ và vẽ các biểu đồ vào book/figures/.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Đảm bảo in tiếng Việt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đảm bảo import được common.py
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from book.lib.common import (
    DEFAULT_DATA_DIR,
    compute_m1_statistics,
    load_accepted_results,
    load_benchmark,
)
from book.lib.hoang_benchmark import generate_stage_timing_chart
from book.lib.hoang_stats import generate_size_comparison_chart


def prepare_m2_data(m2_dir: Path, output_dir: Path, figures_dir: Path) -> dict | None:
    """Xử lý dữ liệu Milestone 2 từ các tệp Parquet nếu có."""
    papers_path = m2_dir / "papers.parquet"
    hier_path = m2_dir / "hierarchy.parquet"
    elem_path = m2_dir / "elements.parquet"
    bib_path = m2_dir / "bibtex.parquet"

    if not (papers_path.exists() and hier_path.exists() and elem_path.exists() and bib_path.exists()):
        print(f" -> [M2] Không tìm thấy đủ 4 tệp Parquet cốt lõi trong: {m2_dir}")
        return None

    try:
        import numpy as np
        import pandas as pd
        import pyarrow.parquet as pq
    except ImportError:
        print(" -> [M2] Cần pyarrow và pandas để xử lý Parquet.")
        return None

    print(f" -> [M2] Đang nạp và phân tích dữ liệu Milestone 2 từ {m2_dir}...")

    # 1. Đọc papers.parquet
    df_p = pq.read_table(papers_path).to_pandas()
    df_p["version_count"] = 1 + df_p["revised_dates"].apply(
        lambda x: len(x) if isinstance(x, (list, np.ndarray)) else 0
    )
    total_declared = int(df_p["version_count"].sum())

    # 2. Đọc hierarchy.parquet
    t_hier = pq.read_table(hier_path, columns=["arxiv_id", "version", "element_id"])
    df_h = t_hier.to_pandas()
    total_edges = len(df_h)
    parsed_vers = (
        df_h[["arxiv_id", "version"]].drop_duplicates().groupby("arxiv_id").size().rename("parsed_version_count")
    )
    edge_counts = df_h.groupby("arxiv_id").size().rename("hierarchy_edge_count")

    # 3. Đọc elements.parquet
    t_elem = pq.read_table(elem_path, columns=["arxiv_id", "element_id", "kind"])
    df_e = t_elem.to_pandas()
    total_unique_elements = len(df_e)
    dedup_elem_counts = df_e.groupby("arxiv_id").size().rename("dedup_element_count")
    kind_counts = df_e["kind"].value_counts().to_dict()

    # 4. Đọc bibtex.parquet
    t_bib = pq.read_table(bib_path)
    df_bib = t_bib.to_pandas()
    total_bib = len(df_bib)
    bib_papers = int(df_bib["arxiv_id"].nunique())
    bib_types = df_bib["entry_type"].str.lower().value_counts().head(6).to_dict()
    cits_per_paper = df_bib.groupby("arxiv_id").size()

    # Tính độ đầy đủ các trường BibTeX
    field_completeness = {}
    for col in ["title", "authors", "year", "doi", "journal", "url"]:
        s = df_bib[col]
        if col == "authors":
            non_null = s.apply(
                lambda x: len(x) > 0 if isinstance(x, (list, np.ndarray)) else (pd.notna(x) and x != "")
            ).sum()
        else:
            non_null = s.apply(lambda x: pd.notna(x) and str(x).strip() != "").sum()
        field_completeness[f"{col}_pct"] = round(non_null / total_bib * 100, 2)

    # 5. Hợp nhất bảng chi tiết từng bài báo
    df_merged = df_p[["arxiv_id", "version_count"]].set_index("arxiv_id")
    df_merged = df_merged.join(parsed_vers).fillna({"parsed_version_count": 0})
    df_merged["parsed_version_count"] = df_merged["parsed_version_count"].astype(int)
    df_merged["empty_version_count"] = df_merged["version_count"] - df_merged["parsed_version_count"]
    df_merged = df_merged.join(edge_counts).fillna({"hierarchy_edge_count": 0})
    df_merged["hierarchy_edge_count"] = df_merged["hierarchy_edge_count"].astype(int)
    df_merged["raw_element_count"] = df_merged["hierarchy_edge_count"]
    df_merged = df_merged.join(dedup_elem_counts).fillna({"dedup_element_count": 0})
    df_merged["dedup_element_count"] = df_merged["dedup_element_count"].astype(int)

    df_pub_out = df_merged.reset_index()[
        [
            "arxiv_id",
            "version_count",
            "empty_version_count",
            "parsed_version_count",
            "raw_element_count",
            "dedup_element_count",
            "hierarchy_edge_count",
        ]
    ]

    csv_path = output_dir / "m2_hierarchy_publications.csv"
    df_pub_out.to_csv(csv_path, index=False, encoding="utf-8")
    print(f" -> [M2] Đã xuất bảng CSV chi tiết: {csv_path} ({len(df_pub_out):,} dòng)")

    # 6. Tính dung lượng lưu trữ
    storage = {}
    total_bytes = 0
    for fname in ["papers.parquet", "hierarchy.parquet", "elements.parquet", "bibtex.parquet", "references.parquet"]:
        fpath = m2_dir / fname
        if fpath.exists():
            b = os.path.getsize(fpath)
            storage[fname] = {"bytes": b, "mb": round(b / (1024 * 1024), 2)}
            total_bytes += b
    storage["total_storage_bytes"] = total_bytes
    storage["total_storage_mb"] = round(total_bytes / (1024 * 1024), 2)

    # 7. Xuất file JSON tổng hợp
    parsed_docs = int(kind_counts.get("document", len(df_h[["arxiv_id", "version"]].drop_duplicates())))
    m2_summary = {
        "source_path": str(m2_dir),
        "is_mock": False,
        "arxiv_id_min": str(df_p["arxiv_id"].min()),
        "arxiv_id_max": str(df_p["arxiv_id"].max()),
        "total_publications": len(df_p),
        "publications_with_empty_versions": int((df_merged["empty_version_count"] > 0).sum()),
        "publications_all_empty": int((df_merged["parsed_version_count"] == 0).sum()),
        "declared_versions": total_declared,
        "parsed_versions": parsed_docs,
        "empty_versions": total_declared - parsed_docs,
        "raw_element_count_sum": total_edges,
        "dedup_element_count": total_unique_elements,
        "dedup_saved_count": total_edges - total_unique_elements,
        "dedup_ratio_pct": round((total_edges - total_unique_elements) / total_edges * 100, 2),
        "hierarchy_edge_count": total_edges,
        "avg_edges_per_parsed_version": round(total_edges / parsed_docs, 2),
        "element_kind_counts": {k: int(v) for k, v in kind_counts.items()},
        "bibtex": {
            "total_entries": total_bib,
            "unique_papers": bib_papers,
            "coverage_pct": round(bib_papers / len(df_p) * 100, 2),
            "mean_citations_per_paper": round(float(cits_per_paper.mean()), 2),
            "median_citations_per_paper": int(cits_per_paper.median()),
            "max_citations_per_paper": int(cits_per_paper.max()),
            "entry_types": {str(k): int(v) for k, v in bib_types.items()},
            "field_completeness": field_completeness,
        },
        "storage": storage,
    }

    json_path = output_dir / "m2_hierarchy_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(m2_summary, f, indent=2, ensure_ascii=False)
    print(f" -> [M2] Đã xuất tệp tóm tắt JSON: {json_path}")

    # 8. Vẽ đồ thị PNG (dùng matplotlib thuần, không phụ thuộc seaborn)
    try:
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = "DejaVu Sans"

        # Biểu đồ 1: Phân bố 11 kind trong elements
        fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)
        kinds = list(kind_counts.keys())
        counts = list(kind_counts.values())
        bars = ax.barh(kinds[::-1], counts[::-1], color="#2563eb", edgecolor="#1e40af", alpha=0.85)
        for bar in bars:
            w = bar.get_width()
            pct = w / total_unique_elements * 100
            ax.text(
                w + 15000,
                bar.get_y() + bar.get_height() / 2,
                f"{w:,.0f} ({pct:.1f}%)",
                va="center",
                ha="left",
                fontsize=8.5,
                color="#1f2937",
            )
        ax.set_title(
            "Phân bố 11 Loại Phần tử Cây Phân cấp trong Bảng elements (Hoàng - 5,000 bài)",
            fontsize=12,
            fontweight="bold",
            pad=12,
        )
        ax.set_xlabel("Số lượng Phần tử Độc bản", fontsize=10)
        ax.set_xlim(0, max(counts) * 1.25)
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        elem_chart_path = figures_dir / "m2-hoang-elements.png"
        plt.savefig(elem_chart_path)
        plt.close(fig)
        print(f" -> [M2] Đã tạo biểu đồ phần tử: {elem_chart_path}")

        # Biểu đồ 2: Phiên bản & Độ phủ
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=200)
        labels_pie = [f'Có TeX\n({m2_summary["parsed_versions"]:,})', f'Rỗng/PDF\n({m2_summary["empty_versions"]:,})']
        sizes_pie = [m2_summary["parsed_versions"], m2_summary["empty_versions"]]
        colors_pie = ["#10b981", "#f59e0b"]
        ax1.pie(
            sizes_pie,
            labels=labels_pie,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors_pie,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        )
        ax1.set_title("Tỷ lệ Phiên bản Dựng được Cây (Document)", fontsize=11, fontweight="bold")

        ver_dist = df_p["version_count"].value_counts().sort_index()
        ax2.bar(ver_dist.index.astype(str), ver_dist.values, color="#6366f1", edgecolor="#4338ca", alpha=0.85)
        for x, y in zip(ver_dist.index.astype(str), ver_dist.values):
            ax2.text(x, y + 40, f"{y:,}", ha="center", va="bottom", fontsize=8.5)
        ax2.set_title("Phân bố Số lượng Phiên bản trên mỗi Bài báo", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Số phiên bản (v1, v2...)", fontsize=9.5)
        ax2.set_ylabel("Số bài báo", fontsize=9.5)
        ax2.set_ylim(0, max(ver_dist.values) * 1.15)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)

        plt.tight_layout()
        ver_chart_path = figures_dir / "m2-hoang-versions.png"
        plt.savefig(ver_chart_path)
        plt.close(fig)
        print(f" -> [M2] Đã tạo biểu đồ phiên bản: {ver_chart_path}")
    except Exception as exc:
        print(f" -> [M2] Lỗi khi tạo đồ thị M2: {exc}")

    return m2_summary


def main():
    parser = argparse.ArgumentParser(description="Chuẩn bị dữ liệu thống kê & benchmark (Hoàng)")
    parser.add_argument("--run-dir", action="append", default=[], help="Thư mục chứa kết quả run thật M1")
    parser.add_argument("--m2-dir", help="Thư mục chứa 5 tệp Parquet thật của Milestone 2")
    args = parser.parse_args()

    output_dir = DEFAULT_DATA_DIR / "hoang"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = REPO_ROOT / "book" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("==> [Hoang] Đang xử lý số liệu thống kê và benchmark...")

    # Tìm các thư mục dữ liệu thật M1
    run_dirs = [Path(d) for d in args.run_dir]
    if not run_dirs:
        default_handoffs = REPO_ROOT.parent / "drive-data" / "handoffs"
        if default_handoffs.exists():
            run_dirs = sorted([d for d in default_handoffs.iterdir() if d.is_dir()])
            print(f" -> Tự động phát hiện {len(run_dirs)} thư mục handoffs thật: {[d.name for d in run_dirs]}")

    # 1. Nạp và tính toán thống kê M1
    accepted_files = []
    for rd in run_dirs:
        f = rd / "accepted_results.jsonl"
        if f.exists():
            accepted_files.append(f)

    if accepted_files:
        print(f" -> Đang nạp {len(accepted_files)} tệp accepted_results.jsonl thật...")
        records = load_accepted_results(accepted_files)
    else:
        print(" -> Không tìm thấy dữ liệu thật, sử dụng Mock Data.")
        records = load_accepted_results()

    stats = compute_m1_statistics(records)
    stats_file = output_dir / "statistics_summary.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(
        f" -> Đã lưu thống kê M1 vào: {stats_file} ({stats['total_papers_discovered']:,} bài, {stats['papers_complete']:,} bài hợp lệ)"
    )

    # 2. Xử lý benchmark M1
    bench_file_path = None
    timing_file_path = None
    for rd in run_dirs:
        if "hoang" in rd.name.lower():
            bf = rd / "benchmark" / f"{rd.name}.json"
            tf = rd / "benchmark" / f"{rd.name}-timing.json"
            if bf.exists():
                bench_file_path = bf
            if tf.exists():
                timing_file_path = tf
            break

    if bench_file_path and bench_file_path.exists():
        print(f" -> Đang nạp benchmark Colab CPU thật từ: {bench_file_path.name}")
        bench = load_benchmark(bench_file_path, timing_file_path)

        hoang_results = [r for r in records if r.get("owner") == "hoang"]
        if hoang_results:
            durations = defaultdict(float)
            for r in hoang_results:
                s = r.get("step") or r.get("task_type")
                durations[s] += r.get("duration_seconds") or 0.0

            bench["stage_timings"] = {
                "Discovery (T1)": round(durations.get("discovery", 198.86), 2),
                "Metadata (T2)": round(durations.get("metadata", 13618.60), 2),
                "Sources (T3)": round(durations.get("sources", 47810.12), 2),
            }
            if "discovery" in durations:
                bench["discovery_seconds"] = round(durations["discovery"], 2)
    else:
        print(" -> Không tìm thấy benchmark thật, sử dụng Mock Benchmark.")
        bench = load_benchmark()

    bench_file = output_dir / "benchmark_summary.json"
    with open(bench_file, "w", encoding="utf-8") as f:
        json.dump(bench, f, indent=2, ensure_ascii=False)
    print(f" -> Đã lưu benchmark M1 vào: {bench_file}")

    # 3. Sinh đồ thị M1
    chart1 = figures_dir / "fig-1-6-size-comparison.png"
    generate_size_comparison_chart(chart1)
    print(f" -> Đã tạo biểu đồ thống kê M1: {chart1}")

    chart2 = figures_dir / "fig-1-8-stage-timing.png"
    generate_stage_timing_chart(chart2)
    print(f" -> Đã tạo biểu đồ benchmark M1: {chart2}")

    # 4. Xử lý Milestone 2
    if args.m2_dir:
        m2_dir = Path(args.m2_dir)
        if m2_dir.exists():
            prepare_m2_data(m2_dir, output_dir, figures_dir)
    else:
        m2_sum_file = output_dir / "m2_hierarchy_summary.json"
        if m2_sum_file.exists():
            print(f" -> [M2] Sử dụng tệp thống kê toàn nhóm M2 sẵn có: {m2_sum_file}")
        else:
            default_m2 = REPO_ROOT.parent / "drive-data" / "dataset"
            if default_m2.exists():
                prepare_m2_data(default_m2, output_dir, figures_dir)
            else:
                print(f" -> [M2] Chưa tìm thấy thư mục M2 tại: {default_m2}")

    print("==> Hoàn tất chuẩn bị dữ liệu Milestone 1 & Milestone 2 cho Hoàng.")


if __name__ == "__main__":
    main()

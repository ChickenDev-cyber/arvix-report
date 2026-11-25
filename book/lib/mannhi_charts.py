"""Build SVG charts for Mẫn Nhi's report from real CSV data."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read CSV rows. Return an empty list when the file is missing."""
    if not path.exists():
        print(f"[SKIP] Không tìm thấy file: {path}")
        return []

    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes"}


def keep_real_rows(
    rows: list[dict[str, str]],
    filename: str,
    run_id: str | None = None,
) -> list[dict[str, str]]:
    """Keep only records explicitly marked as real data."""
    real_rows = []

    for row in rows:
        # Không xác định được real/mock thì không sử dụng.
        if (row.get("is_mock") or "").strip().lower() != "false":
            continue

        # Chỉ lọc run_id khi người dùng chỉ định.
        if run_id and (row.get("run_id") or "").strip() != run_id:
            continue

        real_rows.append(row)

    print(
        f"[INFO] {filename}: "
        f"{len(real_rows)}/{len(rows)} dòng dữ liệu thật được giữ lại."
    )

    if not rows:
        print(f"[WARNING] {filename} hiện không có dữ liệu.")

    elif not real_rows:
        print(
            f"[WARNING] {filename} không có dòng is_mock=False"
            + (f" thuộc run_id={run_id}." if run_id else ".")
        )

    return real_rows


def remove_old_charts(output_dir: Path, filenames: list[str]) -> None:
    """Remove old generated charts to avoid displaying stale results."""
    for filename in filenames:
        target = output_dir / filename
        if target.exists():
            target.unlink()


def build_charts(
    data_dir: Path,
    output_dir: Path,
    run_id: str | None = None,
    only: str = "all",
) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Cần cài matplotlib từ reqs/mannhi.txt để sinh biểu đồ."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    # Xóa biểu đồ cũ theo phạm vi đang tạo lại.
    m1_files = ["references-count.svg", "references-status.svg", "discovery-status.svg"]
    m2_files = ["m2-hierarchy-elements.svg", "m2-hierarchy-versions.svg"]
    if only in {"all", "m1"}:
        remove_old_charts(output_dir, m1_files)
    if only in {"all", "m2"}:
        remove_old_charts(output_dir, m2_files)

    created: list[Path] = []

    if only in {"all", "m1"}:
        # --------------------------------------------------
        # 1. REFERENCES
        # --------------------------------------------------
        refs = keep_real_rows(
            read_rows(data_dir / "references_per_paper.csv"),
            "references_per_paper.csv",
            run_id,
        )

        # Chỉ lấy bài thu thập thành công và có kết quả hoàn chỉnh.
        completed_refs = []

        for row in refs:
            if (row.get("status") or "").strip().lower() != "success":
                continue

            if not is_true(row.get("complete")):
                continue

            try:
                count = int(row.get("arxiv_reference_count", ""))
            except (TypeError, ValueError):
                continue

            if count < 0:
                continue

            completed_refs.append(count)

        # 1a. Phân bố số arXiv references trên mỗi bài.
        if completed_refs:
            fig, ax = plt.subplots()
            ax.hist(completed_refs, bins="auto")
            ax.set_title("Số arXiv references trên mỗi bài")
            ax.set_xlabel("Số arXiv ID duy nhất")
            ax.set_ylabel("Số bài")
            fig.tight_layout()

            target = output_dir / "references-count.svg"
            fig.savefig(target, format="svg")
            plt.close(fig)

            created.append(target)
        else:
            print(
                "[SKIP] references-count.svg: "
                "không có bài References thật, thành công và hoàn chỉnh."
            )

        # 1b. Phân bố trạng thái thu thập References.
        if refs:
            statuses = Counter(
                (row.get("status") or "").strip() or "missing"
                for row in refs
            )

            fig, ax = plt.subplots()
            labels = list(statuses.keys())
            values = [statuses[label] for label in labels]

            ax.bar(labels, values)
            ax.set_title("Trạng thái thu thập References")
            ax.set_xlabel("Status")
            ax.set_ylabel("Số bài")
            fig.tight_layout()

            target = output_dir / "references-status.svg"
            fig.savefig(target, format="svg")
            plt.close(fig)

            created.append(target)
        else:
            print("[SKIP] references-status.svg: không có dữ liệu References thật.")

    # --------------------------------------------------
    # 2. DISCOVERY
    # --------------------------------------------------
    if only in {"all", "m1"}:
        discovery = keep_real_rows(
            read_rows(data_dir / "discovery.csv"),
            "discovery.csv",
            run_id,
        )

        # CSV Discovery hiện có status, không có
        # candidates_checked và found_count.
        # Vì vậy chỉ vẽ biểu đồ trạng thái, không tự suy ra số liệu.
        if discovery:
            statuses = Counter(
                (row.get("status") or "").strip() or "missing"
                for row in discovery
            )

            fig, ax = plt.subplots()
            labels = list(statuses.keys())
            values = [statuses[label] for label in labels]

            ax.bar(labels, values)
            ax.set_title("Trạng thái xử lý Discovery")
            ax.set_xlabel("Status")
            ax.set_ylabel("Số bản ghi")
            fig.tight_layout()

            target = output_dir / "discovery-status.svg"
            fig.savefig(target, format="svg")
            plt.close(fig)

            created.append(target)
        else:
            print("[SKIP] discovery-status.svg: không có dữ liệu Discovery thật.")

    # --------------------------------------------------
    # 3. MILESTONE 2 — HIERARCHICAL PARSING (MẪN NHI)
    # --------------------------------------------------
    if only not in {"all", "m2"}:
        return created
    m2_summary_path = data_dir / "m2_hierarchy_summary.json"
    m2_pubs_path = data_dir / "m2_hierarchy_publications.csv"

    if m2_summary_path.is_file():
        m2_summary = json.loads(m2_summary_path.read_text(encoding="utf-8"))
        kind_counts = m2_summary.get("element_kind_counts") or {}
        if not m2_summary.get("is_mock", True) and kind_counts:
            labels = list(kind_counts.keys())
            values = [int(kind_counts[k]) for k in labels]
            total_pubs = int(m2_summary.get("total_publications", 0))

            fig, ax = plt.subplots(figsize=(9.5, 4.6))
            palette = [
                "#2563eb", "#0ea5e9", "#10b981", "#f59e0b", "#6366f1",
                "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#64748b", "#0f172a",
            ]
            colors = [palette[i % len(palette)] for i in range(len(labels))]
            bars = ax.bar(labels, values, color=colors)
            ax.set_yscale("log")
            ax.set_title(f"Phân bố loại phần tử (elements) — {total_pubs:,} bài Mẫn Nhi")
            ax.set_xlabel("Loại phần tử (kind)")
            ax.set_ylabel("Số lượng phần tử (thang log)")
            ax.tick_params(axis="x", rotation=25)
            for tick in ax.get_xticklabels():
                tick.set_horizontalalignment("right")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    val * 1.15,
                    f"{val:,}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
            ax.set_ylim(top=max(values) * 3.5)
            fig.tight_layout()

            target = output_dir / "m2-hierarchy-elements.svg"
            fig.savefig(target, format="svg")
            plt.close(fig)
            created.append(target)

    if m2_pubs_path.is_file() and m2_summary_path.is_file():
        m2_summary = json.loads(m2_summary_path.read_text(encoding="utf-8"))
        m2_pubs = read_rows(m2_pubs_path)
        if not m2_summary.get("is_mock", True) and m2_pubs:
            parsed_v = int(m2_summary.get("parsed_versions", 0))
            empty_v = int(m2_summary.get("empty_versions", 0))
            declared_v = int(m2_summary.get("declared_versions", parsed_v + empty_v))
            edge_counts = [
                int(r["hierarchy_edge_count"])
                for r in m2_pubs
                if r.get("hierarchy_edge_count", "").isdigit() and int(r["hierarchy_edge_count"]) > 0
            ]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))

            v_labels = ["Có cây phân cấp", "Phiên bản rỗng"]
            v_vals = [parsed_v, empty_v]
            bars1 = ax1.bar(v_labels, v_vals, color=["#16a34a", "#f59e0b"])
            ax1.set_title(f"Trạng thái phiên bản ({declared_v:,} phiên bản)")
            ax1.set_ylabel("Số phiên bản")
            ax1.grid(axis="y", linestyle="--", alpha=0.4)
            for bar, val in zip(bars1, v_vals):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    val + max(v_vals) * 0.02,
                    f"{val:,}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
            ax1.set_ylim(top=max(v_vals) * 1.15)

            if edge_counts:
                capped = [min(x, 4000) for x in edge_counts]
                ax2.hist(capped, bins=25, color="#3b82f6", edgecolor="white")
                ax2.set_title(f"Phân bố số cạnh hierarchy / bài (n={len(edge_counts):,} bài có TeX)")
                ax2.set_xlabel("Số cạnh hierarchy (cắt ngưỡng 4.000)")
                ax2.set_ylabel("Số bài báo")
                ax2.grid(axis="y", linestyle="--", alpha=0.4)

            fig.tight_layout()
            target = output_dir / "m2-hierarchy-versions.svg"
            fig.savefig(target, format="svg")
            plt.close(fig)
            created.append(target)

    return created


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/mannhi"),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("book/_static/generated"),
    )

    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Chỉ lấy dữ liệu của run_id cụ thể trong CSV.",
    )

    parser.add_argument(
        "--only",
        choices=["all", "m1", "m2"],
        default="all",
        help="Chọn nhóm biểu đồ cần tạo (all, m1, m2).",
    )

    args = parser.parse_args()

    generated = build_charts(
        args.data_dir,
        args.output_dir,
        args.run_id,
        args.only,
    )

    if generated:
        print("\n[OK] Các biểu đồ đã được tạo:")
        for path in generated:
            print(path)
    else:
        print("\n[WARNING] Không có biểu đồ nào được tạo.")
#!/usr/bin/env python3
"""
scripts/prepare_mannhi.py
-------------------------
Script do Mẫn Nhi phụ trách.
Xử lý dữ liệu discovery và references từ accepted_results.jsonl / config.py
để sinh các file trong data/mannhi/:
  - ranges.json
  - discovery.csv
  - references_per_paper.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "data" / "mannhi"

DISCOVERY_FIELDS = [
    "run_id", "arxiv_id", "owner", "status", "is_mock",
    "error_code", "retryable",
]
REFERENCE_FIELDS = [
    "run_id", "arxiv_id", "owner", "status", "complete", "is_mock",
    "s2_reference_count", "arxiv_reference_count",
    "complete_reference_count", "error_code", "retryable",
]
M2_PUB_FIELDS = [
    "arxiv_id", "version_count", "empty_version_count", "parsed_version_count",
    "raw_element_count", "dedup_element_count", "hierarchy_edge_count",
]


def normalize_owner(value: Any) -> str:
    """Normalize owner labels used by different pipeline/report versions."""
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def is_mannhi(record: dict[str, Any]) -> bool:
    return normalize_owner(record.get("owner")) in {"mannhi", "manhnhi", "ngomannhi"}


def find_source_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("ARXIV_PIPELINE_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())

    # Common layout when both repositories are cloned into one parent folder.
    candidates.extend([
        REPO_ROOT.parent / "arxiv-data-science",
        REPO_ROOT.parent / "arXiv",
        REPO_ROOT.parent / "arxiv_pipeline",
    ])

    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "src" / "arxiv_pipeline" / "config.py").is_file():
            return candidate

    checked = "\n".join(f"  - {p}" for p in candidates) or "  (không có đường dẫn nào)"
    raise FileNotFoundError(
        "Không tìm thấy repo arxiv-data-science (thiếu src/arxiv_pipeline/config.py).\n"
        "Hãy chạy lại với --source-root <đường-dẫn-repo-arxiv-data-science> "
        "hoặc đặt biến môi trường ARXIV_PIPELINE_ROOT.\n"
        f"Các đường dẫn đã kiểm tra:\n{checked}"
    )


def load_assigned_ranges(source_root: Path) -> list[dict[str, Any]]:
    src_dir = source_root / "src"
    sys.path.insert(0, str(src_dir))
    importlib.invalidate_caches()
    try:
        config = importlib.import_module("arxiv_pipeline.config")
        assigned = getattr(config, "ASSIGNED_RANGES")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            f"Không import được ASSIGNED_RANGES từ {src_dir / 'arxiv_pipeline' / 'config.py'}. "
            "Kiểm tra repo mã nguồn có đầy đủ thư mục src/arxiv_pipeline."
        ) from exc

    return [dict(item) for item in assigned if normalize_owner(item.get("owner")) == "mannhi"]


def to_arxiv_id(month: str, sequence: int) -> str:
    year, month_number = month.split("-", maxsplit=1)
    return f"{year[-2:]}{month_number}.{sequence:05d}"


def serialize_ranges(ranges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in ranges:
        start_month = item["start_month"]
        end_month = item["end_month"]
        result.append({
            "owner": item["owner"],
            "start": to_arxiv_id(start_month, int(item["start_id"])),
            "end": to_arxiv_id(end_month, int(item["end_id"])),
            "inclusive": bool(item.get("inclusive", True)),
        })
    return result


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    return value if isinstance(value, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.is_file():
        return records
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL lỗi tại {path}, dòng {line_number}: {exc}") from exc
            if isinstance(item, dict):
                records.append(item)
    return records


def get_error_fields(record: dict[str, Any]) -> tuple[str, Any]:
    error = record.get("error")
    if isinstance(error, dict):
        return str(error.get("code") or ""), error.get("retryable", "")
    return "", ""


def collect_run_data(source_root: Path, selected_run_id: str | None, extra_runs_dirs: list[Path] | None = None):
    candidate_run_dirs: list[Path] = []
    runs_dir = source_root / "runs"
    if runs_dir.is_dir():
        candidate_run_dirs.extend(sorted(p for p in runs_dir.iterdir() if p.is_dir()))
    for extra in extra_runs_dirs or []:
        if extra.is_dir():
            if (extra / "accepted_results.jsonl").is_file():
                candidate_run_dirs.append(extra)
            else:
                candidate_run_dirs.extend(sorted(p for p in extra.iterdir() if p.is_dir()))

    if not candidate_run_dirs:
        raise FileNotFoundError(f"Không tìm thấy thư mục runs trong {source_root}")

    run_dirs = candidate_run_dirs
    if selected_run_id:
        run_dirs = [p for p in run_dirs if p.name == selected_run_id]
        if not run_dirs:
            raise FileNotFoundError(f"Không tìm thấy run_id '{selected_run_id}' trong {runs_dir}")

    discovery_rows: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []
    run_manifest: list[dict[str, Any]] = []

    for run_dir in run_dirs:
        records = read_jsonl(run_dir / "accepted_results.jsonl")
        scope = read_json(run_dir / "scope.json")
        if not records and not scope:
            continue

        run_id = str(scope.get("run_id") or run_dir.name)
        run_is_mock = bool(scope.get("is_mock", False)) or any(r.get("is_mock") is True for r in records)
        own_records = [r for r in records if is_mannhi(r)]

        disc_count = 0
        ref_count = 0
        for record in own_records:
            task_type = str(record.get("task_type") or record.get("step") or "").lower()
            arxiv_id = str(record.get("arxiv_id") or "")
            status = record.get("status", "")
            is_mock = bool(record.get("is_mock", run_is_mock))
            error_code, retryable = get_error_fields(record)
            data = record.get("data") if isinstance(record.get("data"), dict) else {}

            if task_type == "discovery":
                if isinstance(data.get("papers"), list):
                    for item in data["papers"]:
                        pid = item.get("arxiv_id", "") if isinstance(item, dict) else str(item)
                        discovery_rows.append({
                            "run_id": run_id, "arxiv_id": pid,
                            "owner": record.get("owner", ""), "status": "found",
                            "is_mock": is_mock, "error_code": error_code,
                            "retryable": retryable,
                        })
                        disc_count += 1
                    for pid in data.get("excluded_ids") or []:
                        discovery_rows.append({
                            "run_id": run_id, "arxiv_id": str(pid),
                            "owner": record.get("owner", ""), "status": "excluded",
                            "is_mock": is_mock, "error_code": error_code,
                            "retryable": retryable,
                        })
                        disc_count += 1
                    for pid in data.get("unresolved_ids") or []:
                        discovery_rows.append({
                            "run_id": run_id, "arxiv_id": str(pid),
                            "owner": record.get("owner", ""), "status": "unresolved",
                            "is_mock": is_mock, "error_code": error_code,
                            "retryable": retryable,
                        })
                        disc_count += 1
                else:
                    discovery_rows.append({
                        "run_id": run_id, "arxiv_id": arxiv_id,
                        "owner": record.get("owner", ""), "status": status,
                        "is_mock": is_mock, "error_code": error_code,
                        "retryable": retryable,
                    })
                    disc_count += 1
            elif task_type == "references":
                metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
                complete_val = data.get("complete", record.get("complete", ""))
                reference_rows.append({
                    "run_id": run_id, "arxiv_id": arxiv_id,
                    "owner": record.get("owner", ""), "status": status,
                    "complete": complete_val,
                    "is_mock": is_mock,
                    "s2_reference_count": metrics.get("s2_reference_count", record.get("s2_reference_count", "")),
                    "arxiv_reference_count": metrics.get("arxiv_reference_count", record.get("arxiv_reference_count", "")),
                    "complete_reference_count": metrics.get("complete_reference_count", record.get("complete_reference_count", "")),
                    "error_code": error_code, "retryable": retryable,
                })
                ref_count += 1

        run_manifest.append({
            "run_id": run_id,
            "is_mock": run_is_mock,
            "accepted_result_records": len(records),
            "mannhi_records": len(own_records),
            "discovery_rows": disc_count,
            "reference_rows": ref_count,
        })

    return discovery_rows, reference_rows, run_manifest


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def collect_m2_hierarchy_data(source_root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Extract Milestone 2 hierarchical parsing summary from real SQLite if available."""
    db_path = source_root / "data" / "m2_parsing_real.sqlite"
    if not db_path.is_file():
        return None, []

    con = sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        pub_rows: list[dict[str, Any]] = []
        elem_counts = dict(cur.execute("SELECT arxiv_id, COUNT(*) FROM elements GROUP BY arxiv_id").fetchall())
        edge_counts = dict(cur.execute("SELECT arxiv_id, COUNT(*) FROM hierarchy GROUP BY arxiv_id").fetchall())

        total_declared = 0
        total_empty = 0
        pubs_with_empty = 0
        pubs_all_empty = 0
        raw_elem_sum = 0

        for arxiv_id, version_count, empty_json, raw_elem_count in cur.execute(
            "SELECT arxiv_id, version_count, empty_versions, raw_element_count "
            "FROM publications_meta ORDER BY arxiv_id"
        ):
            empty_list = json.loads(empty_json or "[]")
            empty_cnt = len(empty_list)
            parsed_cnt = max(0, int(version_count) - empty_cnt)
            total_declared += int(version_count)
            total_empty += empty_cnt
            if empty_cnt > 0:
                pubs_with_empty += 1
            if int(raw_elem_count) == 0:
                pubs_all_empty += 1
            raw_elem_sum += int(raw_elem_count)

            pub_rows.append({
                "arxiv_id": arxiv_id,
                "version_count": int(version_count),
                "empty_version_count": empty_cnt,
                "parsed_version_count": parsed_cnt,
                "raw_element_count": int(raw_elem_count),
                "dedup_element_count": int(elem_counts.get(arxiv_id, 0)),
                "hierarchy_edge_count": int(edge_counts.get(arxiv_id, 0)),
            })

        kind_counts = {
            str(kind): int(cnt)
            for kind, cnt in cur.execute(
                "SELECT kind, COUNT(*) FROM elements GROUP BY kind ORDER BY COUNT(*) DESC"
            ).fetchall()
        }
        dedup_elem_cnt = int(cur.execute("SELECT COUNT(*) FROM elements").fetchone()[0])
        hierarchy_edge_cnt = int(cur.execute("SELECT COUNT(*) FROM hierarchy").fetchone()[0])
        parsed_docs = int(kind_counts.get("document", 0))
        min_id, max_id = cur.execute("SELECT MIN(arxiv_id), MAX(arxiv_id) FROM publications_meta").fetchone()

        summary: dict[str, Any] = {
            "source_db": str(db_path),
            "is_mock": False,
            "arxiv_id_min": min_id,
            "arxiv_id_max": max_id,
            "total_publications": len(pub_rows),
            "publications_with_empty_versions": pubs_with_empty,
            "publications_all_empty": pubs_all_empty,
            "declared_versions": total_declared,
            "parsed_versions": parsed_docs,
            "empty_versions": total_empty,
            "raw_element_count_sum": raw_elem_sum,
            "dedup_element_count": dedup_elem_cnt,
            "hierarchy_edge_count": hierarchy_edge_cnt,
            "avg_edges_per_parsed_version": round(hierarchy_edge_cnt / parsed_docs, 2) if parsed_docs else 0.0,
            "element_kind_counts": kind_counts,
        }
        return summary, pub_rows
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Tổng hợp dữ liệu Discovery/References của Mẫn Nhi.")
    parser.add_argument("--source-root", help="Đường dẫn repo arxiv-data-science (chứa src/ và runs/).")
    parser.add_argument("--run-id", help="Chỉ xử lý một run_id cụ thể; mặc định xử lý tất cả run có dữ liệu.")
    parser.add_argument("--extra-runs-dir", action="append", default=[], help="Thư mục runs bổ sung (ví dụ m1-colab-man-nhi-01/corpus/runs).")
    args = parser.parse_args()

    extra_dirs = [Path(p).expanduser().resolve() for p in args.extra_runs_dir]
    default_local_m1 = REPO_ROOT.parent / "m1-colab-man-nhi-01" / "corpus" / "runs"
    if default_local_m1.is_dir() and default_local_m1.resolve() not in extra_dirs:
        extra_dirs.append(default_local_m1.resolve())

    try:
        source_root = find_source_root(args.source_root)
        assigned_ranges = load_assigned_ranges(source_root)
        discovery_rows, reference_rows, runs = collect_run_data(source_root, args.run_id, extra_dirs)
    except (FileNotFoundError, RuntimeError, ValueError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ranges_data = serialize_ranges(assigned_ranges)
    (OUTPUT_DIR / "ranges.json").write_text(
        json.dumps(ranges_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(OUTPUT_DIR / "discovery.csv", DISCOVERY_FIELDS, discovery_rows)
    write_csv(OUTPUT_DIR / "references_per_paper.csv", REFERENCE_FIELDS, reference_rows)

    m2_summary, m2_pub_rows = collect_m2_hierarchy_data(source_root)
    if m2_summary is not None:
        (OUTPUT_DIR / "m2_hierarchy_summary.json").write_text(
            json.dumps(m2_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_csv(OUTPUT_DIR / "m2_hierarchy_publications.csv", M2_PUB_FIELDS, m2_pub_rows)

    manifest = {
        "source_repository": str(source_root),
        "selected_run_id": args.run_id,
        "is_mock": any(item["is_mock"] for item in runs),
        "runs": runs,
        "discovery_rows": len(discovery_rows),
        "reference_rows": len(reference_rows),
        "note": "Kiểm tra is_mock trước khi sử dụng số liệu làm kết quả thực nghiệm.",
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[OK] Source repository: {source_root}")
    print(f"[OK] Dải ID Mẫn Nhi: {len(ranges_data)}")
    print(f"[OK] Discovery rows: {len(discovery_rows)}")
    print(f"[OK] References rows: {len(reference_rows)}")
    print(f"[OK] Output: {OUTPUT_DIR}")
    if manifest["is_mock"]:
        print("[WARNING] Dữ liệu có run mock (is_mock=true); không dùng làm kết quả thực nghiệm thật.")
    if not discovery_rows and not reference_rows:
        print("[WARNING] Chưa có accepted_results cho Mẫn Nhi; CSV chỉ có header.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

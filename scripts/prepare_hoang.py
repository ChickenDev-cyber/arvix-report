#!/usr/bin/env python3
"""
scripts/prepare_hoang.py
------------------------
Script do Hoàng phụ trách.
Đọc dữ liệu pipeline thật từ các thư mục handoff (mốc chốt của 5 owner:
Hoàng-22, Mẫn Nhi-31, Huỳnh Nhi-30, Khang-24, Trọng-40)
hoặc fallback về mock data nếu chưa có dữ liệu thật.

Tính toán 5 chỉ số bắt buộc theo đề bài Milestone 1:
  - Bảng tổng thể 5 chỉ số
  - Phân rã theo từng owner
  - Benchmark hiệu năng Colab CPU
Ghi file tổng hợp vào data/hoang/ và vẽ 2 biểu đồ vào book/figures/.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from collections import defaultdict

# Đảm bảo in tiếng Việt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đảm bảo import được common.py
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from book.lib.common import (
    load_accepted_results,
    load_benchmark,
    compute_m1_statistics,
    DEFAULT_DATA_DIR,
)
from book.lib.hoang_stats import generate_size_comparison_chart
from book.lib.hoang_benchmark import generate_stage_timing_chart


def main():
    parser = argparse.ArgumentParser(description="Chuẩn bị dữ liệu thống kê & benchmark (Hoàng)")
    parser.add_argument("--run-dir", action="append", default=[], help="Thư mục chứa kết quả run thật")
    args = parser.parse_args()

    output_dir = DEFAULT_DATA_DIR / "hoang"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("==> [Hoang] Đang xử lý số liệu thống kê và benchmark...")

    # Tìm các thư mục dữ liệu thật
    run_dirs = [Path(d) for d in args.run_dir]
    if not run_dirs:
        # Tự động tìm kiếm thư mục handoffs
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
    print(f" -> Đã lưu thống kê vào: {stats_file} ({stats['total_papers_discovered']:,} bài, {stats['papers_complete']:,} bài hợp lệ)")

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

        # Tính toán thời gian từng công đoạn từ accepted_results của Hoàng nếu có
        hoang_results = [r for r in records if r.get("owner") == "hoang"]
        if hoang_results:
            durations = defaultdict(float)
            for r in hoang_results:
                s = r.get("step") or r.get("task_type")
                durations[s] += (r.get("duration_seconds") or 0.0)
            
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
    print(f" -> Đã lưu benchmark vào: {bench_file}")

    # 3. Sinh đồ thị trực quan phục vụ báo cáo
    figures_dir = REPO_ROOT / "book" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    chart1 = figures_dir / "fig-1-6-size-comparison.png"
    generate_size_comparison_chart(chart1)
    print(f" -> Đã tạo biểu đồ thống kê: {chart1}")

    chart2 = figures_dir / "fig-1-8-stage-timing.png"
    generate_stage_timing_chart(chart2)
    print(f" -> Đã tạo biểu đồ benchmark: {chart2}")

    print("==> Hoàn tất chuẩn bị dữ liệu cho Hoàng.")


if __name__ == "__main__":
    main()

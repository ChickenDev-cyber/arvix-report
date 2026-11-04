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

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from book.lib.common import DEFAULT_DATA_DIR, load_accepted_results


def main():
    output_dir = DEFAULT_DATA_DIR / "mannhi"
    output_dir.mkdir(parents=True, exist_ok=True)
    print("==> [Mannhi] Khởi tạo dữ liệu cho Mẫn Nhi...")
    
    # Placeholder: Ghi file mẫu ban đầu
    ranges_file = output_dir / "ranges.json"
    if not ranges_file.exists():
        ranges_file.write_text('[\n  {"range": "2301.00001 - 2301.00100", "expected": 100}\n]\n', encoding="utf-8")
        print(f" -> Tạo file mẫu: {ranges_file}")

    print("==> Hoàn tất.")


if __name__ == "__main__":
    main()

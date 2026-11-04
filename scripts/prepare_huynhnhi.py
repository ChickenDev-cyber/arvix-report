#!/usr/bin/env python3
"""
scripts/prepare_huynhnhi.py
---------------------------
Script do Huỳnh Nhi phụ trách.
Xử lý dữ liệu metadata, sources và quality issues để sinh các file trong data/huynhnhi/:
  - metadata_per_paper.csv
  - sources_per_version.csv
  - quality_issues.csv
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from book.lib.common import DEFAULT_DATA_DIR, load_accepted_results


def main():
    output_dir = DEFAULT_DATA_DIR / "huynhnhi"
    output_dir.mkdir(parents=True, exist_ok=True)
    print("==> [Huynhnhi] Khởi tạo dữ liệu cho Huỳnh Nhi...")

    # Placeholder: Ghi file mẫu ban đầu
    quality_file = output_dir / "quality_issues.csv"
    if not quality_file.exists():
        quality_file.write_text("stage,field,issue_type,count\nmetadata,authors,missing,0\n", encoding="utf-8")
        print(f" -> Tạo file mẫu: {quality_file}")

    print("==> Hoàn tất.")


if __name__ == "__main__":
    main()

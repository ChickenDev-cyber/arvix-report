---
kernelspec:
  name: python3
  display_name: Python 3
---
# 3.1 Chuẩn bị & kiểm kê dữ liệu

> **Người phụ trách:** Huỳnh Nhi (`@TrinhNhi3011`)  
> **Reviewer:** Minh Trọng (`@ChickenDev-cyber`)

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m2 = unified.load_json("m2_unified_summary")
m3 = unified.load_json("m3_unified_summary")
OWNERS = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
```

Mục này trình bày bước kiểm kê nguồn đầu vào từ Milestone 1 và 2 (`inventory.json`) và hợp đồng toàn vẹn khóa `(arxiv_id, citation_key)` trước khi trích xuất đặc trưng. Mô-đun này (`prep`) là tầng đầu tiên của Chương 3. Nó kiểm tra rằng mọi tầng sau đọc đúng dữ liệu, đúng phiên bản và các bảng nối được với nhau, trước khi bước tạo nhãn và trích xuất đặc trưng bắt đầu.

## 1. Đầu vào và phạm vi

Mô-đun nhận đầu ra của hai milestone trước, mỗi thành viên một bộ cho dải 5000 bài của mình:

| Nguồn | Bảng | Vai trò trong Chương 3 |
|---|---|---|
| Milestone 1 | `papers` | Danh sách bài và metadata |
| Milestone 1 | `references` | Tập đích $\mathcal{R}_p$: các bài arXiv mà bài $p$ trích dẫn |
| Milestone 2 | `elements` | Nội dung câu có chứa lệnh trích dẫn |
| Milestone 2 | `hierarchy` | Cây phân cấp của từng phiên bản |
| Milestone 2 | `bibtex` | Tập mục tham khảo $\mathcal{E}_p$ đã hợp nhất của bài $p$ |

Lần chạy chính thức dùng chế độ `full`, `seed = 42`, cho cả năm owner (`hoang`, `huynh-nhi`, `khang`, `man-nhi`, `trong`), với mỗi owner một snapshot `m1:corpus + m2:parquet`. Mã nguồn được ghim ở commit `8345a27b495d2afa2730959529e76da93a3edd4f`.

## 2. Kiểm kê bằng `inventory.json`

Trước khi đọc dữ liệu, mô-đun lập một bản kiểm kê (`inventory.json`) liệt kê mọi file đầu vào và đối chiếu SHA-256 của từng file. Mục đích là để mọi kết quả ở các mục sau truy ngược được về đúng byte đầu vào, và để phát hiện ngay nếu có file bị sửa, thiếu hoặc lẫn giữa các owner.

Lần chạy chính thức băm 159 file đầu vào. Cùng với bản kiểm kê, tổ hợp nhãn cuối cùng cũng có dấu vân tay riêng (`labels_sha256`):

```{code-cell} python
:tags: [remove-input]
:label: tbl-3-1-runconfig
:caption: Cấu hình và dấu vân tay của lần chạy Milestone 3 (nguồn m3_unified_summary.json)
rc = m3["run_config"]
pd.DataFrame([
    {"Mục": "Chế độ", "Giá trị": rc["mode"]},
    {"Mục": "Hạt giống (seed)", "Giá trị": rc["seed"]},
    {"Mục": "Số owner", "Giá trị": len(rc["owners"])},
    {"Mục": "Số file đầu vào đã băm SHA-256", "Giá trị": rc["input_files_hashed_count"]},
    {"Mục": "Phiên bản mã nguồn", "Giá trị": rc["code_revision"][:7]},
    {"Mục": "labels_sha256", "Giá trị": rc["labels_sha256"][:16] + "…"},
    {"Mục": "Trạng thái", "Giá trị": f'{rc["status"]} / đánh giá {rc["evaluation_status"]}'},
    {"Mục": "Thời gian chạy toàn pipeline", "Giá trị": f'{rc["elapsed_seconds"]:.2f} s ({rc["elapsed_minutes"]} phút)'},
])
```

## 3. Hợp đồng khóa `(arxiv_id, citation_key)`

Bài toán của Chương 3 là với mỗi mục BibTeX trong bài $p$, tìm bài arXiv tương ứng trong danh sách tham khảo của $p$. Để làm được, bốn bảng phải nối với nhau qua các khóa sau, và mô-đun kiểm tra chúng trước khi chuyển sang bước tạo nhãn:

| Quan hệ | Khóa nối | Ý nghĩa |
|---|---|---|
| `bibtex` ↔ `papers` | `arxiv_id` | Mọi mục BibTeX phải thuộc một bài có trong `papers` |
| `references` ↔ `papers` | `arxiv_id` | Mọi dòng tham khảo thuộc một bài trích dẫn có thật |
| `bibtex` ↔ `elements` | `(arxiv_id, citation_key)` | Khóa trong lệnh `\cite{}` của `content` phải có trong `bibtex` (Chương 2 đã viết lại `\cite` sang khóa hợp nhất) |
| `bibtex` ↔ ứng viên $\mathcal{R}_p$ | `arxiv_id` | Mục BibTeX của bài $p$ chỉ được so khớp với `references` của chính bài $p$ |

Cặp `(arxiv_id, citation_key)` là khóa duy nhất của bảng `bibtex`. Hai điều được bảo đảm:

1. Không trùng khóa: trong một bài, không có hai mục BibTeX cùng `citation_key`. Việc này do bước khử trùng lặp ở mục 2.2 bảo đảm và được kiểm lại ở đây.
2. Không nối chéo bài: tập ứng viên của một bài chỉ gồm dòng `references` có cùng `arxiv_id`. Hai bài khác nhau có thể dùng cùng một `citation_key` (ví dụ `duchi2013local`) mà không nhầm lẫn, vì khóa nối luôn có cả `arxiv_id`.

Mẫu thật dưới đây cho thấy cùng một bài `2504.17523` xuất hiện ở cả hai bảng, với cùng khóa nối `arxiv_id`:

```{code-cell} python
:tags: [remove-input]
:label: tbl-3-1-bibtex
:caption: Mục BibTeX (bảng bibtex) của bài 2504.17523
unified.load_sample_csv("bibtex")[["arxiv_id", "citation_key", "entry_type", "title", "year"]]
```

```{code-cell} python
:tags: [remove-input]
:label: tbl-3-1-references
:caption: Tập đích (bảng references) của cùng bài 2504.17523
unified.load_sample_csv("references")[["arxiv_id", "ref_arxiv_id", "ref_title", "ref_submission_date"]]
```

Mỗi mục BibTeX (ví dụ `bassily2015local`, "Local, private, efficient protocols for succinct histograms") sẽ được so với các dòng của bảng `references` cùng bài (ví dụ `1504.04686` cùng tiêu đề). Các mục 3.2 và 3.3 mô tả cách gán nhãn và chia dữ liệu trên các cặp này.

## 4. Độ phủ: bài nào đủ điều kiện

Không phải bài nào cũng đi tiếp được: một bài chỉ có dòng trong bảng `predictions` khi có cả mục BibTeX (để làm truy vấn) lẫn danh sách tham khảo arXiv (để làm đích). Trong pool 2,525 bài (25 gán nhãn thủ công và 2,500 tự động), 1,934 bài có dòng dự đoán và 591 bài thì không, vì thiếu BibTeX:

- 201 bài không có phiên bản TeX nào phân tích được (`no_parsed_tex_versions`);
- 390 bài có TeX nhưng không trích ra được mục BibTeX nào (`has_tex_but_no_bibtex`).

```{code-cell} python
:tags: [remove-input]
:label: fig-3-1-missing
:caption: Số bài trong pool không có dòng dự đoán, theo thành viên và nguyên nhân
miss = m3["pool_and_split"]["missing_bibtex_by_owner"]
fig = go.Figure()
fig.add_bar(name="Không có phiên bản TeX phân tích được",
            x=OWNERS, y=[miss[o]["no_parsed_tex_versions"] for o in OWNERS])
fig.add_bar(name="Có TeX nhưng không có BibTeX",
            x=OWNERS, y=[miss[o]["has_tex_but_no_bibtex"] for o in OWNERS])
fig.update_layout(barmode="stack", yaxis_title="Số bài", margin=dict(t=30, b=40))
unified.render_plotly(fig, height=340)
```

Các số này khớp với thống kê ở Chương 2: trên 25,000 bài, 19,204 bài có BibTeX (`total_papers_with_bibtex`), còn 2,558 bài không có danh mục tham khảo nào và 3,182 bài chỉ có `.bbl` đã bị lọc ở bước tải nguồn (mục 1.4), nên những bài thuộc hai nhóm này không có dòng dự đoán.

## 5. Kết quả kiểm tra và bàn giao

Khi cả ba kiểm tra ở trên (băm đầu vào, hợp đồng khóa, độ phủ) đều đạt, mô-đun bàn giao cho tầng gán nhãn (mục 3.2) một tập dữ liệu đã được cố định bằng dấu vân tay. Kiểm định cuối ở mục 3.5 xác nhận 0 lỗi toàn vẹn trên toàn bộ bảng dự đoán.

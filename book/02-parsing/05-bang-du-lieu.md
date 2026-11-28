---
kernelspec:
  name: python3
  display_name: Python 3
---
# 2.5 Bảng dữ liệu (elements, hierarchy, bibtex)

> **Người phụ trách:** Huỳnh Nhi (`@TrinhNhi3011`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m2 = unified.load_json("m2_unified_summary")
```

Milestone 2 xuất ba bảng. Mục này mô tả dạng của chúng, quan hệ giữa chúng và 12 dòng mẫu thật lấy từ file Parquet; quá trình tạo ra nội dung đã được trình bày ở mục 2.1 và 2.2.

```{code-cell} python
:tags: [remove-input]
:label: tbl-2-5-size
:caption: Quy mô ba bảng Milestone 2
import pandas as pd
pq = m2["six_table_parquet_bytes"]
rows = [
    ("elements", m2["total_unique_elements"], pq["elements"]),
    ("hierarchy", m2["total_hierarchy_edges"], pq["hierarchy"]),
    ("bibtex", m2["total_unified_bibtex_rows"], pq["bibtex"]),
]
df = pd.DataFrame(
    [{"Bảng": n, "Số dòng": r, "Dung lượng Parquet (MiB)": round(b / 2**20, 2)} for n, r, b in rows]
)
total = {"Bảng": "Tổng", "Số dòng": int(df["Số dòng"].sum()),
         "Dung lượng Parquet (MiB)": m2["m2_three_table_parquet_mib"]}
pd.concat([df, pd.DataFrame([total])], ignore_index=True)
```

Ba bảng có tổng dung lượng 1,117.27 MiB (1.091 GiB), trong đó `elements` chiếm phần lớn.

```{code-cell} python
:tags: [remove-input]
:label: fig-2-5-size
:caption: Dung lượng Parquet của ba bảng Milestone 2 (MiB)
names = ["elements", "hierarchy", "bibtex"]
vals = [round(pq[n] / 2**20, 2) for n in names]
fig = go.Figure(go.Bar(x=names, y=vals, text=[f"{v:,.2f}" for v in vals], textposition="outside"))
fig.update_layout(yaxis_title="MiB", margin=dict(t=30, b=40))
unified.render_plotly(fig, height=320)
```

## 1. Bảng `elements`

Mỗi dòng là một phần tử khác nhau của một bài, tính trên mọi phiên bản. Một phần tử có nội dung giống hệt nhau (sau khi làm sạch) ở nhiều phiên bản chỉ chiếm một dòng.

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `element_id` | string | non-null, khóa chính | Định danh phần tử, duy nhất trong bài |
| `arxiv_id` | string | non-null | Bài chứa phần tử |
| `kind` | string (dictionary) | | Loại phần tử, một trong 11 giá trị: `document`, `section`, `subsection`, `subsubsection`, `paragraph`, `sentence`, `formula`, `figure`, `itemize`, `enumerate`, `item` |
| `content` | string | | Nội dung văn bản sau khi làm sạch và chuẩn hóa |

Kiểu *dictionary* nghĩa là cột chỉ nhận một tập nhỏ giá trị lặp lại, nên Parquet lưu theo dạng từ điển cho gọn. Bảng có 11,098,189 dòng; câu (`sentence`) là loại nhiều nhất với 8,634,050 dòng (77.8%).

12 dòng đầu của bài `2504.17523`:

```{code-cell} python
:tags: [remove-input]
:label: tbl-2-5-elements
:caption: 12 dòng thật của bảng elements
unified.load_sample_csv("elements")
```

## 2. Bảng `hierarchy`

Mỗi dòng là một cạnh giữa nút con và nút cha trong cây của một phiên bản.

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `arxiv_id` | string | non-null | Bài |
| `version` | int | | Phiên bản (1, 2, …) |
| `element_id` | string | non-null, khóa ngoại tới `elements` | Nút con |
| `parent_id` | string | non-null, khóa ngoại tới `elements` | Nút cha |

Vì phần tử giống nhau giữa các phiên bản dùng chung một `element_id`, cây của v1 và v2 có thể cùng trỏ tới một dòng trong `elements`. Muốn dựng lại cây của phiên bản N thì lọc `hierarchy` theo (`arxiv_id`, `version = N`) rồi nối với `elements` qua `element_id`. Một phiên bản không có TeX (mục 1.4) không có cạnh nào trong bảng này, nhưng vẫn được ghi nhận là phiên bản rỗng trong thống kê độ phủ (mục 2.3). Bảng có 16,185,255 dòng, nhiều hơn `elements` vì mỗi phần tử dùng chung xuất hiện một cạnh ở mỗi phiên bản chứa nó.

```{code-cell} python
:tags: [remove-input]
:label: tbl-2-5-hierarchy
:caption: Các dòng thật của bảng hierarchy (phiên bản 1 của bài 2504.17523)
unified.load_sample_csv("hierarchy")
```

Trong mẫu trên, các câu `s1`…`s6` (tóm tắt) có cha là nút gốc `root1`, còn `h1` là tiêu đề mục "Introduction" cũng treo dưới `root1`; các câu `s7` trở đi là con của `h1`.

## 3. Bảng `bibtex`

Mỗi dòng là một mục tài liệu tham khảo của một bài sau khi đã khử trùng lặp và hợp nhất trường (mục 2.2).

| Cột | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| `arxiv_id` | string | non-null | Bài trích dẫn |
| `citation_key` | string | non-null | Khóa trích dẫn đã chọn sau khi gộp |
| `entry_type` | string (dictionary) | | `article`, `inproceedings`, `misc`, … |
| `title` | string | | Tiêu đề |
| `authors` | list of strings | | Danh sách tác giả |
| `year` | int | nullable | Năm |
| `doi` | string | | DOI |
| `journal` | string | | Tạp chí hoặc hội nghị |
| `url` | string | | Đường dẫn |

Cặp (`arxiv_id`, `citation_key`) xác định duy nhất một dòng. Mọi lệnh `\cite{}` trong nội dung đã được đổi sang khóa này, nên khóa trong `content` của `elements` khớp được với `bibtex`. Bảng có 975,674 dòng thuộc 19,204 bài. Các trường `doi` (34.13%) và `url` (20.64%) thường để trống vì nhiều nguồn tham khảo không ghi; `title` có ở 99.23% và `year` ở 98.36% số dòng.

```{code-cell} python
:tags: [remove-input]
:label: tbl-2-5-bibtex
:caption: 12 dòng thật của bảng bibtex
unified.load_sample_csv("bibtex")
```

## 4. Định danh `element_id`

Theo đề, `element_id` bắt đầu bằng khóa của bài, tiếp theo là một phần phân biệt duy nhất trong bài. Trong dữ liệu chính thức, khóa bài chính là `arxiv_id` giữ nguyên dấu chấm, và phần phân biệt gồm loại nút kèm số thứ tự, cách nhau bằng `#`:

| Mẫu | Loại nút | Ví dụ |
|---|---|---|
| `<arxiv_id>#root<N>` | Nút gốc `document` của phiên bản N | `2504.17523#root1` |
| `<arxiv_id>#h<N>` | Tiêu đề mục | `2504.17523#h1` |
| `<arxiv_id>#s<N>` | Câu | `2504.17523#s1` |

Mỗi phiên bản có nút gốc riêng (`root1`, `root2`, …), còn phần tử có nội dung giống nhau giữa các phiên bản chỉ xuất hiện một lần trong `elements` dù có mặt ở nhiều cây. Đây là kết quả của khử trùng lặp mức nội dung ở mục 2.2.

## 5. Tài liệu tham khảo

- Đề bài Milestone 2. https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/parsing
- Apache Parquet. *Encodings: Dictionary Encoding*. https://parquet.apache.org/docs/file-format/data-pages/encodings/

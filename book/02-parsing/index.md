---
kernelspec:
  name: python3
  display_name: Python 3
---
# Chương 2. Milestone 2: Phân tích cú pháp phân cấp (Parsing)

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

Chương 1 kết thúc với một kho nguồn TeX/BibTeX được lưu theo từng phiên bản của mỗi bài báo (mục 1.4), kèm metadata và lịch sử phiên bản (mục 1.3). Chương 2 mô tả cách biến kho nguồn này thành dữ liệu có cấu trúc: mỗi phiên bản của một bài được phân tích thành một cây phân cấp, nội dung được làm sạch và chuẩn hóa, các mục tài liệu tham khảo được đưa về BibTeX thống nhất, và phần trùng lặp giữa các phiên bản được gộp lại.

Kết quả chốt: pipeline phân tích thành công 22,961 / 25,000 bài (91.84%) và 37,967 / 40,896 phiên bản (92.84%). Phần còn lại là các bài và phiên bản không có TeX (PDF-only, DOCX) nên được ghi nhận là rỗng. Đầu ra gồm 11,098,189 phần tử, 16,185,255 cạnh phân cấp và 975,674 dòng BibTeX.

## 1. Đầu vào từ Milestone 1

- Nguồn TeX/BibTeX của từng phiên bản: chỉ gồm file `.tex` và `.bib`; các lệnh `\begin{figure}`, `\includegraphics` vẫn còn trong TeX dù file hình đã bị bỏ (mục 1.4).
- Danh sách phiên bản của mỗi bài, lấy từ metadata đã được xác minh (mục 1.3).
- Phiên bản không có TeX (`unsupported`: chỉ có PDF, DOCX hoặc gói không có `.tex`) vẫn có bản ghi rỗng. Theo đề, những phiên bản này không sinh phần tử nào nhưng phải được ghi nhận là rỗng và tính vào độ phủ phiên bản, không bị bỏ qua.

## 2. Ba thách thức của TeX trên arXiv

Nguồn của arXiv là mã do hàng chục nghìn tác giả tự viết, nên không có cấu trúc thống nhất. Thiết kế của chương xuất phát từ ba khó khăn thực tế:

1. Một bài là nhiều file, và không rõ file nào là gốc. Gói nguồn có thể chứa nhiều file `.tex` (chương, phụ lục, bản nháp, mẫu tạp chí). Chỉ một file chứa `\documentclass` là tệp gốc thật, và các file khác được kéo vào bằng `\input`/`\include`. Chọn nhầm gốc làm cả cây sai. Việc chọn gốc và mở rộng `\input` an toàn được mô tả ở mục 2.1.
2. Nội dung lẫn với lệnh định dạng và toán. Một câu văn xen kẽ `\textbf{}`, `\cite{}`, công thức nội dòng `$...$`, macro tự định nghĩa. Dấu chấm trong `e.g.`, `Fig.` hay trong công thức làm tách câu theo quy tắc đơn giản bị sai. Phải làm sạch mà không phá vùng toán, rồi mới tách câu (mục 2.2).
3. Tài liệu tham khảo ở nhiều dạng khác nhau. Trên 25,000 bài, nguồn tham khảo gồm file `.bib` (14,152 bài), `\bibitem` ngay trong `.tex` (4,846 bài), cả hai (262 bài), chỉ có `.bbl` do BibTeX sinh sẵn mà bị lọc mất nên không còn danh mục (`bbl_missing`, 3,182 bài), và không có danh mục nào (2,558 bài).

```{code-cell} python
:tags: [remove-input]
:label: fig-2-0-bibsource
:caption: Nguồn tài liệu tham khảo của 25,000 bài
src = m2["bib_source_counts_total"]
labels = {
    "bib_file": "Có file .bib",
    "bibitem": "Chỉ \\bibitem",
    "both": "Cả hai",
    "bbl_missing": "Chỉ có .bbl (đã bị lọc)",
    "none": "Không có danh mục",
}
order = ["bib_file", "bibitem", "both", "bbl_missing", "none"]
fig = go.Figure(go.Bar(
    x=[labels[k] for k in order],
    y=[src[k] for k in order],
    text=[f"{src[k]:,}" for k in order],
    textposition="outside",
))
fig.update_layout(yaxis_title="Số bài", margin=dict(t=30, b=40))
unified.render_plotly(fig, height=340)
```

## 3. Kiến trúc: đảo thứ tự xử lý

Cách làm tự nhiên là dựng cây trước, khử trùng lặp, rồi mới xử lý tài liệu tham khảo. Nhóm làm ngược lại, vì khử trùng lặp dựa trên nội dung, mà nội dung chứa lệnh `\cite{key}`. Hai phiên bản của một bài có thể dùng hai khóa khác nhau cho cùng một tài liệu (`ye2019privkv` ở v1, `Ye2019PrivKV` ở v2); nếu chưa thống nhất khóa thì cùng một câu bị coi là hai câu khác nhau và không được gộp.

Vì vậy pipeline chạy theo thứ tự sau:

1. Trích xuất và hợp nhất BibTeX từ `.bib`, `\bibitem` (và các dạng tương đương) của mọi phiên bản, gộp các mục trùng thành một khóa duy nhất cho mỗi bài.
2. Viết lại mọi `\cite{}` trong TeX sang khóa đã hợp nhất.
3. Dựng cây phân cấp cho từng phiên bản từ TeX đã được viết lại.
4. Khử trùng lặp phần tử giữa các phiên bản, giờ đã so sánh được trên nội dung có khóa trích dẫn ổn định.

Nhờ đảo thứ tự này, khử trùng lặp mức nội dung giảm số phần tử từ 16,223,222 xuống 11,098,189 (giảm 5,125,033, tức 31.59%), và bảng `bibtex` giữ khóa nhất quán với `content` của `elements`.

```{code-cell} python
:tags: [remove-input]
:label: fig-2-0-dedup
:caption: Số phần tử trước và sau khử trùng lặp (toàn corpus)
before = m2["total_raw_element_occurrences"]
after = m2["total_unique_elements"]
fig = go.Figure(go.Bar(
    x=["Trước khử trùng lặp", "Sau khử trùng lặp"],
    y=[before, after],
    text=[f"{before:,}", f"{after:,}"],
    textposition="outside",
))
fig.update_layout(yaxis_title="Số phần tử", margin=dict(t=30, b=40))
unified.render_plotly(fig, height=340)
```

## 4. Đầu ra

Ba bảng theo đề, mô tả chi tiết ở mục 2.5, tổng dung lượng Parquet 1,117.27 MiB (1.091 GiB):

- `elements`: mỗi phần tử khác nhau của một bài (qua mọi phiên bản) là một dòng;
- `hierarchy`: các cạnh cha-con của cây phân cấp, theo từng phiên bản;
- `bibtex`: các mục tài liệu tham khảo sau khi khử trùng lặp và hợp nhất.

## 5. Cách đọc chương này

| Mục | Nội dung |
|---|---|
| [2.1 Phân tích cú pháp phân cấp](01-phan-cap.md) | Nhận diện file gốc có `\documentclass`, đi theo `\input`/`\include`, dựng cây Document → Section → … → Sentence/Block Formula/Figure |
| [2.2 Chuẩn hóa và khử trùng lặp](02-chuan-hoa.md) | Làm sạch lệnh định dạng, chuẩn hóa toán, chuyển `\bibitem` sang BibTeX, khử trùng lặp mức tham chiếu và mức nội dung giữa các phiên bản |
| [2.3 Thống kê](03-thong-ke.md) | Tỷ lệ parse thành công, độ phủ phiên bản, số phần tử và số mục tham chiếu trước/sau khử trùng lặp |
| [2.4 Benchmark](04-benchmark.md) | Thời gian chạy toàn bộ, thời gian trung bình mỗi bài, RAM tối đa trên Colab CPU |
| [2.5 Bảng dữ liệu](05-bang-du-lieu.md) | Cột, kiểu và quan hệ của ba bảng `elements`, `hierarchy`, `bibtex`, kèm 12 dòng mẫu thật |

Các mục 2.1 đến 2.3 nối tiếp nhau theo thứ tự xử lý: dựng cây (2.1), chuẩn hóa và gộp (2.2), rồi đo kết quả (2.3). Người chỉ cần biết dạng dữ liệu đầu ra có thể đọc thẳng mục 2.5.

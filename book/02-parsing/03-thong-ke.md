---
kernelspec:
  name: python3
  display_name: Python 3
---

# 2.3 Thống kê Phân tích Cú pháp (Parsing Statistics)

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Minh Trọng (`@ChickenDev-cyber`), Mẫn Nhi (`@NhiNgo49`)

Tiểu mục này trình bày các chỉ số thống kê định lượng của quá trình phân tích cú pháp mã nguồn TeX, dựng cây phân cấp văn bản và hợp nhất thư mục tài liệu tham khảo BibTeX (Milestone 2). Toàn bộ số liệu được trích xuất trực tiếp từ kết quả chạy thực tế trên **25,000 bài báo** được lưu trữ chuẩn hóa tại `data/unified/m2_unified_summary.json`.

---

## 1. Bảng chỉ số thống kê tổng hợp toàn nhóm Milestone 2

Dưới đây là các chỉ số định lượng then chốt của pipeline Milestone 2, tuân thủ tuyệt đối quy định của đề bài:

| STT | Chỉ số Thống kê theo Đề bài | Giá trị Định lượng Toàn Nhóm | Tỷ lệ / Đánh giá | Phương pháp & Ý nghĩa Kỹ thuật |
|:---:|:---|:---:|:---:|:---|
| **1** | **Tổng số bài báo phân tích (Total Publications)** | **25,000 bài** | **100.0%** | Phân bổ đồng đều 5,000 bài cho 5 thành viên (từ tháng 09/2024 đến 07/2025) |
| | * Bài báo phân tích thành công (Có TeX) | **22,961 bài** | **91.84%** | Có ít nhất một phiên bản phân tích thành công và dựng cây phân cấp |
| | * Bài báo rỗng (PDF-only / Unsupported) | **2,039 bài** | **8.16%** | Tác giả chỉ nộp PDF hoặc định dạng không hỗ trợ trích xuất nguồn từ M1 |
| **2** | **Tổng số phiên bản khai báo (Declared Versions)** | **40,896 phiên bản** | 1.636 ver/bài | Tính từ $v_1$ và toàn bộ mảng `revised_dates` trong siêu dữ liệu arXiv |
| | * Phiên bản parse thành công (Có nguồn TeX) | **37,967 phiên bản** | **92.84%** | Dựng thành công cây phân cấp với nút gốc `document` |
| | * Phiên bản rỗng được ghi nhận hợp lệ | **2,929 phiên bản** | **7.16%** | Tuân thủ đề bài: ghi nhận `nodes = []`, không sinh cạnh trong `hierarchy` |
| **3** | **Độ bao phủ Phiên bản (Version Coverage)** | **40,896 / 40,896 versions** | **100.0%** | 100% tất cả các phiên bản khai báo đều được theo dõi và xử lý nhất quán |
| **4** | **Số phần tử nội dung (`elements`)** | | | |
| | * Trước khi khử trùng lặp (Tổng cộng thô) | **16,223,222 elements** | 100.0% | Tổng số lần xuất hiện của các câu văn xuôi, công thức, bảng biểu... |
| | * Sau khi khử trùng lặp toàn văn | **11,098,189 elements** | **68.41%** | Chỉ lưu một bản ghi duy nhất cho các phần tử trùng khớp nội dung làm sạch |
| | * **Mức giảm trùng lặp nội dung (Dedup Saved)** | **-5,125,033 elements** | **Tiết kiệm 31.59%** | Giảm thiểu 31.59% số dòng lưu trữ văn bản dư thừa giữa các phiên bản |
| **5** | **Số cạnh quan hệ phân cấp (`hierarchy`)** | **16,185,255 edges** | 426.3 edges/ver | Quan hệ cha - con biểu diễn cấu trúc cây bài báo qua các phiên bản |
| **6** | **Số mục tài liệu tham khảo (`bibtex`)** | **975,674 entries** | 47.8 entries/bài | Hợp nhất từ file `.bib` và khối `\bibitem` trên 20,409 bài có BibTeX |
| **7** | **Dung lượng lưu trữ Parquet 3 bảng M2** | **1,117.27 MiB** (1.091 GiB) | ~223.5 MiB/owner | 3 bảng Parquet M2 (`elements`, `hierarchy`, `bibtex`) nén Snappy |

---

## 2. Phân rã thống kê chi tiết theo 5 thành viên (Owner Breakdown)

Dữ liệu phân tích cú pháp được bóc tách chi tiết theo 5 phân dải 5,000 bài của từng thành viên:

| Thành viên (Owner) | Bài có TeX | Phiên bản Khai báo | Phiên bản Parse được | Phiên bản Rỗng | Phần tử Thô | Phần tử Độc bản (Dedup) | Tỷ lệ Giảm Dedup | Số cạnh Hierarchy | Mục BibTeX | Dung lượng Parquet M2 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Huỳnh Nhi** (`huynh-nhi`) | 4,578 | 8,268 | 7,687 | 581 (7.03%) | 3,194,213 | 2,167,101 | **32.16%** | 3,186,526 | 195,076 | 217.22 MiB |
| **Mẫn Nhi** (`man-nhi`) | 4,544 | 8,251 | 7,592 | 659 (7.99%) | 3,276,789 | 2,221,136 | **32.22%** | 3,269,197 | 195,360 | 222.02 MiB |
| **Hoàng** (`hoang`) | 4,664 | 8,384 | 7,888 | 496 (5.92%) | 3,262,182 | 2,198,596 | **32.60%** | 3,254,294 | 203,414 | 227.36 MiB |
| **Minh Trọng** (`trong`) | 4,585 | 8,060 | 7,449 | 611 (7.58%) | 3,334,790 | 2,288,312 | **31.38%** | 3,327,341 | 194,577 | 227.95 MiB |
| **Phúc Khang** (`khang`) | 4,590 | 7,933 | 7,351 | 582 (7.34%) | 3,155,248 | 2,223,044 | **29.54%** | 3,147,897 | 187,247 | 222.72 MiB |
| **TỔNG CỘNG TOÀN NHÓM** | **22,961** | **40,896** | **37,967** | **2,929 (7.16%)** | **16,223,222** | **11,098,189** | **31.59%** | **16,185,255** | **975,674** | **1,117.27 MiB** |

---

## 3. Trực quan hóa dữ liệu tương tác (Plotly)

### A. Phân bố 11 loại phần tử trong cây phân cấp (`elements`)

Cây phân cấp của mỗi phiên bản được phân rã thành 11 loại phần tử (`kind`). Biểu đồ dưới đây thể hiện số lượng và tỷ trọng của từng loại phần tử độc bản sau khi khử trùng lặp toàn văn:

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m2 = unified.load_json("m2_unified_summary")
kinds = m2["element_kind_distribution"]
tot = m2["total_unique_elements"]

fig_kinds = go.Figure(go.Bar(
    x=list(kinds.values()),
    y=list(kinds.keys()),
    orientation="h",
    text=[f"{v:,} ({v/tot:.2%})" for v in kinds.values()],
    textposition="auto",
    marker=dict(
        color=list(kinds.values()),
        colorscale="Viridis",
        showscale=False
    )
))

fig_kinds.update_layout(
    title="<b>Phân bố 11 loại phần tử cây phân cấp sau khử trùng lặp (11,098,189 elements)</b>",
    xaxis_title="Số lượng phần tử độc bản",
    yaxis_title="Loại phần tử (kind)",
    yaxis=dict(autorange="reversed"),
    template="plotly_white",
    height=420
)

unified.render_plotly(fig_kinds, height=420)
```

### B. Top 12 loại mục tài liệu tham khảo BibTeX (`bibtex_entry_type_top12`)

Trong tổng số **975,674 mục trích dẫn BibTeX**, các bài báo khoa học chủ yếu trích dẫn các bài báo tạp chí (`article`), tài liệu arXiv/pre-print (`misc`), và kỷ yếu hội nghị (`inproceedings`):

```{code-cell} python
:tags: [remove-input]
import plotly.graph_objects as go
from book.lib import unified

m2 = unified.load_json("m2_unified_summary")
bib = m2["bibtex_entry_type_top12"]

fig_bib = go.Figure(go.Bar(
    x=list(bib.keys()),
    y=list(bib.values()),
    text=[f"{v:,}" for v in bib.values()],
    textposition="outside",
    marker_color="#3366CC"
))

fig_bib.update_layout(
    title="<b>Top 12 loại mục tài liệu tham khảo trong bảng bibtex (975,674 entries)</b>",
    xaxis_title="Loại mục trích dẫn (entry_type)",
    yaxis_title="Số lượng mục",
    yaxis=dict(range=[0, 630000]),
    template="plotly_white",
    height=400
)

unified.render_plotly(fig_bib, height=400)
```

### C. Cơ cấu nguồn trích dẫn tài liệu tham khảo (`bib_source_counts_total`)

Quá trình trích xuất BibTeX của nhóm xử lý song song cả hai nguồn: tệp `.bib` độc lập và các khối lệnh `\bibitem` nội suy trong tệp `.tex`:

```{code-cell} python
:tags: [remove-input]
import plotly.graph_objects as go
from book.lib import unified

m2 = unified.load_json("m2_unified_summary")
srcs = m2["bib_source_counts_total"]

labels_map = {
    "bib_file": "Tệp .bib độc lập",
    "bibitem": "\\bibitem nội tuyến trong .tex",
    "bbl_missing": "Thiếu .bbl (M1 lọc)",
    "none": "Không có tài liệu tham khảo",
    "both": "Kết hợp cả .bib và \\bibitem"
}

labels = [labels_map.get(k, k) for k in srcs.keys()]
values = list(srcs.values())

fig_pie = go.Figure(go.Pie(
    labels=labels,
    values=values,
    hole=0.45,
    textinfo="label+percent",
    marker=dict(colors=["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#9467bd"])
))

fig_pie.update_layout(
    title="<b>Cơ cấu nguồn trích xuất tài liệu tham khảo trên 25,000 bài báo</b>",
    template="plotly_white",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
)

unified.render_plotly(fig_pie, height=400)
```

---

## 4. Phân tích độ bao phủ và xử lý phiên bản rỗng

Đề bài đặt ra nguyên tắc thiết kế nghiêm ngặt: *"A version without TeX sources, kept as an empty record by Milestone 1, yields no parsed elements: record the version as empty rather than skipping it, so coverage statistics and the tables below reflect reality."*

Nhóm tuân thủ tuyệt đối nguyên tắc này:
1. **Độ bao phủ đạt 100%:** Toàn bộ **40,896 phiên bản khai báo** đều được theo dõi trong pipeline phân tích cú pháp.
2. **37,967 phiên bản có TeX hợp lệ (92.84%):** Được phân tích cây phân cấp hoàn chỉnh, tạo nút gốc `document` và các nhánh phần tử con.
3. **2,929 phiên bản rỗng (7.16%):** Bao gồm các bài PDF-only hoặc phiên bản không tải được mã nguồn ở M1. Pipeline khởi tạo `VersionHierarchy` với `nodes = []`. Các phiên bản này không tạo cạnh giả trong bảng `hierarchy`, bảo đảm dữ liệu phản ánh chính xác thực tế khoa học.

---

## 5. Hiệu quả tối ưu hóa của thuật toán khử trùng lặp

1. **Khử trùng lặp nội dung văn bản (`elements`):**
   - Thuật toán so khớp chính xác sau làm sạch (lọc bỏ các lệnh định dạng TeX và chuẩn hóa công thức toán học) giúp loại bỏ **5,125,033 phần tử trùng lặp**, tiết kiệm **31.59% dung lượng** (từ 16.22 triệu dòng thô xuống còn 11.10 triệu dòng độc bản).
   - Trong bảng `hierarchy`, các phiên bản cập nhật sau ($v_2, v_3, \dots$) chỉ cần trỏ `element_id` về phần tử đã tồn tại, giúp cấu trúc cơ sở dữ liệu quan hệ đạt độ nén tối đa.
2. **Hợp nhất trường BibTeX (`Field Unionization`):**
   - Thay vì ghi đè thô bạo, pipeline hợp nhất các trường thông tin (`title`, `authors`, `year`, `doi`, `journal`, `url`) giữa các phiên bản bài báo, đảm bảo độ đầy đủ thông tin cao nhất phục vụ huấn luyện mô hình ghép nối trích dẫn ở Milestone 3.

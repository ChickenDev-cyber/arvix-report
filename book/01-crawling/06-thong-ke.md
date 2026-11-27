---
kernelspec:
  name: python3
  display_name: Python 3
---

# 1.6 Thống kê

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Huỳnh Nhi (`TrinhNhi3011`)

Tiểu mục này trình bày các chỉ số thống kê định lượng toàn diện của pipeline thu thập dữ liệu (Milestone 1). Toàn bộ dữ liệu được tổng hợp chuẩn hóa từ **100% kho ngữ liệu thực tế 25,000 bài báo** của 5 thành viên (được lưu trữ tại `data/unified/m1_final_corpus.json` và `data/unified/m1_batch_summary.json`), phản ánh độ bao phủ, cơ cấu phiên bản, mạng lưới trích dẫn và hiệu quả lọc mã nguồn TeX.

---

## 1. Bảng 5 chỉ số bắt buộc theo yêu cầu đề bài

Các chỉ số dưới đây được kết xuất tự động từ bộ dữ liệu chuẩn hóa của 5 thành viên (`huynh-nhi`, `man-nhi`, `hoang`, `trong`, `khang`), tuân thủ chặt chẽ đặc tả định dạng và phương pháp đo lường của đề tài:

| STT | Chỉ số bắt buộc theo đề | Giá trị tính toán toàn nhóm | Ghi chú & Phương pháp tính toán |
|:---:|:---|:---:|:---|
| **1** | **Số bài crawl thành công** | **24,732 / 25,000 bài** (Tỷ lệ: **98.93%**) | Số bài hoàn thành thu thập theo chuẩn `assignment.papers_complete` (bao gồm bài TeX hoàn chỉnh và các bài `pdf_only`/`unsupported` được ghi nhận đúng chuẩn arXiv) |
| **2** | **Kích thước trung bình mỗi bài (Trước lọc)** | **5.54 MB / version** (5,543,702 B)<br>Tích lũy bài: **~7.56 – 11.49 MB / bài** | Trung bình trọng số trên 37,963 mẫu phiên bản nguồn tải từ `export.arxiv.org`. Khi cộng dồn các phiên bản theo từng bài, dung lượng thô đạt ~7.56 – 11.49 MB/bài (*xem Mục 2*) |
| | **Kích thước trung bình mỗi bài (Sau lọc)** | **322.04 KB / version** (322,043 B)<br>Tích lũy bài: **~359 – 684 KB / bài** | Giảm **94.19%** dung lượng lưu trữ nhờ loại bỏ hình ảnh (`.png`, `.jpg`, `.pdf`, `.eps`) và file nhị phân, bảo toàn 100% mã nguồn `.tex` và `.bib` |
| **3** | **Số reference trung bình mỗi bài** | **18.67 refs / bài** (Toàn bộ 25,000 bài)<br>**22.36 refs / bài** (20,878 bài có trích dẫn) | Tổng cộng **466,763 trích dẫn arXiv** được thu thập từ Semantic Scholar Graph API. Tỷ lệ bài báo có ít nhất một trích dẫn arXiv đạt **83.51%** |
| **4** | **Tỷ lệ thành công crawl Reference Metadata** | **99.77%** (465,709 / 466,763 refs) | Tỷ lệ trích xuất thành công siêu dữ liệu (ngày nộp, tiêu đề, tác giả) qua arXiv API trên tổng số trích dẫn arXiv |
| **5** | **Phạm vi khảo sát (`scope`)** | **25,000 bài** (179,012 ID ứng viên) | 5 dải ID chuyên ngành Data Science / Machine Learning phân bổ đều cho 5 thành viên (5,000 bài/người từ tháng 09/2024 đến 07/2025) |

---

## 2. Phương pháp tính toán & Phân biệt các thước đo lưu trữ

Nhóm làm rõ phương pháp luận và sự khác biệt giữa hai góc nhìn đo lường dung lượng lưu trữ:

### A. Đo lường theo phiên bản (`per_version_bytes`) vs Cộng dồn theo bài (`per_paper_sum_bytes`)
1. **Góc nhìn từng phiên bản (`per_version_bytes` - schema 1.2):**
   Mỗi lần tải từ `export.arxiv.org` là một gói nén `.tar.gz` của một phiên bản cụ thể ($v_1, v_2, \dots$). Thước đo này tính trung bình trên các phiên bản TeX độc lập:
   $$\overline{\text{Size}}_{\text{version}} = \frac{1}{|\mathcal{V}|} \sum_{v \in \mathcal{V}} \text{extracted\_bytes}(v) = 5.54 \text{ MB} \xrightarrow{\text{filter}} 322.04 \text{ KB} \quad (-94.19\%)$$
2. **Góc nhìn tích lũy mỗi bài (`per_paper_sum_bytes` - assignment):**
   Một bài báo khoa học trên arXiv thường trải qua nhiều lần sửa đổi. Tổng chi phí lưu trữ của một bài là tổng dung lượng của toàn bộ các phiên bản thuộc bài báo đó:
   $$\text{RawBytes}(P_i) = \sum_{v \in \text{Versions}(P_i)} \text{extracted\_bytes}(v)$$
   Theo góc nhìn này, một bài báo có dung lượng trung bình trước lọc từ **7.56 MB** đến **11.49 MB**, và sau lọc chỉ còn **359 KB** đến **684 KB** (tỷ lệ giảm dung lượng từ **94.05%** đến **95.25%**).

### B. Lưu ý kỹ thuật về dữ liệu của thành viên Khang
> [!NOTE]
> Trong gói bàn giao `m3-delivery.zip` của Phúc Khang (`khang`), tiến trình kiểm tra phát hiện cờ `validation.valid = false` với thông báo *"Handoff is being updated; wait for a successful checkpoint"*. Do đó, tệp `assignment-statistics-schema12.json` vắng mặt, dẫn tới chỉ số `schema12` và `per_version_bytes` trong `m1_batch_summary.json` của Khang mang giá trị `null`. Tuy nhiên, các chỉ số tích lũy `assignment` và `per_paper_sum_bytes` vẫn được ghi nhận đầy đủ, minh bạch và nhất quán (xem bảng chi tiết Mục 4).

---

## 3. Trực quan hóa dữ liệu tương tác (Plotly)

### A. Phân bố số lượng phiên bản của 25,000 bài báo

Trong tổng số 25,000 bài báo, nhóm ghi nhận tổng cộng **40,896 phiên bản khai báo** (trung bình **1.6358 phiên bản/bài**):
- **14,341 bài báo** (tỷ lệ **57.36%**) chỉ có 1 phiên bản duy nhất ($v_1$).
- **10,659 bài báo** (tỷ lệ **42.64%**) là bài đa phiên bản (từ $v_2$ đến $v_{13}$).
- **4,284 bài báo** (tỷ lệ **17.14%**) đã được công bố tại các hội nghị / tạp chí (`venue_rate`).

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

fc = unified.load_json("m1_final_corpus")
v_dist = fc["version_count_distribution"]

labels = [f"v{k}" for k in range(1, 11)] + ["v11+"]
counts = [v_dist.get(str(k), 0) for k in range(1, 11)]
v11_plus = sum(v for k, v in v_dist.items() if int(k) > 10)
counts.append(v11_plus)

fig_versions = go.Figure(data=[
    go.Bar(
        x=labels,
        y=counts,
        text=[f"{c:,}<br>({c/25000:.1%})" for c in counts],
        textposition="outside",
        marker=dict(
            color=counts,
            colorscale="Blues",
            showscale=False
        )
    )
])

fig_versions.update_layout(
    title="<b>Phân bố số lượng phiên bản trên 25,000 bài báo (Milestone 1)</b>",
    xaxis_title="Số lượng phiên bản",
    yaxis_title="Số lượng bài báo",
    template="plotly_white",
    height=400,
    yaxis=dict(range=[0, 16500])
)

unified.render_plotly(fig_versions, height=400)
```

### B. Hiệu quả lọc mã nguồn TeX theo từng thành viên

Việc loại bỏ các tệp hình ảnh và nhị phân giúp tiết kiệm băng thông và dung lượng lưu trữ trên Google Drive/Colab mà không làm mất thông tin cấu trúc cho Milestone 2. Biểu đồ dưới đây đối chiếu dung lượng trung bình trước và sau lọc trên từng phân dải:

```{code-cell} python
:tags: [remove-input]
import plotly.graph_objects as go
from book.lib import unified

fc = unified.load_json("m1_final_corpus")
owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
display_names = ["Huỳnh Nhi", "Mẫn Nhi", "Hoàng", "Minh Trọng", "Phúc Khang"]

before_mb = []
after_mb = []
reductions = []

for o in owners:
    snap = fc["by_owner"][o]["colab_statistics_snapshot"]
    b = snap["mean_extracted_bytes_before_filter"] / (1024 * 1024)
    a = snap["mean_retained_source_bytes"] / (1024 * 1024)
    r = snap["source_filter_reduction_rate"] * 100
    before_mb.append(round(b, 2))
    after_mb.append(round(a, 2))
    reductions.append(round(r, 2))

wt = fc["colab_source_filter_summary"]
display_names.append("Toàn nhóm (TB trọng số)")
before_mb.append(round(wt["weighted_mean_before_filter_bytes"] / (1024 * 1024), 2))
after_mb.append(round(wt["weighted_mean_retained_bytes"] / (1024 * 1024), 2))
reductions.append(round(wt["weighted_reduction_rate"] * 100, 2))

fig_filter = go.Figure(data=[
    go.Bar(
        name="Trước lọc (Thô)",
        x=display_names,
        y=before_mb,
        text=[f"{v} MB" for v in before_mb],
        textposition="auto",
        marker_color="#ef553b"
    ),
    go.Bar(
        name="Sau lọc (TeX/BibTeX)",
        x=display_names,
        y=after_mb,
        text=[f"{v} MB" for v in after_mb],
        textposition="auto",
        marker_color="#00cc96"
    )
])

fig_filter.update_layout(
    barmode="group",
    title="<b>Dung lượng trung bình mỗi phiên bản trước và sau lọc nguồn TeX (MB)</b>",
    xaxis_title="Thành viên phụ trách (Owner)",
    yaxis_title="Dung lượng trung bình (MB)",
    template="plotly_white",
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

unified.render_plotly(fig_filter, height=420)
```

---

## 4. Bảng thống kê chi tiết theo 5 phân dải thành viên

Bảng đối chiếu toàn diện 5 phân dải thu thập (5,000 bài báo/người) tổng hợp từ `m1_final_corpus.json` và `m1_batch_summary.json`:

| Thành viên | Dải arXiv ID | Số bài hoàn thành | Phiên bản khai báo | Có Venue | arXiv Refs | Tỷ lệ Ref Complete | TB trước lọc (Per-version) | TB sau lọc (Per-version) | TB trước lọc (Per-paper) | TB sau lọc (Per-paper) | Tỷ lệ giảm |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Huỳnh Nhi** (`huynh-nhi`) | `2409.03594 – 2409.08593` | 4,960 (99.20%) | 8,268 | 960 (19.20%) | 91,161 | 99.86% | 5.29 MB | 296 KB | 9.08 MB | 508 KB | **94.41%** |
| **Mẫn Nhi** (`man-nhi`) | `2501.12642 – 2501.17641` | 4,954 (99.08%) | 8,251 | 918 (18.36%) | 78,635 | 100.00% | 4.99 MB | 327 KB | 8.60 MB | 563 KB | **93.45%** |
| **Hoàng** (`hoang`) | `2503.06914 – 2503.11913` | 4,958 (99.16%) | 8,384 | 820 (16.40%) | 108,616 | 99.21% | 6.47 MB | 389 KB | 11.49 MB | 684 KB | **94.05%** |
| **Minh Trọng** (`trong`) | `2504.17523 – 2505.00665` | 4,922 (98.44%) | 8,060 | 838 (16.76%) | 91,814 | 99.98% | 4.88 MB | 277 KB | 8.35 MB | 473 KB | **94.33%** |
| **Phúc Khang** (`khang`) | `2506.20788 – 2507.01658` | 4,938 (98.76%) | 7,933 | 748 (14.96%) | 96,537 | 100.00% | *null\** | *null\** | 7.56 MB | 359 KB | **95.25%** |
| **TOÀN NHÓM** | **25,000 bài** | **24,732 (98.93%)** | **40,896** | **4,284 (17.14%)** | **466,763** | **99.77%** | **5.54 MB** | **322 KB** | **9.02 MB** | **517 KB** | **94.19%** |

*\* Ghi chú: Dải của Khang không có số liệu `per_version_bytes` trong schema 1.2 do cờ validation checkpoint; số liệu per-paper sum được tính toán trực tiếp từ `assignment.source_sizes`.*

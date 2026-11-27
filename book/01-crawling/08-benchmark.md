---
kernelspec:
  name: python3
  display_name: Python 3
---

# 1.8 Benchmark (Colab CPU)

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Mẫn Nhi (`@NhiNgo49`)

Tiểu mục này trình bày kết quả đo lường hiệu năng, thời gian thực thi (wall time) và mức tiêu thụ tài nguyên phần cứng (CPU, RAM, Disk) của pipeline thu thập dữ liệu (Milestone 1) trên môi trường chuẩn **Google Colab (chỉ sử dụng CPU)** theo quy định của đề tài.

Nội dung trọng tâm đối chiếu trực tiếp giữa **Mốc cơ sở 06/11 (`m1_baseline_nov06.json`)** và **Đợt tối ưu hóa S2-Batch (`m1_batch_summary.json`)**, định lượng mức tăng tốc thực tế khi chuyển dịch sang cơ chế truy vấn batch đa luồng.

---

## 1. Môi trường và phương pháp đo lường quy chuẩn

Nhằm đảm bảo tính tái lập và công bằng, toàn bộ các phép đo benchmark được thực hiện trực tiếp trên máy ảo tiêu chuẩn Google Colab (CPU runtime) không sử dụng GPU/TPU:

| Tiêu chí | Cấu hình máy ảo Google Colab tiêu chuẩn |
|:---|:---|
| **Hệ điều hành** | Linux kernel 6.6.159+ (Ubuntu 22.04 LTS x86_64) |
| **Vi xử lý (CPU)** | Intel(R) Xeon(R) CPU @ 2.20GHz — **2 vCPU** |
| **Dung lượng RAM hệ thống** | **12.67 GB** (13,605,818,368 bytes) |
| **Môi trường thực thi** | CPython 3.13.18 (Kiến trúc x86_64) |
| **Phương pháp giám sát RAM** | Giám sát RSS toàn bộ cây tiến trình con qua `psutil.Process.memory_info().rss` |
| **Chế độ bộ nhớ đệm (`cache_mode`)** | `mixed` (Quản lý trạng thái bằng SQLite và checkpoint resume qua các phiên chạy Colab) |
| **Nguyên tắc đo Wall Time** | Tính tổng thời gian runner của từng thành viên độc lập, tuyệt đối không cộng dồn thời gian giữa các máy ảo khác nhau |

---

## 2. So sánh hiệu năng: Mốc cơ sở 06/11 vs Đợt tối ưu S2-Batch

Trong giai đoạn đầu (mốc 06/11), việc crawl trích dẫn qua Semantic Scholar Graph API thực hiện theo từng bài riêng lẻ (GET request) dẫn tới tình trạng bị nghẽn và giới hạn tần suất (Rate Limit 429), kéo dài thời gian chạy lên tới **26.02h – 35.48h** qua 167 phiên chạy dở dang.

Ở đợt chạy **S2-Batch**, nhóm tái kiến trúc công đoạn thu thập:
1. Gom cụm các truy vấn Semantic Scholar thành các mẻ POST batch (tối đa 500 bài/lô).
2. Tối ưu hóa truy vấn ngày nộp qua arXiv API theo lô 100 ID.
3. Đồng bộ hóa bộ đệm lưu trữ cục bộ để giảm thiểu I/O lặp lại.

Kết quả thời gian chạy thực tế giảm xuống còn **16.57h – 22.77h**, đạt mức tiết kiệm thời gian từ **31.69% đến 47.72%** (tốc độ xử lý tăng từ **1.46x đến 1.91x**), đồng thời hoàn thành **24,732 / 25,000 bài** (tỷ lệ thành công **98.93%**).

### A. Bảng đối chiếu chi tiết hiệu năng giữa 2 giai đoạn

| Thành viên (Owner) | Phiên chạy (06/11 $\to$ Batch) | Wall Time 06/11 (h) | Wall Time S2-Batch (h) | Tỷ lệ giảm thời gian | Hệ số tăng tốc (Speedup) | Số request HTTP Audit (Batch) | Số bài hoàn thành (Batch) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Huỳnh Nhi** (`huynh-nhi`) | 35 $\to$ 26 phiên | 35.48 h | **18.55 h** | **-47.72%** | **1.91x** | 14,470 calls | 4,960 (99.20%) |
| **Mẫn Nhi** (`man-nhi`) | 39 $\to$ 35 phiên | 34.09 h | **20.71 h** | **-39.24%** | **1.65x** | 14,950 calls | 4,954 (99.08%) |
| **Hoàng** (`hoang`) | 37 $\to$ 51 phiên | 33.33 h | **22.77 h** | **-31.69%** | **1.46x** | 14,875 calls | 4,958 (99.16%) |
| **Minh Trọng** (`trong`) | 29 $\to$ 11 phiên | 29.09 h | **16.69 h** | **-42.62%** | **1.74x** | 14,919 calls | 4,922 (98.44%) |
| **Phúc Khang** (`khang`) | 27 $\to$ 13 phiên | 26.02 h | **16.57 h** | **-36.31%** | **1.57x** | 15,109 calls | 4,938 (98.76%) |
| **TOÀN NHÓM** | **167 $\to$ 136 phiên** | **26.02h – 35.48h** | **16.57h – 22.77h** | **-31.69% đến -47.72%** | **1.46x – 1.91x** | **74,323 calls** | **24,732 (98.93%)** |

*(Ghi chú: Số liệu HTTP Audit phản ánh toàn bộ các cuộc gọi mạng được ghi nhận trong `http_audit_counts`, bao gồm cả mã 200, 429 và retry có kiểm soát).*

---

## 3. Trực quan hóa so sánh thời gian thực thi (Plotly)

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

b6 = unified.load_json("m1_baseline_nov06")
bs = unified.load_json("m1_batch_summary")

owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
names = ["Huỳnh Nhi", "Mẫn Nhi", "Hoàng", "Minh Trọng", "Phúc Khang"]

nov06_hours = []
batch_hours = []
speedups = []
reductions = []

for o in owners:
    b = b6["by_owner"][o]
    vs = b["vs_s2_batch"]
    nov06_hours.append(round(b["runner_wall_sum_hours"], 2))
    batch_hours.append(round(vs["batch_active_wall_hours"], 2))
    speedups.append(round(vs["speedup_factor"], 2))
    reductions.append(round(vs["wall_time_reduction_pct"], 1))

fig_bench = go.Figure(data=[
    go.Bar(
        name="Baseline 06/11 (Cũ)",
        x=names,
        y=nov06_hours,
        text=[f"{h}h" for h in nov06_hours],
        textposition="auto",
        marker_color="#636EFA"
    ),
    go.Bar(
        name="S2-Batch (Mới)",
        x=names,
        y=batch_hours,
        text=[f"{h}h<br>(-{r}%)" for h, r in zip(batch_hours, reductions)],
        textposition="auto",
        marker_color="#00CC96"
    )
])

fig_bench.update_layout(
    barmode="group",
    title="<b>Đối chiếu thời gian thực thi (Wall Hours) giữa Mốc 06/11 và Đợt S2-Batch</b>",
    xaxis_title="Thành viên phụ trách (Owner)",
    yaxis_title="Thời gian thực thi liên tục (Giờ)",
    template="plotly_white",
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

unified.render_plotly(fig_bench, height=420)
```

---

## 4. Phân tích tài nguyên phần cứng (CPU, RAM, Disk)

Bên cạnh thời gian thực thi, mức tiêu thụ tài nguyên bộ nhớ và đĩa cứng được duy trì ở mức tối ưu xuyên suốt các phiên chạy:

1. **Bộ nhớ RAM (`RSS`):**
   - **RAM đỉnh (`peak_ram_max_mib`):** Dao động từ **255.13 MiB** đến **1,077.38 MiB** tùy thuộc vào số lượng luồng nén và kích thước gói tar.gz lớn nhất của từng bài. Mức đỉnh này chỉ chiếm tối đa **8.5%** tổng dung lượng 12.67 GB của Colab, hoàn toàn loại trừ nguy cơ tràn bộ nhớ (Out-Of-Memory).
   - **RAM trung bình theo thời gian (`mean_ram_wall_weighted_mib`):** Dao động ổn định từ **111.74 MiB** đến **151.16 MiB**, khẳng định pipeline không bị rò rỉ bộ nhớ (memory leak) qua hàng chục giờ thực thi liên tục.
2. **Không gian lưu trữ đĩa cứng (`Disk Space`):**
   - **Dung lượng kết quả (`final_output_gib`):** Mỗi phân dải 5,000 bài sản sinh từ **1.34 GiB** đến **3.11 GiB** dữ liệu sạch (bao gồm tệp nguồn `.tex`/`.bib` đã lọc hình ảnh và tệp siêu dữ liệu SQLite/JSONL).
   - **Dung lượng đĩa đỉnh (`peak_disk_max_gib`):** Tối đa đạt **3.20 GiB**, hoàn toàn phù hợp với hạn ngạch 107.7 GB SSD của Colab.
3. **Quản lý giới hạn tần suất API (Rate Limit & HTTP Audit):**
   - Tổng cộng **74,323 cuộc gọi HTTP** được kiểm toán toàn nhóm. Tỷ lệ phản hồi HTTP 429 được xử lý triệt để nhờ thuật toán Exponential Backoff kết hợp Jitter, đảm bảo pipeline vận hành bền bỉ mà không bị máy chủ arXiv chặn IP.

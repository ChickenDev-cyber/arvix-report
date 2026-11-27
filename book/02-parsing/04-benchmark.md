---
kernelspec:
  name: python3
  display_name: Python 3
---

# 2.4 Đo lường Hiệu năng (Performance Benchmarking)

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Minh Trọng (`@ChickenDev-cyber`), Phúc Khang (`@khang1108`)

Tiểu mục này trình bày kết quả đo lường hiệu năng thực tế của pipeline phân tích cú pháp (Milestone 2) trên môi trường chuẩn **Google Colab (chỉ sử dụng CPU)** theo quy định của đề tài.

Nội dung bao gồm:
1. **Kết quả vận hành sản xuất thực tế** trên 25,000 bài báo của 5 thành viên sử dụng bộ tách câu dựa trên luật (`backend: "rule"`), ghi nhận trực tiếp từ `m2_unified_summary.json`.
2. **Nghiên cứu đối chiếu 4 bộ tách câu** (`rule`, `punkt`, `spacy`, `sat`) trên tập chẩn đoán và dải 100 bài từ `m2_tokenizer_benchmark.json`, luận giải căn cứ khoa học đằng sau quyết định lựa chọn kiến trúc sản xuất.

---

## 1. Môi trường Thử nghiệm Quy chuẩn (Colab CPU Testbed)

Toàn bộ các phép đo benchmark của Milestone 2 được thực thi trực tiếp trên máy ảo Google Colab tiêu chuẩn chạy ở chế độ CPU thuần:

| Tiêu chí | Cấu hình máy ảo Google Colab tiêu chuẩn |
|:---|:---|
| **Bộ vi xử lý (CPU)** | Intel(R) Xeon(R) CPU @ 2.20GHz — **2 vCPU** |
| **Dung lượng RAM hệ thống** | **12.67 GB** (13,605,818,368 bytes) |
| **Hệ điều hành & Môi trường** | Linux kernel 6.6.159+ (Ubuntu 22.04 LTS x86_64), CPython 3.13.18 |
| **Các thư viện chính** | `pyarrow==23.0.1`, `psutil==5.9.5`, `spacy==3.8.18`, `wtpsplit==2.2.2` |
| **Phương pháp giám sát RAM** | Giám sát RSS thực tế qua `psutil.Process.memory_info().rss` |
| **Cơ chế nạp & giải phóng** | Streaming theo từng bài báo (`per-publication streaming`), giải phóng bộ nhớ ngay sau khi dựng cây |

---

## 2. Kết quả Đo lường Thực tế Toàn Nhóm trên 25,000 Bài báo (`backend: "rule"`)

Trong quá trình triển khai sản xuất, toàn bộ 5 thành viên đã chạy đồng nhất bộ tách câu **`rule`** trên 5 phân dải 5,000 bài độc lập. Kết quả đo lường thực tế từ `m2_unified_summary.json["benchmark_summary"]` được tổng hợp dưới đây:

| STT | Chỉ số Đo lường theo Đề bài | Kết quả Thực nghiệm trên Colab CPU | Đánh giá Kỹ thuật |
|:---:|:---|:---:|:---|
| **I** | **THỜI GIAN THỰC THI (WALL TIME)** | | |
| **1** | **Thời gian chạy mỗi phân dải 5,000 bài** | **1.06h – 1.72h** (3,807.28s – 6,203.72s) | Hoàn thành trọn vẹn 5,000 bài/người trong một phiên chạy duy nhất |
| **2** | **Thời gian trung bình xử lý mỗi bài báo** | **0.76s – 1.24s / bài** | Bao gồm: Đọc TeX $\to$ Giải quyết luồng $\to$ Tách câu $\to$ Dựng cây $\to$ Khử trùng lặp $\to$ Ghi Parquet |
| **3** | **Thời gian trung bình mỗi phiên bản TeX** | **~460 – 780 ms / version** | Đo trên 37,967 phiên bản có nguồn TeX hợp lệ |
| **II** | **MỨC TIÊU THỤ BỘ NHỚ (RAM FOOTPRINT)** | | |
| **4** | **Bộ nhớ RAM đỉnh điểm (`peak_rss_mib`)** | **674.16 – 701.77 MiB** | Chiếm chưa đầy **5.5%** tổng RAM của Colab (12.67 GB), tuyệt đối không OOM |
| **5** | **Bộ nhớ RAM trung bình (`mean_rss_mib`)** | **130.04 – 200.72 MiB** | Mức tiêu thụ ổn định, chứng minh cơ chế streaming giải phóng bộ nhớ hoàn hảo |
| **III**| **DUNG LƯỢNG LƯU TRỮ PARQUET M2** | | |
| **6** | **Tổng kích thước 3 bảng Parquet M2** | **1,117.27 MiB** (1.091 GiB) | Nén Snappy (`elements`: 782.18 MiB, `hierarchy`: 196.44 MiB, `bibtex`: 138.65 MiB) |
| **7** | **Dung lượng trung bình mỗi phân dải** | **217.22 – 227.95 MiB / owner** | Phân bổ đồng đều và tối ưu giữa 5 thành viên |

### Bảng chi tiết hiệu năng theo 5 thành viên:

| Thành viên (Owner) | Số bài xử lý | Thời gian thực thi (Wall Time) | Tốc độ trung bình (s/bài) | RAM Đỉnh (Peak RSS) | RAM Trung bình (Mean RSS) | Trạng thái / Exit Code |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Huỳnh Nhi** (`huynh-nhi`) | 5,000 bài | **1.06 h** (3,807.28 s) | 0.76 s / bài | 693.34 MiB | 161.22 MiB | Complete (Exit 0) |
| **Mẫn Nhi** (`man-nhi`) | 5,000 bài | **1.63 h** (5,863.15 s) | 1.17 s / bài | 674.16 MiB | 157.37 MiB | Complete (Exit 0) |
| **Hoàng** (`hoang`) | 5,000 bài | **1.72 h** (6,203.72 s) | 1.24 s / bài | 701.77 MiB | 200.72 MiB | Complete (Exit 0) |
| **Minh Trọng** (`trong`) | 5,000 bài | **1.67 h** (6,027.53 s) | 1.21 s / bài | 676.53 MiB | 165.11 MiB | Complete (Exit 0) |
| **Phúc Khang** (`khang`) | 5,000 bài | **1.50 h** (5,416.48 s) | 1.08 s / bài | 689.44 MiB | 130.04 MiB | Complete (Exit 0) |
| **TOÀN NHÓM** | **25,000 bài** | **1.06h – 1.72h / dải** | **1.09 s / bài (TB)** | **674.16 – 701.77 MiB** | **130.04 – 200.72 MiB** | **100% Thành công** |

---

## 3. Trực quan hóa Thời gian Thực thi (Plotly)

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

owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
names = ["Huỳnh Nhi", "Mẫn Nhi", "Hoàng", "Minh Trọng", "Phúc Khang"]
wall_h = [round(m2["by_owner"][o]["benchmark"]["wall_hours"], 2) for o in owners]
speed_s = [round(m2["by_owner"][o]["benchmark"]["mean_seconds_per_processed_publication"], 2) for o in owners]

fig_m2_bench = go.Figure(data=[
    go.Bar(
        x=names,
        y=wall_h,
        text=[f"{h}h ({s}s/bài)" for h, s in zip(wall_h, speed_s)],
        textposition="outside",
        marker_color="#1f77b4"
    )
])

fig_m2_bench.update_layout(
    title="<b>Thời gian chạy thực tế Milestone 2 trên Colab 2 vCPU theo từng phân dải (backend: rule)</b>",
    xaxis_title="Thành viên phụ trách (Owner)",
    yaxis_title="Thời gian thực thi liên tục (Giờ)",
    yaxis=dict(range=[0, 2.2]),
    template="plotly_white",
    height=400
)

unified.render_plotly(fig_m2_bench, height=400)
```

---

## 4. Nghiên cứu Đối chiếu 4 Bộ tách câu (Tokenizer Benchmark)

Trước khi tiến hành phân tích cú pháp trên toàn bộ 25,000 bài báo, nhóm đã thực hiện nghiên cứu so sánh chuyên sâu giữa 4 bộ tách câu:
1. **`rule` (Rule baseline):** Thuật toán regex kết hợp từ điển chuyên ngành do nhóm tự phát triển, bảo toàn vùng toán và trích dẫn.
2. **`punkt` (NLTK Punkt):** Mô hình unsupervised sentence boundary detection kinh điển của NLTK (`punkt_tab English`).
3. **`spacy` (spaCy senter):** Mô hình học sâu dựa trên parser/senter của spaCy (`en_core_web_sm 3.8.0`).
4. **`sat` (Segment Any Text):** Mô hình phân đoạn câu tiên tiến dựa trên mạng nơ-ron thu nhỏ (`wtpsplit 2.2.2`, `sat-3l-sm ONNX CPU`).

### A. Đánh giá trên Tập chẩn đoán TeX 11 bài (`diagnostic_11_papers`)

Tập chẩn đoán bao gồm 1,574 khối văn bản văn xuôi chứa các trường hợp khó đặc thù của văn bản khoa học: công thức toán inline `$x_i$`, viết tắt chuyên ngành (*et al.*, *vs.*, *e.g.*, *i.e.*), dấu ba chấm, và các cụm ngoặc trích dẫn.

```{code-cell} python
:tags: [remove-input]
import plotly.graph_objects as go
from book.lib import unified

tb = unified.load_json("m2_tokenizer_benchmark")
methods = tb["diagnostic_11_papers"]["methods"]

m_names = [m["label"] for m in methods]
contracts = [m["contract_passed"] / m["contract_total"] * 100 for m in methods]
diag = [m["diagnostic_passed"] / m["diagnostic_total"] * 100 for m in methods]

fig_diag = go.Figure(data=[
    go.Bar(
        name="Tuân thủ hợp đồng bảo toàn (40 tiêu chí)",
        x=m_names,
        y=contracts,
        text=[f"{v:.1f}%" for v in contracts],
        textposition="auto",
        marker_color="#2ca02c"
    ),
    go.Bar(
        name="Đạt ca chẩn đoán khó (12 ca)",
        x=m_names,
        y=diag,
        text=[f"{v:.1f}%" for v in diag],
        textposition="auto",
        marker_color="#ff7f0e"
    )
])

fig_diag.update_layout(
    barmode="group",
    title="<b>Đánh giá chất lượng 4 bộ tách câu trên tập chẩn đoán TeX (Diagnostic Benchmark)</b>",
    xaxis_title="Bộ tách câu (Tokenizer)",
    yaxis_title="Tỷ lệ hoàn thành (%)",
    yaxis=dict(range=[0, 115]),
    template="plotly_white",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

unified.render_plotly(fig_diag, height=400)
```

| Phương pháp | Cấu hình kỹ thuật | Ca chẩn đoán đạt (12 ca) | Tuân thủ hợp đồng bảo toàn (40 tiêu chí) | Số câu trích xuất | Thời gian chạy (giây) |
|:---|:---|:---:|:---:|:---:|:---:|
| **`rule` (Nhóm chọn)** | **Python + regex/vocab** | 7 / 12 | **40 / 40 (100.0%)** | 5,635 câu | **0.54s – 0.80s** |
| **`punkt`** | NLTK 3.10.4 (punkt_tab) | 8 / 12 | 38 / 40 (95.0%) | 5,630 câu | 0.79 s |
| **`spacy`** | spaCy 3.8.18 (senter) | **10 / 12** | 35 / 40 (87.5%) | 5,608 câu | 3.37 s |
| **`sat`** | wtpsplit 2.2.2 (sat-3l-sm ONNX) | 9 / 12 | 27 / 40 (67.5%) | 5,466 câu | 222.13 s |

### B. Đo lường mở rộng trên 100 bài báo (`range_benchmark_100_papers`)

Khi mở rộng quy mô kiểm thử trên 100 bài báo khoa học thực tế (93 bài có TeX hợp lệ, 7,525 khối văn bản, 31,607 câu trích xuất):

| Bộ tách câu | Cấu hình mẻ (Batch) | Thời gian chạy (93 bài) | Tốc độ xử lý (s/ver) | RAM Đỉnh (Peak RSS) | Ước tính chạy 40,000 phiên bản TeX |
|:---|:---:|:---:|:---:|:---:|:---:|
| **`spacy`** | Outer batch = 1 | 17.28 s | 0.186 s/ver | 151.54 MiB | ~2.06 giờ |
| **`spacy`** | Outer batch = 32 | 9.70 s | 0.104 s/ver | 163.59 MiB | ~1.16 giờ |
| **`sat`** | Outer batch = 1, Inner = 1 | 1,283.91 s (~21.4 phút) | 13.805 s/ver | 1,310.14 MiB | **~153.33 giờ** (~6.4 ngày liên tục) |

---

## 5. Luận giải Khoa học: Vì sao nhóm chốt `rule` cho Sản xuất 25,000 bài?

Dựa trên kết quả thực nghiệm toàn diện, nhóm đã đưa ra quyết định kỹ thuật chốt kiến trúc **`rule`** cho toàn bộ 25,000 bài báo vì 4 lý do then chốt:

1. **Tuyệt đối tuân thủ hợp đồng bảo toàn ranh giới câu (100% Contract Compliance):**
   - Bộ `rule` đạt **40/40 tiêu chí kiểm định**, không bao giờ ngắt câu bên trong công thức toán inline `$x_i \dots y_i$`, khối công thức toán `\begin{equation}`, hoặc bên trong các cặp ngoặc trích dẫn `\cite{...}`.
   - Ngược lại, các mô hình nơ-ron như `sat` chỉ đạt 27/40 do cơ chế phân đoạn xác suất thường xuyên cắt ngang các biểu thức toán phức tạp khi gặp dấu chấm thập phân hoặc dấu phẩy trong công thức.
2. **Tốc độ thực thi vượt trội và khả thi trên Colab CPU:**
   - Bộ `rule` chỉ mất trung bình **~1.09 giây cho mỗi bài báo đầy đủ**, cho phép hoàn thành 5,000 bài trong vòng 1.06h – 1.72h.
   - Trong khi đó, mô hình học sâu `sat` cần tới **153.3 giờ** (~6.4 ngày chạy liên tục trên CPU) để xử lý toàn bộ kho ngữ liệu, hoàn toàn bất khả thi trong hạn mức thời gian và session của Google Colab.
3. **An toàn bộ nhớ và không phụ thuộc thư viện nặng:**
   - Bộ `rule` được cài đặt thuần Python và regex đã biên dịch, không đòi hỏi nạp trọng số nơ-ron ONNX hay PyTorch, giữ RAM đỉnh ổn định ở mức **~674 – 702 MiB**.
   - Điều này triệt tiêu hoàn toàn nguy cơ rò rỉ bộ nhớ hoặc xung đột phiên bản nhị phân C-extension giữa các máy ảo Colab.

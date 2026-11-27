---
kernelspec:
  name: python3
  display_name: Python 3
---

# 3.5 Đánh giá MRR@5 & Kiểm định Toàn vẹn

> **Người phụ trách:** Huy Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Phúc Khang (`@khang1108`)

Tiểu mục này trình bày phương pháp luận đánh giá mô hình ghép nối trích dẫn (Milestone 3) thông qua chỉ số **Mean Reciprocal Rank tại ngưỡng cắt 5 (MRR@5)**, đối chiếu hiệu năng giữa mô hình cơ sở (Baseline) và mô hình hồi quy Logistic chọn lọc (`LogisticRegression C=0.1`), phân tích chi phí tiêu thụ tài nguyên CPU/RAM, và công bố kết quả kiểm định toàn vẹn dữ liệu tự động (`validate_dataset`).

Toàn bộ kết quả thực nghiệm và số liệu kiểm định được nạp tự động từ tệp chuẩn hóa `data/unified/m3_unified_summary.json`.

---

## 1. Định nghĩa và Phương pháp Luận Đánh giá MRR@5

### A. Công thức tính toán MRR@5

Xếp hạng trích dẫn là bài toán tìm kiếm tài liệu tham khảo đúng $y^* \in \mathcal{E}_p$ cho từng mục BibTeX $q = (p, k) \in \mathcal{B}_p$ trong danh sách top 5 ứng viên được đề xuất $[\hat{c}_1, \hat{c}_2, \hat{c}_3, \hat{c}_4, \hat{c}_5]$.

Chỉ số **Reciprocal Rank (RR)** của một truy vấn $q$ được định nghĩa:
$$\text{RR}(q) = \begin{cases} \frac{1}{\text{rank}(q)}, & 1 \le \text{rank}(q) \le 5 \\ 0, & \text{rank}(q) > 5 \text{ or not found} \end{cases}$$
Trong đó $\text{rank}(q)$ là vị trí của bài báo đúng trong top 5 ứng viên được mô hình đề xuất. Nếu bài báo đúng xuất hiện ngoài top 5 hoặc không tìm thấy, $\text{RR}(q) = 0$.

Chỉ số **Mean Reciprocal Rank (MRR@5)** trên tập hợp truy vấn kiểm thử $Q$ là trung bình cộng của các giá trị RR:
$$\text{MRR@5} = \frac{1}{|Q|} \sum_{q \in Q} \text{RR}(q)$$

Bên cạnh đó, nhóm theo dõi tỷ lệ xuất hiện của kết quả đúng trong top $k$ (**Hits@k**):
$$\text{Hits@}k = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{rank}(q) \le k), \quad k \in \{1, 3, 5\}$$

### B. Miền đánh giá và Phân loại Trạng thái Nhãn

Bảng dự đoán `predictions` chứa tổng cộng **101,441 dòng** phân bổ trên 2,525 bài báo. Tuy nhiên, theo đúng chuẩn mực khoa học và đặc tả kỹ thuật của Milestone 3, chỉ số MRR@5 chỉ được tính toán trên các truy vấn có đích khớp thực tế:

1. **Truy vấn khớp đích (`matched` - $|Q| = 35,373$ truy vấn):**
   - Bao gồm **1,880 truy vấn gán nhãn thủ công** (manual audit) và **33,493 truy vấn gán nhãn tự động** đạt độ tin cậy cao qua hệ thống heuristic 3 tầng.
   - Đây là tập hợp duy nhất có nhãn ground truth (`groundtruth_arxiv_id != NULL`), đóng vai trò là tập $Q$ chính thức để tính toán MRR@5.
2. **Truy vấn không có đích khớp trong dải (`no_match`):**
   - Các mục BibTeX trích dẫn tài liệu ngoài kho ngữ liệu arXiv (sách giáo trình, bài báo hội thảo không đưa lên arXiv, hoặc bài thuộc dải năm/tháng khác). Trạng thái này được loại trừ khỏi mẫu đánh giá xếp hạng.
3. **Bản ghi chưa duyệt (`unreviewed`):**
   - Các cặp ứng viên thứ cấp không được gán nhãn dương, đóng vai trò mẫu âm hoặc dự phòng trong bảng xuất bản.

---

## 2. Bảng Đối chiếu Hiệu năng: Baseline vs Logistic Regression (C=0.1)

Mô hình cơ sở (**Baseline**) xếp hạng ứng viên thuần túy dựa trên độ tương đồng Cosine của vector TF-IDF tiêu đề kết hợp so khớp chuỗi tác giả thô. 

Mô hình được chọn (**`LogisticRegression` với $C=0.1$**) sử dụng 24 đặc trưng đa chiều (kết hợp tương đồng chuỗi RapidFuzz, khoảng cách năm xuất bản, độ tin cậy định danh arXiv, và điểm số cạnh tranh nội nhóm).

| Tập phân chia (Split) | Phân loại nhãn | Số lượng truy vấn ($|Q|$) | Baseline MRR@5 | Model (LR C=0.1) MRR@5 | Tăng trưởng ($\Delta$) | Baseline Hits@1 | Model Hits@1 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Validation** | Thủ công (Manual) | 435 | 0.974138 | **1.000000** | +0.025862 | 94.94% | **100.00%** |
| | Tự động (Automatic) | 76 | 1.000000 | **1.000000** | 0.000000 | 100.00% | **100.00%** |
| | **Validation Chung** | **511** | **0.977984** | **1.000000** | **+0.022016** | **95.69%** | **100.00%** |
| **Test** | Thủ công (Manual) | 431 | 0.997680 | **1.000000** | +0.002320 | 99.54% | **100.00%** |
| | Tự động (Automatic) | 97 | 1.000000 | **1.000000** | 0.000000 | 100.00% | **100.00%** |
| | **Test Chung** | **528** | **0.998106** | **1.000000** | **+0.001894** | **99.62%** | **100.00%** |
| **Train** | Thủ công (Manual) | 1,014 | 0.983399 | **1.000000** | +0.016601 | 96.75% | **100.00%** |
| | Tự động (Automatic) | 33,320 | 0.984715 | **0.999895** | +0.015180 | 97.46% | **99.98%** |
| | **Train Chung** | **34,334** | **0.984677** | **0.999898** | **+0.015221** | **97.43%** | **99.98%** |
| **TOÀN CỤC** | **Manual (100% người duyệt)** | **1,880** | **0.984530** | **1.000000** | **+0.015470** | **96.97%** | **100.00%** |
| | **Automatic** | **33,493** | **0.984794** | **0.999896** | **+0.015102** | **97.47%** | **99.98%** |
| | **TỔNG HỢP TOÀN BỘ** | **35,373** | **0.984780** | **0.999901** | **+0.015121** | **97.44%** | **99.98%** |

### Nhận xét kết quả:
1. **Hoàn hảo trên tập nhãn người duyệt (Manual Ground Truth):**
   Trên toàn bộ **1,880 truy vấn được 5 thành viên gán nhãn thủ công**, mô hình Logistic Regression đạt **MRR@5 = 1.000000** và **Hits@1 = 100.00%** (1,880/1,880 truy vấn xếp bài báo đúng ở vị trí số 1 ngay lần dự đoán đầu tiên), khắc phục hoàn toàn 57 lỗi xếp hạng sai vị trí của Baseline.
2. **Hiệu năng vượt trội trên quy mô lớn:**
   Trên toàn bộ 35,373 truy vấn, mô hình đưa MRR@5 từ 0.9848 lên **0.999901**. Baseline để sót **905 truy vấn lỗi** (xếp sai vị trí hoặc nằm ngoài top 5), trong khi mô hình Logistic Regression chỉ còn **duy nhất 6 trường hợp bất đồng** (trong đó có tới 3 trường hợp thực chất là heuristic tự động gán nhầm và mô hình đã dự đoán đúng mục tiêu thực tế).

---

## 3. Trực quan hóa So sánh MRR@5 (Plotly)

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m3 = unified.load_json("m3_unified_summary")
mb = m3["metrics_baseline"]["metrics"]
mm = m3["metrics_model"]["metrics"]

categories = [
    "Validation (Manual)",
    "Validation (Chung)",
    "Test (Manual)",
    "Test (Chung)",
    "Toàn cục (35,373 queries)"
]

base_mrr = [
    mb["valid"]["manual"]["mrr_at_5"],
    mb["valid"]["overall"]["mrr_at_5"],
    mb["test"]["manual"]["mrr_at_5"],
    mb["test"]["overall"]["mrr_at_5"],
    mb["overall"]["overall"]["mrr_at_5"]
]

model_mrr = [
    mm["valid"]["manual"]["mrr_at_5"],
    mm["valid"]["overall"]["mrr_at_5"],
    mm["test"]["manual"]["mrr_at_5"],
    mm["test"]["overall"]["mrr_at_5"],
    mm["overall"]["overall"]["mrr_at_5"]
]

fig_mrr = go.Figure(data=[
    go.Bar(
        name="Baseline (Cosine / Lexical)",
        x=categories,
        y=[v * 100 for v in base_mrr],
        text=[f"{v:.4f}" for v in base_mrr],
        textposition="auto",
        marker_color="#EF553B"
    ),
    go.Bar(
        name="Logistic Regression (C=0.1)",
        x=categories,
        y=[v * 100 for v in model_mrr],
        text=[f"{v:.6f}" for v in model_mrr],
        textposition="auto",
        marker_color="#00CC96"
    )
])

fig_mrr.update_layout(
    barmode="group",
    title="<b>So sánh chỉ số MRR@5 giữa Baseline và Mô hình Logistic Regression (C=0.1)</b>",
    xaxis_title="Phân chia tập dữ liệu & Phân loại nhãn",
    yaxis_title="Điểm số MRR@5 (%)",
    yaxis=dict(range=[96, 101]),
    template="plotly_white",
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

unified.render_plotly(fig_mrr, height=420)
```

---

## 4. Chi phí Tính toán trên CPU & Mức tiêu thụ Tài nguyên

Tuân thủ nguyên tắc **Zero External Knowledge** và thực thi thuần túy trên CPU (2 vCPU Colab):

1. **Thời gian thực thi pipeline M3 toàn diện (`run_config`):**
   - Tổng thời gian thực thi: **772.85 giây** (~**12.88 phút**).
   - Quy trình bao gồm: kiểm kê và băm SHA-256 cho **159 tệp đầu vào**, tiền xử lý cặp ứng viên, gán nhãn tự động, trích xuất 24 đặc trưng, cross-validation 5-fold, thẩm định trên tập Valid/Test, và xuất bảng `predictions`.
2. **Chi tiết thời gian huấn luyện mô hình (`training_report.timings_seconds`):**
   - **Tổng thời gian mô hình hóa:** **476.26 giây** (~**7.94 phút**).
   - *Kiểm định chéo 5 nếp (5-fold Group CV):* 407.85 s (chiếm 85.6% thời gian).
   - *Trích xuất đặc trưng huấn luyện (`train_features`):* 30.25 s trên 1,561,952 cặp dữ liệu.
   - *Thẩm định trên tập Valid (`validation`):* 16.78 s.
   - *Tải dữ liệu huấn luyện (`load_train`):* 14.36 s.
   - *Huấn luyện bộ vectorizer TF-IDF (109,864 từ):* 5.10 s.
   - *Khớp mô hình cuối cùng (`final_fit`):* **1.81 giây**.
3. **Mức độ tiêu thụ bộ nhớ RAM:**
   - **RAM đỉnh (`peak_rss_mb`):** **2,393.5 MB** (~**2.34 GB**).
   - Nằm hoàn toàn trong ngưỡng an toàn 12.67 GB của Colab CPU, không xảy ra hiện tượng tràn RAM.

---

## 5. Kết quả Kiểm định Toàn vẹn Dữ liệu Tự động (`validate_dataset`)

Nhóm thiết lập quy trình kiểm định toàn vẹn nghiêm ngặt hai tầng trước khi đóng gói dữ liệu bàn giao:

### A. Kiểm định Bảng dự đoán (`validation_model`)
Hàm kiểm định `validate_predictions` quét qua toàn bộ các dòng dự đoán:
- **Trạng thái kiểm định:** `valid = True` (🟢 **Hợp lệ tuyệt đối**).
- **Số dòng dự đoán kiểm tra:** **101,441 dòng**.
- **Số phân vùng bài báo kiểm tra:** **2,525 bài báo**.
- **Lỗi vi phạm schema / thiếu dữ liệu:** **0 lỗi** (`total_issues: 0`).
- **Cảnh báo dữ liệu bất thường:** **0 cảnh báo** (`warnings: []`).

### B. Kiểm định Toàn bộ 6 Bảng Parquet Toàn Nhóm (`dataset_validation`)
Quy trình `validate_dataset` kiểm tra cấu trúc schema, kiểu dữ liệu, khóa chính, và tính toàn vẹn tham chiếu của toàn bộ **6 bảng Parquet** trên cả 5 thư mục thành viên (`export/{owner}`):

| Thành viên (Owner) | Thư mục dữ liệu | Số bảng Parquet kiểm tra | Danh mục các bảng | Trạng thái kiểm định | Số lỗi phát hiện |
|:---|:---|:---:|:---|:---:|:---:|
| **Huỳnh Nhi** (`huynh-nhi`) | `export/huynh-nhi` | 6 bảng | `papers`, `references`, `elements`, `hierarchy`, `bibtex`, `predictions` | 🟢 **Hợp lệ (Valid)** | **0 lỗi** |
| **Mẫn Nhi** (`man-nhi`) | `export/man-nhi` | 6 bảng | `papers`, `references`, `elements`, `hierarchy`, `bibtex`, `predictions` | 🟢 **Hợp lệ (Valid)** | **0 lỗi** |
| **Hoàng** (`hoang`) | `export/hoang` | 6 bảng | `papers`, `references`, `elements`, `hierarchy`, `bibtex`, `predictions` | 🟢 **Hợp lệ (Valid)** | **0 lỗi** |
| **Minh Trọng** (`trong`) | `export/trong` | 6 bảng | `papers`, `references`, `elements`, `hierarchy`, `bibtex`, `predictions` | 🟢 **Hợp lệ (Valid)** | **0 lỗi** |
| **Phúc Khang** (`khang`) | `export/khang` | 6 bảng | `papers`, `references`, `elements`, `hierarchy`, `bibtex`, `predictions` | 🟢 **Hợp lệ (Valid)** | **0 lỗi** |
| **TOÀN BỘ 5 THÀNH VIÊN** | **5 kho dữ liệu xuất bản** | **30 bảng Parquet** | **Đầy đủ 6 bảng chuẩn hóa theo yêu cầu đề bài** | 🟢 **100% HỢP LỆ** | **0 LỖI** |

Kết quả kiểm định khẳng định toàn bộ hệ thống cơ sở dữ liệu Parquet và kết quả dự đoán Milestone 3 đạt độ tin cậy tuyệt đối, sẵn sàng bàn giao và tải lên Hugging Face Hub.

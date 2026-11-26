# 1.6 Thống kê

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Huỳnh Nhi (`TrinhNhi3011`)

Tiểu mục này trình bày các số liệu thống kê tổng hợp của pipeline thu thập dữ liệu (Milestone 1) nhằm đánh giá mức độ hoàn thành nhiệm vụ, hiệu quả tối ưu lưu trữ nguồn TeX, và độ bao phủ của mạng lưới trích dẫn dựa trên **100% dữ liệu crawl thực tế của toàn nhóm**.

---

## 1. Bảng 5 chỉ số bắt buộc theo yêu cầu đề bài

Các chỉ số dưới đây được tổng hợp trực tiếp từ tập kết quả `accepted_results.jsonl` và `scope.json` tại các mốc checkpoint chốt của cả 5 thành viên (Trọng `resume-40`, Mẫn Nhi `resume-31`, Huỳnh Nhi `resume-30`, Khang `resume-24`, Hoàng `resume-22`).

> [!NOTE]
> **Trạng thái dữ liệu:** 🟢 **Dữ liệu Crawl Thật (Toàn nhóm - 5 Thành viên)**  
> Dữ liệu được trích xuất tự động từ 65,240 bản ghi `Result` hợp lệ qua script `scripts/prepare_hoang.py`. Toàn bộ số liệu tuân thủ tuyệt đối quy tắc cộng dồn phiên bản theo từng bài báo.

| STT | Chỉ số bắt buộc theo đề | Giá trị tính toán | Ghi chú & Phương pháp tính toán |
|:---:|:------------------------|:-----------------:|:--------------------------------|
| **1** | **Số bài crawl thành công** | **20,870 / 23,988 bài** (Tỷ lệ: **87.0%**) | Số bài hoàn thành đầy đủ cả 3 công đoạn thu thập cốt lõi (Discovery $\to$ Metadata $\to$ Sources TeX/BibTeX). Các bài còn lại thuộc dạng tác giả chỉ nộp PDF (`pdf_only`) hoặc Word (`docx`) theo đúng quy chuẩn arXiv |
| **2** | **Kích thước trung bình mỗi bài (Trước lọc)** | **7,823.8 KB** (~7.46 MB / 7,823,833 bytes) | Trung bình cộng tổng dung lượng giải nén thô của tất cả các phiên bản của mỗi bài (*xem Lưu ý 1*) |
| | **Kích thước trung bình mỗi bài (Sau lọc)** | **492.1 KB** (492,123 bytes) | Giảm **93.7%** dung lượng lưu trữ sau khi loại bỏ hình ảnh và file nhị phân, bảo toàn 100% các file `.tex` và `.bib` phục vụ Milestone 2 |
| **3** | **Số reference trung bình mỗi bài** | **17.0 refs/bài** (Trích dẫn có arXiv ID) | Số reference thô trung bình thu thập từ Semantic Scholar Graph API là **37.6 refs/bài** trên tổng số 174,740 trích dẫn thô (*xem Lưu ý 2*) |
| **4** | **Tỷ lệ thành công crawl Reference Metadata** | **99.1%** (78,339 / 79,047 refs) | Tỷ lệ trích xuất thành công ngày nộp của bài được trích dẫn từ arXiv API trên tổng số arXiv references |
| **5** | **Phạm vi khảo sát (`scope`)** | **23,988 bài** (5 dải ID thuộc Computer Science / Data Science) | Phân chia cho 5 thành viên cào song song trên Google Colab CPU (`2501.xxxxx` đến `2505.xxxxx`) |

---

## 2. Lưu ý về phương pháp tính toán và đối chiếu dữ liệu

Nhằm đảm bảo sự chính xác tuyệt đối giữa yêu cầu của đề bài và cấu trúc dữ liệu lưu trữ, nhóm làm rõ hai điểm khác biệt cốt lõi:

### Lưu ý 1: Kích thước trung bình mỗi bài vs mỗi phiên bản
- Trong schema thu thập, trường `summary.mean_extracted_bytes_before_filter` ban đầu phản ánh kích thước trung bình **trên từng phiên bản (per version)** tải về từ `export.arxiv.org`.
- Tuy nhiên, đề bài yêu cầu kích thước trung bình **trên mỗi bài báo (per paper)**. Một bài báo có thể có nhiều phiên bản ($v_1, v_2, \dots, v_k$). Do đó, nhóm tính toán bằng cách cộng dồn tất cả các phiên bản trước khi lấy trung bình:
  $$\text{RawBytes}(P_i) = \sum_{v \in \text{Versions}(P_i)} \text{extracted\_bytes}(v)$$
  $$\overline{\text{Size}} = \frac{1}{N} \sum_{i=1}^N \text{RawBytes}(P_i)$$
- Trong đó $\text{RawBytes}(P_i)$ là tổng dung lượng trước lọc của bài $P_i$, và $\overline{\text{Size}}$ là kích thước trung bình mỗi bài. Nhờ công thức này, số liệu báo cáo phản ánh đúng tổng chi phí lưu trữ của toàn bộ lịch sử bài báo (trung bình 7.46 MB thô rút gọn xuống còn 492 KB sạch).

### Lưu ý 2: Phân loại số lượng Reference
Semantic Scholar Graph API trả về hai lớp dữ liệu trích dẫn:
1. **Tổng trích dẫn thô (`s2_reference_count`):** Bao gồm toàn bộ các tài liệu tham khảo (sách, hội thảo, bài báo thuộc nhiều nguồn xuất bản khác nhau). Toàn nhóm thu thập được 174,740 trích dẫn, trung bình đạt **37.6 tài liệu/bài**.
2. **Trích dẫn có định danh arXiv (`arxiv_reference_count`):** Chỉ lọc các trích dẫn có chứa mã số arXiv hợp lệ. Đây là tập hợp được đưa vào công đoạn truy vấn metadata ngày nộp bài qua arXiv API, đạt 79,047 trích dẫn, trung bình **17.0 tài liệu/bài**. Tỷ lệ truy vấn thành công ngày nộp đạt **99.1%**.

---

## 3. Trực quan hóa so sánh kích thước trước và sau lọc

Việc lọc bỏ các tệp hình ảnh (`.png`, `.jpg`, `.pdf`, `.eps`) trong các gói mã nguồn TeX giúp tiết kiệm đáng kể không gian lưu trữ và băng thông truyền tải, trong khi vẫn bảo toàn đầy đủ các lệnh nhúng hình (`\includegraphics`, `figure`) để phục vụ phân tích cấu trúc ở Milestone 2.

:::{figure} ../figures/fig-1-6-size-comparison.png
:name: fig-1-6-size-comparison
:alt: Biểu đồ so sánh kích thước trước và sau khi lọc hình ảnh theo từng thành viên

Biểu đồ so sánh dung lượng gói nguồn trung bình trước và sau khi loại bỏ hình ảnh theo từng người phụ trách (Owner) và trung bình toàn nhóm. Tỷ lệ tiết kiệm dung lượng thực tế đạt từ 92% đến 94% trên mọi dải dữ liệu.
:::

---

## 4. Thống kê chi tiết theo từng người phụ trách dải (Owner)

Dữ liệu crawl thực tế được phân chia đồng đều trên 5 dải ID với 5 máy ảo Google Colab CPU độc lập:

| Thành viên (Owner) | Mốc Checkpoint | Số bài phát hiện | Số bài thành công | Tỷ lệ thành công | Dung lượng sau lọc TB | Số ref arXiv TB |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hoàng** (`hoang`) | `resume-22` | 4,194 bài | 3,666 bài | 87.4% | 629.2 KB | —* |
| **Mẫn Nhi** (`man-nhi`) | `resume-31` | 5,000 bài | 4,378 bài | 87.6% | 548.7 KB | 15.8 refs/bài |
| **Huỳnh Nhi** (`huynh-nhi`) | `resume-30` | 4,977 bài | 4,379 bài | 88.0% | 484.5 KB | 18.1 refs/bài |
| **Khang** (`khang`) | `resume-24` | 4,817 bài | 4,016 bài | 83.4% | 325.7 KB | —* |
| **Minh Trọng** (`trong`) | `resume-40` | 5,000 bài | 4,431 bài | 88.6% | 426.9 KB | 18.3 refs/bài |
| **Toàn nhóm** | **5 mốc chốt** | **23,988 bài** | **20,870 bài** | **87.0%** | **492.1 KB** | **17.0 refs/bài** |

*(Ghi chú: Nhóm phân công chuyên biệt hóa các công đoạn chạy nặng: Khang và Hoàng tập trung tải và giải nén khối lượng lớn TeX sources; công đoạn trích xuất References API được Mẫn Nhi, Huỳnh Nhi và Trọng chạy chuyên sâu).*

---

*(Dữ liệu chi tiết được xuất tự động bởi `scripts/prepare_hoang.py` và lưu trữ tại `data/hoang/statistics_summary.json`)*.

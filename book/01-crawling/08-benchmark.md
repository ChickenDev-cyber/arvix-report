# 1.8 Benchmark (Colab CPU)

> **Người phụ trách:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Reviewer:** Mẫn Nhi (`@NhiNgo49`)

Tiểu mục này trình bày kết quả đo lường hiệu năng, thời gian thực thi và mức tiêu thụ tài nguyên phần cứng (CPU, RAM, Disk) của pipeline thu thập dữ liệu trên môi trường chuẩn **Google Colab (chỉ sử dụng CPU)** theo đúng quy định của đề bài.

---

## 1. Môi trường và phương pháp đo lường

Để đảm bảo tính tái lập và công bằng khi đánh giá, toàn bộ các phép đo benchmark chính thức được thực hiện trực tiếp trên máy ảo tiêu chuẩn Google Colab (CPU runtime) không sử dụng bộ tăng tốc GPU/TPU.

> [!NOTE]
> **Trạng thái dữ liệu:** 🟢 **Đo lường Thực tế (Google Colab CPU — Checkpoint: `m1-colab-hoang-01`)**  
> Dữ liệu hiệu năng được trích xuất trực tiếp từ các bộ đếm `process_tree_rss` (psutil) và file báo cáo `m1-colab-hoang-01.json` kết hợp nhật ký thời gian `events.jsonl`.

| Tiêu chí | Cấu hình máy ảo Google Colab tiêu chuẩn |
|:---|:---|
| **Hệ điều hành** | Linux kernel 6.6.159+ (Ubuntu 22.04 LTS x86_64) |
| **Vi xử lý (CPU)** | Intel(R) Xeon(R) CPU @ 2.20GHz — **2 vCPU** |
| **Dung lượng RAM hệ thống** | **12.67 GB** (13,605,818,368 bytes) |
| **Môi trường thực thi** | CPython 3.13.18 (Kiến trúc x86_64) |
| **Phương pháp giám sát RAM (`method`)** | Giám sát RSS toàn bộ cây tiến trình con qua thư viện `psutil` (chu kỳ lấy mẫu 0.1s) |
| **Chế độ bộ nhớ đệm (`cache_mode`)** | `mixed` (Hỗ trợ checkpoint lưu trạng thái SQLite và resume an toàn qua các lần restart Colab) |
| **Mã định danh Git Commit** | `f27db48` (Cải tiến cơ chế quản lý tiến trình, recovery và sidecar timing) |

---

## 2. Kết quả đo lường thời gian và tài nguyên

Các chỉ số thời gian chi tiết của từng bài báo và từng công đoạn được trích xuất từ chuỗi sự kiện `events.jsonl` và bộ đo lường benchmark độc lập:

| Nhóm chỉ số | Chỉ số cụ thể | Giá trị đo được | Đơn vị | Diễn giải kỹ thuật |
|:---|:---|:---:|:---:|:---|
| **Thời gian thực thi** | **Tổng thời gian Discovery** | **198.86** | giây | Quét toàn bộ dải 5,000 ID và xác minh hợp lệ theo lô 100 ID |
| | **Thời gian xử lý bài nhanh nhất** | **3.61** | giây | Bài có 1 phiên bản, dung lượng TeX nhỏ và ít trích dẫn |
| | **Thời gian xử lý bài chậm nhất** | **198.51** | giây | Bài có nhiều phiên bản lớn, nhiều file BibTeX và nhiều hình bị loại |
| | **Thời gian trung bình mỗi bài** | **75.92** | giây/bài | Tính trên toàn bộ các bài xử lý thành công trong phiên chạy |
| | **Tổng thời gian thực thi (Wall time)** | **24,366.93** | giây (~**6.77 giờ**) | Thời gian thực thi liên tục trên máy ảo Colab CPU |
| **Tài nguyên bộ nhớ** | **RAM Đỉnh (Peak RAM)** | **175.3** | MB (183,853,056 B) | Mức bộ nhớ cao nhất của toàn bộ cây tiến trình crawl |
| | **RAM Trung bình (Mean RAM)** | **112.7** | MB (118,219,749 B) | Mức tiêu thụ ổn định, chứng minh không có hiện tượng memory leak |
| **Không gian đĩa** | **Dung lượng đĩa tối đa (Peak Disk)** | **2,362.2** | MB (~**2.31 GB**) | Tính cả không gian giải nén tạm trước khi lọc hình ảnh |
| | **Dung lượng kết quả cuối (Output)** | **2,321.7** | MB (~**2.27 GB**) | Tổng dung lượng tệp nguồn TeX/BibTeX đã lọc sạch và JSONL |

> [!IMPORTANT]
> **Lưu ý về phương pháp đo lường:** Khi chạy crawler phân tán hoặc chạy lại từ checkpoint (resume), thời gian của các máy tính riêng biệt **không được cộng dồn cơ học** thành wall time của toàn bộ hệ thống. Thời gian ghi nhận ở bảng trên phản ánh đúng một phiên thực thi thực tế đầy đủ của dải `hoang` trên máy ảo Google Colab CPU độc lập.

---

## 3. Phân bố thời gian theo các công đoạn Pipeline

Biểu đồ dưới đây minh họa thời gian tiêu tốn cho từng công đoạn chính trong pipeline thu thập bài báo:

:::{figure} ../figures/fig-1-8-stage-timing.png
:name: fig-1-8-stage-timing
:alt: Biểu đồ phân bố thời gian theo công đoạn pipeline

Thời gian thực thi chi tiết của các công đoạn chính: Discovery (T1), Metadata (T2), Sources (T3) đo lường thực tế trên Google Colab CPU.
:::

### Nhận xét hiệu năng:
1. **Công đoạn tải và xử lý nguồn (Sources - T3):** Chiếm tỷ trọng lớn nhất (khoảng 77.5% tổng thời gian, tương đương 13.28 giờ xử lý) do phải thực hiện tải các tệp nén `.tar.gz` dung lượng lớn từ máy chủ `export.arxiv.org`, giải nén kiểm tra bảo mật chống path traversal / zip bomb, và quét lọc bỏ hình ảnh.
2. **Công đoạn Metadata (T2):** Chiếm khoảng 22.1% thời gian (3.78 giờ cho 4,194 bài, tương đương 3.25 giây/bài). Tốc độ này phản ánh đúng khoảng cách chờ bắt buộc tối thiểu 3.0 giây giữa các request theo điều khoản sử dụng (Terms of Use) của arXiv OAI-PMH API.
3. **Mức độ tiêu thụ RAM:** Đỉnh RAM duy trì ở mức rất an toàn (**175.3 MB**), chỉ chiếm khoảng **1.3%** tổng dung lượng RAM của máy ảo Colab CPU (12.67 GB). Điều này chứng minh kiến trúc stream tệp theo luồng và giải nén có kiểm soát hoạt động cực kỳ ổn định, không gây tràn bộ nhớ dù xử lý hàng nghìn bài báo liên tục.

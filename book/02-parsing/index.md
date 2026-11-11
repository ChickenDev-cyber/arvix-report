# Chương 2 — Milestone 2: Phân tích cú pháp phân cấp (Hierarchical Parsing)

> **Người phụ trách tổng hợp:** Hoàng (`huynhhuyhoang2006@gmail.com`)  
> **Phối hợp phát triển:** Minh Trọng (`Leader`), Huỳnh Nhi, Mẫn Nhi, Phúc Khang  
> **Reviewer:** Minh Trọng (`@phamminhtrong2306`), Mẫn Nhi (`@NhiNgo49`)

---

Chương 1 kết thúc với một kho dữ liệu nguồn TeX/BibTeX được lưu trữ theo từng phiên bản của hơn 23,988 bài báo, kèm siêu dữ liệu và lịch sử phiên bản đầy đủ. Chương 2 mô tả cách thức chuyển đổi kho nguồn phi cấu trúc này thành các cấu trúc dữ liệu quan hệ chuẩn hóa:
* Mỗi phiên bản của một bài báo được phân tích cú pháp thành một cây phân cấp (`VersionHierarchy`).
* Toàn bộ nội dung văn bản được làm sạch lệnh định dạng và chuẩn hóa toán học thống nhất.
* Tài liệu tham khảo `\bibitem` được trích xuất và chuyển đổi sang các mục chuẩn BibTeX.
* Khử trùng lặp đa mức (Multi-level Deduplication) giữa các phiên bản nhằm tối ưu hóa không gian lưu trữ và tái sử dụng dữ liệu.

---

## 1. Đầu vào từ Milestone 1

* **Kho nguồn TeX/BibTeX của từng phiên bản:** Gồm các tệp `.tex` và `.bib` đã được lọc sạch các tệp nhị phân và hình ảnh tĩnh nhưng vẫn bảo toàn đầy đủ các lệnh nhúng hình (`\begin{figure}`, `\includegraphics`).
* **Lịch sử phiên bản:** Danh sách phiên bản ($v_1, v_2, \dots$) của mỗi bài báo.
* **Phiên bản không có mã nguồn TeX (`unsupported` / PDF-only):** Được ghi nhận với bản ghi cây rỗng (`nodes = []`) theo đúng yêu cầu của đề bài để đảm bảo độ phủ 100% các bài đã thu thập.

---

## 2. Đầu ra: Bộ Ba Bảng Dữ liệu Chuẩn hóa

Kết quả của Milestone 2 được tổ chức thành 3 bảng dữ liệu quan hệ (được lưu dưới định dạng Apache Parquet phục vụ Milestone 3):

1. **`elements`:** Lưu trữ các phần tử nội dung độc bản (phân biệt) xuyên suốt mọi phiên bản của bài báo. Các câu hoặc công thức trùng lặp chính xác chỉ chiếm một dòng duy nhất.
2. **`hierarchy`:** Lưu trữ các cạnh quan hệ nút con – nút cha (`node - parent`) của cây phân cấp cho từng phiên bản.
3. **`bibtex`:** Lưu trữ toàn bộ các mục tài liệu tham khảo sau khi đã khử trùng lặp và hợp nhất toàn bộ các trường thông tin.

---

## 3. Cấu trúc Chương Báo cáo

| Tiểu mục | Nội dung Trình bày Chi tiết |
|---|---|
| [**2.1 Phân tích cú pháp phân cấp**](01-phan-cap.md) | Cơ chế xác định luồng biên dịch qua `\input`/`\include`, thuật toán Hierarchy Stack Engine quản lý cha - con, và 3 loại nút lá (`sentence`, `formula`, `figure`). |
| [**2.2 Chuẩn hóa và khử trùng lặp**](02-chuan-hoa.md) | Làm sạch lệnh định dạng, chuẩn hóa toán học, chuyển `\bibitem` sang BibTeX, khử trùng lặp trích dẫn và khử trùng lặp nội dung toàn văn. |
| [**2.3 Thống kê Phân tích Cú pháp**](03-thong-ke.md) | Tỷ lệ parse thành công, độ bao phủ phiên bản, số lượng phần tử `elements` và `bibtex` trước/sau khi khử trùng lặp. |
| [**2.4 Đo lường Hiệu năng (Benchmark)**](04-benchmark.md) | Thời gian chạy toàn bộ (Wall Time), thời gian trung bình mỗi bài, mức tiêu thụ RAM đỉnh điểm và dung lượng lưu trữ trên Google Colab CPU-only. |
| [**2.5 Bảng dữ liệu quan hệ**](05-bang-du-lieu.md) | Đặc tả chi tiết cấu trúc cột, kiểu dữ liệu, khóa chính/khóa ngoại và ví dụ trực quan về 3 bảng `elements`, `hierarchy`, `bibtex`. |

---

> [!NOTE]
> Toàn bộ các bảng số liệu thống kê và biểu đồ trong chương này được sinh tự động từ quá trình thực thi pipeline thực tế, tuân thủ đúng yêu cầu của giảng viên về tính tái lập và minh bạch khoa học.

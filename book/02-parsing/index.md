# Chương 2 — Milestone 2: Phân tích Cú pháp Phân cấp (Parsing)

> **Người phụ trách:** Huỳnh Nhi (`@TrinhNhi3011`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

Chương 2 mô tả quá trình phân tích cú pháp các tệp nguồn TeX/BibTeX thu thập từ Milestone 1 để chuyển hóa văn bản học thuật thành cấu trúc dữ liệu phân cấp phục vụ nghiên cứu khoa học dữ liệu.

## Danh mục các tiểu mục

- **[2.1 Phân tích cú pháp phân cấp](01-phan-cap.md):** Nhận diện tệp gốc `\documentclass`, duyệt đệ quy `\input`/`\include`, loại bỏ dòng chú thích và xây dựng cây phân cấp tài liệu.
- **[2.2 Chuẩn hóa và khử trùng lặp](02-chuan-hoa.md):** Chuẩn hóa lệnh định dạng, công thức toán học, trích xuất BibTeX và khử trùng lặp tham chiếu/nội dung qua các phiên bản.
- **[2.3 Thống kê](03-thong-ke.md):** Đo lường tỷ lệ parse thành công, độ phủ phiên bản từng bài báo và số lượng thực thể trước/sau khử trùng lặp.
- **[2.4 Benchmark](04-benchmark.md):** Đo lường wall-time, dung lượng bộ nhớ RAM và kích thước đầu ra trên môi trường Colab CPU.
- **[2.5 Bảng dữ liệu (elements, hierarchy, bibtex)](05-bang-du-lieu.md):** Đặc tả schema và minh họa dữ liệu cho 3 bảng đầu ra chuẩn hóa.

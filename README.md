# Báo cáo Jupyter Book — Dự án arXiv Data Science (Milestone 1–2)

> **Kho lưu trữ:** `ChickenDev-cyber/arvix-report`  
> **Trang báo cáo trực tuyến:** [https://chickendev-cyber.github.io/arvix-report/](https://chickendev-cyber.github.io/arvix-report/)  
> **Môn học:** Nhập môn Khoa học Dữ liệu — HCMUS  
> **Nhóm thực hiện:** ChickenDev

---

## 1. Cấu trúc thư mục dự án

```text
arvix-report/
├── myst.yml                              # Cấu hình MyST / Jupyter Book (Hoàng giữ)
├── requirements.txt                      # Danh mục gói phụ thuộc tổng hợp (Hoàng giữ)
├── reqs/
│   ├── hoang.txt                         # Thư viện riêng của Hoàng
│   ├── mannhi.txt                        # Thư viện riêng của Mẫn Nhi
│   └── huynhnhi.txt                      # Thư viện riêng của Huỳnh Nhi
├── CODEOWNERS                            # Phân quyền review tự động
├── .github/workflows/deploy.yml          # CI/CD tự động deploy lên GitHub Pages
├── README.md                             # Tài liệu hướng dẫn (Mẫn Nhi giữ)
├── scripts/
│   ├── prepare_hoang.py                  # Script xử lý dữ liệu của Hoàng
│   ├── prepare_mannhi.py                 # Script xử lý dữ liệu của Mẫn Nhi
│   └── prepare_huynhnhi.py               # Script xử lý dữ liệu của Huỳnh Nhi
├── data/
│   ├── hoang/                            # Thư mục dữ liệu tổng hợp của Hoàng
│   ├── mannhi/                           # Thư mục dữ liệu tổng hợp của Mẫn Nhi
│   └── huynhnhi/                         # Thư mục dữ liệu tổng hợp của Huỳnh Nhi
└── book/
    ├── index.md                          # Trang chủ sách
    ├── lib/
    │   ├── common.py                     # Module đọc dữ liệu dùng chung (Hoàng giữ)
    │   ├── hoang_*.py                    # Code vẽ bảng/hình của Hoàng
    │   ├── mannhi_*.py                   # Code vẽ bảng/hình của Mẫn Nhi
    │   └── huynhnhi_*.py                 # Code vẽ bảng/hình của Huỳnh Nhi
    ├── figures/                          # Biểu đồ và hình ảnh sinh ra từ code
    ├── 01-crawling/                      # Chương 1: Milestone 1 (Crawling)
    └── 02-parsing/                       # Chương 2: Milestone 2 (Parsing)
```

---

## 2. Quy tắc cộng tác và phân quyền (Tránh xung đột Git)

1. **Mỗi file đúng một chủ:** Tuyệt đối không chỉnh sửa file của thành viên khác. Nếu cần thay đổi file của người khác, hãy trao đổi qua issue hoặc nhắn trực tiếp.
2. **File dùng chung do Hoàng quản lý:** `myst.yml`, `requirements.txt`, `.github/workflows/`, `book/lib/common.py`. Mục lục đã được khai báo sẵn đầy đủ các tiểu mục.
3. **Thêm thư viện Python:** Ghi vào file tương ứng trong `reqs/<tên>.txt`. Không sửa trực tiếp `requirements.txt`.
4. **Dữ liệu:** Chỉ ghi vào `data/<tên>/` bằng script riêng `scripts/prepare_<tên>.py`. Tuyệt đối không commit corpus thô (`.tex`, `.bib`, `raw_references.json`).
5. **Vẽ bảng/hình:** Đặt trong `book/lib/<tên>_*.py`. Chỉ import `book.lib.common`.
6. **Nhánh làm việc (Branches):**
   - Mẫn Nhi: `report/mannhi`
   - Huỳnh Nhi: `report/huynhnhi`
   - Hoàng: `report/hoang`
7. **Quy trình gửi Pull Request (PR):**
   - Trước khi mở PR: `git pull --rebase origin main` và chạy lệnh kiểm tra build không lỗi.
   - Mỗi PR chỉ chạm các file thuộc quyền sở hữu của mình.
   - GitHub sẽ tự động gán reviewer theo file `CODEOWNERS`.

---

## 3. Hướng dẫn cài đặt và Build sách trên máy cục bộ

### Bước 1: Tạo môi trường ảo và cài đặt thư viện
```bash
# Khởi tạo môi trường ảo Python (khuyên dùng Python 3.10 - 3.12)
python -m venv .venv

# Kích hoạt môi trường (Windows PowerShell)
.venv\Scripts\Activate.ps1
# Hoặc trên Linux/macOS:
# source .venv/bin/activate

# Cài đặt toàn bộ dependencies
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị dữ liệu và sinh biểu đồ
```bash
python scripts/prepare_hoang.py
python scripts/prepare_mannhi.py
python scripts/prepare_huynhnhi.py
```

### Bước 3: Biên dịch sách sang HTML
```bash
python -m jupyter_book build --html
```

Kết quả tĩnh sẽ được tạo tại thư mục `_build/html/`. Bạn có thể mở tệp `_build/html/index.html` trên trình duyệt để kiểm tra giao diện trước khi commit.

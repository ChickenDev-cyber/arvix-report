# 1.1 Tổng quan và kiến trúc pipeline

> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

---

## 1. Mục tiêu

Milestone 1 xây dựng pipeline thu thập thông tin bài báo arXiv và các dữ liệu liên quan. Theo cấu trúc source hiện tại, pipeline có bốn công đoạn nghiệp vụ:

1. **Discovery (T1):** tạo ID ứng viên trong dải được giao, xác minh ID bằng arXiv API và tạo danh sách bài tìm được.
2. **Metadata (T2):** lấy tiêu đề, tác giả, ngày nộp lần đầu, lịch sử phiên bản và venue từ OAI-PMH arXivRaw.
3. **Sources (T3):** tải source của từng phiên bản, nhận diện định dạng và trích xuất các tệp TeX/BibTeX theo quy tắc của module.
4. **References (T4):** lấy danh sách tài liệu tham khảo từ Semantic Scholar, chuẩn hóa ID arXiv và bổ sung ngày nộp từ arXiv API.

T5 không phải một nguồn dữ liệu thứ năm. Đây là lớp điều phối các công đoạn, quản lý task, trạng thái, checkpoint, phục hồi và xuất kết quả.

## 2. Kiến trúc tổng thể

```{mermaid}
flowchart TD
    A["Cấu hình dải ID<br/>config.py"] --> B["T1 Discovery<br/>arXiv Atom API"]
    B --> C["Danh sách PaperTask"]
    C --> D["T5 PipelineRunner"]
    D --> E["T2 Metadata<br/>OAI-PMH arXivRaw"]
    D --> F["T3 Sources<br/>arXiv source endpoint"]
    D --> G["T4 References<br/>Semantic Scholar"]
    G --> H["arXiv API<br/>ngày nộp v1"]
    E --> I["Result theo schema 1.2"]
    F --> I
    G --> I
    B --> I
    I --> J["Validation + SQLite state"]
    J --> K["accepted_results.jsonl<br/>events / corpus / reports"]
```

Sơ đồ thể hiện quan hệ module ở mức chức năng. Khi chạy T5, `PipelineRunner` điều phối các stage theo thứ tự: discovery luôn chạy trước; stage `sources` gọi T3; stage `references` gọi T4. T2 được tích hợp vào luồng task metadata và được runner phục hồi/lưu trạng thái cùng các task khác. Các module nghiệp vụ trả về `Result`; runner kiểm tra kết quả rồi mới ghi nhận và xuất artifact.

## 3. Công nghệ và thư viện

| Thành phần | Vai trò trong dự án | Cách sử dụng |
|---|---|---|
| Python 3.10+ | Ngôn ngữ triển khai pipeline | Module và CLI trong `src/arxiv_pipeline/` |
| arXiv Atom API | Xác minh ID ứng viên ở T1; lấy ngày nộp v1 ở T4 | Gửi HTTP request và phân tích Atom XML |
| OAI-PMH arXivRaw | Lấy metadata và ngày của từng phiên bản ở T2 | `GetRecord` với `metadataPrefix=arXivRaw` |
| arXiv source endpoint | Tải gói source của từng phiên bản ở T3 | Download và trích xuất định dạng source được hỗ trợ |
| Semantic Scholar Graph API | Lấy references ở T4 | Phân trang qua trường `next` |
| `urllib`, `xml.etree.ElementTree`, `json`, `pathlib` | HTTP, XML, JSON và thao tác tệp | Thư viện chuẩn Python |
| SQLite | Trạng thái task và checkpoint của runner | `state.sqlite` theo `run_id` |

Các module HTTP trong repository sử dụng thư viện chuẩn Python, trong đó có `urllib`; không nên mô tả dự án là dùng `requests`. `matplotlib` chỉ được dùng ở phần sinh biểu đồ báo cáo nếu được khai báo trong môi trường của repo sách, không phải thư viện bắt buộc của pipeline crawl.

## 4. Cấu trúc module

| Module | File chính | Trách nhiệm |
|---|---|---|
| Hợp đồng dữ liệu | `contracts.py`, `pipeline_contracts.py` | Schema `Result`, `PaperTask`, `Scope`, `Statistics`, `Benchmark` và các protocol dùng chung |
| Discovery | `discovery/service.py`, `discovery/api.py` | Sinh ID, chia batch, xác minh Atom feed và tạo Result |
| Metadata | `metadata/service.py`, `metadata/api.py` | Đọc OAI-PMH, kiểm tra trường metadata và lịch sử phiên bản |
| Sources | `sources/service.py`, `sources/extractor.py`, `sources/api.py` | Tải source, nhận diện định dạng, giải nén và lọc tệp |
| References | `references/service.py`, `references/api.py`, `references/checkpoint.py` | Phân trang S2, chuẩn hóa references, lấy ngày arXiv và resume |
| Runner | `runner/service.py`, `runner/state.py`, `runner/checkpoints.py` | Điều phối stage, lưu trạng thái, phục hồi và xuất kết quả |
| Validation | `validation/` | Kiểm tra Result, artifact, scope và corpus |

## 5. Dữ liệu đầu ra

Các module dùng chung schema phiên bản `1.2` trong `contracts.py`. Một Result chứa các thông tin chính:

- `run_id`, `owner`, `is_mock`: nhận diện lượt chạy, thành viên phụ trách và dữ liệu thật/mô phỏng.
- `step`, `arxiv_id`, `version`: xác định công đoạn và bài/phiên bản liên quan.
- `status`: kết quả xử lý như `success`, `partial`, `empty`, `unsupported`, `not_found` hoặc `failed`.
- `data`, `missing_fields`, `error`: dữ liệu trả về, trường còn thiếu và lỗi nếu có.
- `provenance`, `metrics`, `duration_seconds`, `attempts`: nguồn gốc, số đo và thông tin thực thi.

Không được gộp `partial` với `success`: một Result `partial` có thể chứa dữ liệu đã lấy được nhưng vẫn còn ID chưa xác minh, trang chưa tải hoặc trường metadata còn thiếu. Tương tự, `empty` ở T4 biểu thị không có reference arXiv hợp lệ sau khi xử lý, không đồng nghĩa với lỗi truy cập.

## 6. Phạm vi và tính trung thực của số liệu

Số liệu trong báo cáo phải gắn với `run_id`, owner và cờ `is_mock`. Các file `statistics/*.json`, `benchmarks/*.json` và `runs/<run_id>/accepted_results.jsonl` trong bản repository được cung cấp có chứa dữ liệu mẫu `is_mock=true`; chúng hữu ích để kiểm tra luồng và dựng biểu đồ, nhưng không đại diện cho kết quả crawl thật toàn dải. Chỉ thay nhãn thành dữ liệu thật khi manifest của run xác nhận `is_mock=false`.

## 7. Kết quả dữ liệu thật toàn nhóm (25.000 bài báo)

Bảng dưới đây tổng hợp kết quả dữ liệu Milestone 1 cuối cùng của cả 5 thành viên (tổng nguồn từ `data/mannhi/m1_final_25k_summary.json`, `is_mock=false`), phản ánh đầy đủ phạm vi **25.000 bài báo** và **40.896 phiên bản** (trung bình `1,636` phiên bản/bài; `42,64%` bài có $\ge 2$ phiên bản):

| Owner | Dải ID | Số bài | Phiên bản khai báo | Bài có venue | Bài có arXiv refs | Tổng arXiv refs | Refs đủ metadata |
|---|---|---:|---:|---:|---:|---:|---:|
| `hoang` | `2503.06914` – `2503.11913` | 5.000 | 8.384 | 820 (16,40%) | 4.384 (87,68%) | 108.616 | 107.756 (99,21%) |
| `huynh-nhi` | `2409.03594` – `2409.08593` | 5.000 | 8.268 | 960 (19,20%) | 4.306 (86,12%) | 91.161 | 91.031 (99,86%) |
| `khang` | `2506.20788` – `2507.01658` | 5.000 | 7.933 | 767 (15,34%) | 4.325 (86,50%) | 96.537 | 96.537 (100,00%) |
| `man-nhi` | `2501.12642` – `2501.17641` | 5.000 | 8.251 | 918 (18,36%) | 3.538 (70,76%) | 78.635 | 78.635 (100,00%) |
| `trong` | `2504.17523` – `2505.00665` | 5.000 | 8.060 | 819 (16,38%) | 4.325 (86,50%) | 91.814 | 91.750 (99,93%) |
| **Toàn nhóm** | **5 dải** | **25.000** | **40.896** | **4.284 (17,14%)** | **20.878 (83,51%)** | **466.763** | **465.709 (99,77%)** |

### 7.1. Ghi nhận riêng trên tập `m1-colab-man-nhi-01`

Trên bản chạy thật `m1-colab-man-nhi-01` (`is_mock=false`), các công đoạn của Mẫn Nhi đạt:
- **Discovery:** `5.000/5.000` bài `found` (`0` `excluded`, `0` `unresolved`) trong `168,71` giây.
- **Metadata:** `5.000` bản ghi (`4.998` `success`, `2` `partial`).
- **Sources:** `8.199` phiên bản đã xử lý (`7.590` `success`, `609` `unsupported` không có TeX).
- **References:** `4.994` bài có kết quả (`3.538` `success`, `1.456` `empty`, đều có `complete=true`), thu được `78.635` arXiv references với `100%` đủ metadata ngày nộp.

### 7.2. Lưu ý về phạm vi benchmark

Các bản ghi benchmark chụp ở giai đoạn trung gian (ngày 06/11/2026) có `cache_mode=mixed` và `exit_code=2` trước khi hoàn tất đợt chạy bù cuối cùng cho một số dải. Do đó, số đo hiệu năng trung gian không dùng để thay thế kết quả toàn dải cuối cùng ở bảng trên.


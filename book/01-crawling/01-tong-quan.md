---
kernelspec:
  name: python3
  display_name: Python 3
---
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

Bảng dưới đây tổng hợp kết quả dữ liệu Milestone 1 cuối cùng của cả 5 thành viên từ `data/unified/m1_final_corpus.json` (`40.896` phiên bản khai báo, trung bình `1,636` phiên bản/bài; `42,64%` bài có $\ge 2$ phiên bản):

| Owner | Dải ID | Số bài | Phiên bản khai báo | Bài có venue | Bài có arXiv refs | Tổng arXiv refs | Refs đủ metadata |
|---|---|---:|---:|---:|---:|---:|---:|
| `hoang` | `2503.06914` – `2503.11913` | 5.000 | 8.384 | 820 (16,40%) | 4.384 (87,68%) | 108.616 | 107.756 (99,21%) |
| `huynh-nhi` | `2409.03594` – `2409.08593` | 5.000 | 8.268 | 960 (19,20%) | 4.306 (86,12%) | 91.161 | 91.031 (99,86%) |
| `khang` | `2506.20788` – `2507.01658` | 5.000 | 7.933 | 767 (15,34%) | 4.325 (86,50%) | 96.537 | 96.537 (100,00%) |
| `man-nhi` | `2501.12642` – `2501.17641` | 5.000 | 8.251 | 918 (18,36%) | 3.538 (70,76%) | 78.635 | 78.635 (100,00%) |
| `trong` | `2504.17523` – `2505.00665` | 5.000 | 8.060 | 819 (16,38%) | 4.325 (86,50%) | 91.814 | 91.750 (99,93%) |
| **Toàn nhóm** | **5 dải** | **25.000** | **40.896** | **4.284 (17,14%)** | **20.878 (83,51%)** | **466.763** | **465.709 (99,77%)** |

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m1 = unified.load_json("m1_final_corpus")
m1_batch = unified.load_json("m1_batch_summary")

owners = ["hoang", "huynh-nhi", "khang", "man-nhi", "trong"]
versions = [m1["by_owner"][o]["declared_versions"] for o in owners]
refs_total = [m1["by_owner"][o]["arxiv_references"] for o in owners]
wall_hours = [m1_batch["by_owner"][o]["active_wall_hours"] for o in owners]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("Phiên bản khai báo & arXiv references", "Thời gian chạy S2-Batch (giờ)"),
)
fig.add_trace(go.Bar(name="Phiên bản khai báo", x=owners, y=versions, marker_color="#0ea5e9"), row=1, col=1)
fig.add_trace(go.Bar(name="arXiv references", x=owners, y=refs_total, marker_color="#2563eb"), row=1, col=1)
fig.add_trace(
    go.Bar(name="Active wall (h)", x=owners, y=wall_hours, marker_color="#10b981", text=[f"{h:.2f}h" for h in wall_hours], textposition="outside"),
    row=1, col=2,
)
fig.update_layout(
    title="Tổng hợp kết quả Milestone 1 toàn nhóm (25.000 bài báo)",
    barmode="group",
    template="plotly_white",
)
unified.render_plotly(fig, height=380)
```

### 7.1. Kết quả đợt chạy S2-Batch (`m1_batch_summary.json`)

Trên đợt chạy chuẩn hóa toàn nhóm dùng Semantic Scholar POST batch:
- **Thời gian thực thi hoạt động:** `16,57` – `22,77` giờ/thành viên (giảm `31,69%` – `47,72%` so với mốc `26,02` – `35,48` giờ ngày 06/11).
- **Tổng lượt gọi HTTP được kiểm toán:** `74.323` lượt trên toàn nhóm (`14.470` – `15.109` lượt/người).
- **Tỷ lệ hoàn tất bài theo quy ước bài tập:** `24.732 / 25.000` bài (`98,93%`), trong đó `man-nhi` đạt `4.951 / 5.000` (`99,02%`) trong `20,71` giờ.

### 7.2. Lưu ý về phạm vi benchmark

Các bản ghi benchmark chụp ở giai đoạn trung gian (ngày 06/11/2026) chỉ dùng làm mốc đối chiếu trước tối ưu; mọi đánh giá sản lượng dữ liệu cuối cùng của Milestone 1 đều căn cứ vào `m1_final_corpus.json` và `m1_batch_summary.json`.


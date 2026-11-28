---
kernelspec:
  name: python3
  display_name: Python 3
---
# 1.5 Thu thập tài liệu tham khảo (References)


> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

---

## 1. Mục tiêu

T4 lấy danh sách tài liệu tham khảo của một bài báo từ Semantic Scholar Graph API, giữ lại bản ghi gốc đã nhận, chuẩn hóa các reference có arXiv ID và bổ sung ngày nộp phiên bản đầu từ arXiv API. Kết quả được lưu trong `Result` với `step="references"` theo schema 1.2.

## 2. Nguồn dữ liệu

| Nguồn | Dữ liệu sử dụng | Lý do |
|---|---|---|
| Semantic Scholar Graph API | Danh sách references, thông tin cited paper và `next` để phân trang | Cung cấp các mục tài liệu tham khảo của bài báo |
| arXiv Atom API | Trường `published` cho các arXiv ID được trích dẫn | Xác định ngày nộp v1 từ nguồn arXiv |

Ngày nộp được lấy từ arXiv API, không dùng `publicationDate` của Semantic Scholar và không suy ngày từ ID. `ArxivDateClient` chỉ trả ngày cho các ID nằm trong batch đã hỏi; ID không xuất hiện trong phản hồi không được tự động kết luận là không tồn tại.

## 3. Quy trình

```{mermaid}
flowchart TD
    A["PaperTask: owner + arxiv_id"] --> B["Semantic Scholar: page offset=0"]
    B --> C["Lưu raw page"]
    C --> D{"Có next offset?"}
    D -->|Có| E["Request trang tiếp theo"]
    E --> C
    D -->|Không| F["Gộp và chuẩn hóa references"]
    F --> G["Giữ ID arXiv hợp lệ"]
    G --> H["Batch tra ngày published từ arXiv API"]
    H --> I["Bổ sung submission_date"]
    I --> J["Tính missing_fields và metrics"]
    J --> K["Result: success / partial / empty"]
```

### 3.1. Phân trang Semantic Scholar

`SemanticScholarClient.references_page(arxiv_id, offset, limit)` gọi endpoint references của Graph API. Mặc định `page_size=100`, `max_pages=50`. Phản hồi phải là JSON object có trường `data` kiểu danh sách. Trường `next` phải là số nguyên lớn hơn offset hiện tại; nếu không có `next`, module xem như đã đến trang cuối.

Mỗi trang hợp lệ được sao chép vào `raw_references` theo thứ tự nhận được. Bản raw giữ các object gốc, kể cả mục không có arXiv ID, `citedPaper=null` và các mục trùng. Việc giữ raw giúp phân biệt số mục nguồn trả về với số ID arXiv duy nhất sau chuẩn hóa.

### 3.2. Chuẩn hóa và khử trùng

Module chỉ tạo `references` cho ID arXiv hợp lệ. Quy trình chuẩn hóa ID bao gồm bỏ khoảng trắng, tiền tố `arXiv:` và hậu tố phiên bản `vN`; ID cũ dạng phân lớp như `math.GT/0309136v2` được chuẩn hóa về `math/0309136`. ID không hợp lệ bị loại khỏi dictionary `references` nhưng vẫn thuộc số mục nguồn thô.

Các bản ghi trùng được gộp theo ID arXiv chuẩn. Với từng trường, module giữ giá trị không thiếu đầu tiên; không ghép danh sách tác giả từ nhiều bản ghi. Các xung đột được ghi vào `provenance`. Tiêu đề và danh sách tác giả rỗng được xem là thiếu.

### 3.3. Bổ sung ngày nộp

Các ID arXiv sau chuẩn hóa được **khử trùng lặp toàn cục** rồi chia batch tối đa 100 ID để tra `published` từ arXiv Atom API. Ngày chỉ được chấp nhận nếu thuộc batch được yêu cầu và có định dạng ISO hợp lệ: ngày `YYYY-MM-DD` hoặc timestamp có múi giờ. Giá trị không hợp lệ được xem là thiếu và xuất hiện trong `missing_fields`.

### 3.4. Trường dữ liệu và metrics

`Result.data` của T4 có ba trường quan trọng:

| Trường | Ý nghĩa |
|---|---|
| `raw_references` | Các mục gốc từ những trang Semantic Scholar đã chấp nhận, giữ thứ tự và duplicate |
| `references` | Dictionary theo arXiv ID đã chuẩn hóa, gồm `title`, `authors`, `submission_date`, `semantic_scholar_id` |
| `complete` | `true` khi đã lấy hết các trang Semantic Scholar; không có nghĩa mọi metadata đều đầy đủ |

Metrics gồm:

- `s2_reference_count`: số mục nhận được trước lọc và khử trùng; bằng `len(raw_references)`.
- `arxiv_reference_count`: số arXiv ID hợp lệ, duy nhất; bằng số key của `references`.
- `complete_reference_count`: số reference arXiv có đủ bốn trường metadata bắt buộc.

Bất biến cần giữ: `complete_reference_count <= arxiv_reference_count <= s2_reference_count`.

## 4. Quy tắc status

| Tình huống | Status | `data.complete` | Diễn giải |
|---|---|---:|---|
| Đã hết trang, có references arXiv và mọi trường bắt buộc đầy đủ | `success` | `true` | Lấy xong và metadata đầy đủ |
| Đã hết trang nhưng có trường metadata thiếu | `partial` | `true` | Phân trang xong, metadata chưa đầy đủ |
| Đã hết trang, không có reference arXiv hợp lệ | `empty` | `true` | Không có mục arXiv sau chuẩn hóa |
| Lỗi ở trang sau trang đầu | `partial` | `false` | Giữ các trang đã nhận, còn thiếu trang |
| Lỗi ngay trang đầu | `failed` hoặc `not_found` | Không có data | Không có dữ liệu trang được chấp nhận |
| Đạt giới hạn 50 trang khi còn trang tiếp | `partial` | `false` | Lỗi có thể retry; chạy lại để tiếp tục |

Lưu ý: `empty` không chứng minh bài báo không trích dẫn tài liệu nào; nó chỉ mô tả kết quả sau khi lọc về các ID arXiv hợp lệ.

## 5. Rate limit và retry

Client Semantic Scholar mặc định chờ 1 giây giữa các request, timeout 30 giây và tối đa 3 lần gửi cho một request. Client arXiv mặc định chờ ít nhất 3 giây. HTTP 429 được nhận diện là `rate_limited`; các lỗi server 500/502/503/504 và lỗi mạng có thể retry. `Retry-After` được đọc ở dạng số giây hoặc HTTP-date.

Một lưu ý kỹ thuật quan trọng khi gửi khóa API tới Semantic Scholar: `urllib.request.Request` mặc định chuẩn hóa tên header theo kiểu Title-Case (`x-api-key` bị đổi thành `X-Api-Key`), có thể gây từ chối xác thực trên một số cổng kiểm tra header chữ thường. Do đó, client sử dụng `http.client.HTTPSConnection` để giữ nguyên header `x-api-key` viết thường trên kết nối HTTP/1.1 TLS.

Nếu chạy qua runner, `RequestScheduler` có thể lưu lịch request và cooldown vào checkpoint store. Điều này giúp giữ deadline chờ qua lần restart thay vì gửi request quá sớm sau khi chương trình khởi động lại.

## 6. Resume và cache

T4 dùng chung hợp đồng `CheckpointStore` (`load(namespace, key)`, `save(record)`, `delete(namespace, key)`). Hai namespace chính:

| Namespace | Nội dung |
|---|---|
| `references` | Các trang đã nhận, offset, next offset và thời điểm lấy |
| `arxiv_dates` | Ngày nộp v1 đã xác minh của từng arXiv ID |

Key trang gồm owner, arXiv ID, page size và fields. Cache ngày dùng key `[arxiv_id]`; `run_id` được cô lập ở tầng store. Khi resume, `max_pages` chỉ đếm trang tải mới trong lượt hiện tại, nên chương trình có thể tiếp tục sau khi đã lưu 50 trang trước đó. Checkpoint sai schema hoặc sai identity phải báo lỗi rõ ràng, không được âm thầm xem như cache rỗng.

## 7. Kết quả thực nghiệm toàn nhóm và riêng Mẫn Nhi

Từ dữ liệu hợp nhất `m1_final_corpus.json` (`25.000` bài báo), toàn nhóm thu thập được **466.763 trích dẫn arXiv duy nhất** trên **20.878 bài có trích dẫn** (`83,51%`), trong đó **465.709** mục đủ 4 trường metadata (`99,77%`).

Riêng trên dải của Mẫn Nhi (`2501.12642` – `2501.17641`):
- Số bài có trích dẫn arXiv (`citing_papers_with_refs`): **3.538 / 5.000** (`70,76%`).
- Tổng số arXiv references duy nhất: **78.635** (trung bình `15,75` refs/bài trên toàn bộ các bài đã lấy), đạt **100,00%** (`78.635 / 78.635`) đủ metadata ngày nộp v1.
- Trong đợt chạy S2-Batch (`m1_batch_summary.json`): `3.545` bài `success`, `1.450` bài `empty` (tổng `4.995` bài hoàn tất truy vấn = `99,90%`).

## 8. Biểu đồ tương tác từ dữ liệu thật

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

owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
refs_arxiv = [m1["by_owner"][o]["arxiv_references"] for o in owners]
refs_complete = [m1["by_owner"][o]["ref_metadata_complete"] for o in owners]

mn_steps = m1_batch["by_owner"]["man-nhi"]["steps"]
mn_labels = ["success", "empty", "partial", "failed", "not_found"]
mn_vals = [mn_steps.get(f"references|{k}", 0) for k in mn_labels]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        f"arXiv references toàn nhóm ({m1['total_arxiv_references']:,})",
        "Trạng thái References của Mẫn Nhi (S2-Batch)",
    ),
)
fig.add_trace(go.Bar(name="Tổng arXiv refs", x=owners, y=refs_arxiv, marker_color="#0ea5e9"), row=1, col=1)
fig.add_trace(go.Bar(name="Đủ metadata v1", x=owners, y=refs_complete, marker_color="#16a34a"), row=1, col=1)
fig.add_trace(
    go.Bar(name="man-nhi", x=mn_labels, y=mn_vals, marker_color=["#16a34a", "#64748b", "#f59e0b", "#ef4444", "#dc2626"], text=[f"{v:,}" for v in mn_vals], textposition="outside"),
    row=1, col=2,
)
fig.update_layout(
    title="Kết quả thu thập References & độ phủ metadata arXiv v1",
    barmode="group",
    template="plotly_white",
)
unified.render_plotly(fig, height=390)
```


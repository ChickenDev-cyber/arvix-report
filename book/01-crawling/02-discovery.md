---
kernelspec:
  name: python3
  display_name: Python 3
---
# 1.2 Khám phá bài báo (discovery)

> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

---

## 1. Mục tiêu

Discovery tạo danh sách ID ứng viên theo dải được giao, gửi các ID đến arXiv API để xác minh bài tồn tại và phân loại từng ID thành:

- **Found:** API trả về entry có ID nằm trong batch được yêu cầu.
- **Excluded:** phản hồi Atom hợp lệ và đầy đủ xác nhận ID không xuất hiện trong feed.
- **Unresolved:** chưa đủ bằng chứng để kết luận, thường do lỗi request hoặc phản hồi không đầy đủ.

Việc phân biệt `excluded` và `unresolved` quan trọng: timeout, lỗi mạng hoặc phản hồi hỏng không được xem là bằng chứng một bài không tồn tại.

## 2. Cấu hình dải ID

Các dải hiện được khai báo trong `src/arxiv_pipeline/config.py` cho năm owner:

| Owner | Bắt đầu | Kết thúc |
|---|---:|---:|
| `khang` | 2025-06, ID 20788 | 2025-07, ID 1658 |
| `trong` | 2025-04, ID 17523 | 2025-05, ID 665 |
| `hoang` | 2025-03, ID 6914 | 2025-03, ID 11913 |
| `man-nhi` | 2025-01, ID 12642 | 2025-01, ID 17641 |
| `huynh-nhi` | 2024-09, ID 3594 | 2024-09, ID 8593 |

Các mốc được cấu hình `inclusive=True`. Hàm `candidate_ids()` tạo ID theo tháng với phần số thứ tự gồm năm chữ số, ví dụ `2501.12642`. Nếu dải đi qua tháng tiếp theo, chương trình tăng tháng và bắt đầu lại số thứ tự theo mốc kết thúc đã cấu hình. Không nên suy luận số bài thực tế từ số ID ứng viên: nhiều ID có thể không tồn tại.

## 3. Quy trình xử lý

```{mermaid}
flowchart TD
    A["Đọc RangeConfig"] --> B["Sinh candidate IDs"]
    B --> C["Chia batch tối đa 100 ID"]
    C --> D["Gửi arXiv Atom API"]
    D --> E{"Feed hợp lệ và đầy đủ?"}
    E -->|Có| F["Phân loại found / excluded"]
    E -->|Không hoặc payload lỗi| G["Xác minh từng ID còn mơ hồ"]
    G --> H{"Có entry hợp lệ?"}
    H -->|Có| I["Found"]
    H -->|Feed đầy đủ, không có entry| J["Excluded"]
    H -->|Request / payload chưa xác minh| K["Unresolved"]
    F --> L["Tổng hợp Result"]
    I --> L
    J --> L
    K --> L
```

### 3.1. Sinh ID và chia batch

`candidate_ids()` duyệt từng tháng trong cấu hình. `DiscoveryModule` mặc định dùng `batch_size=100`; tham số này có thể cấu hình nhưng không được vượt quá 100. `max_candidates` dùng để chạy thử trên một phần dải. Khi bị giới hạn, Result có `status=partial` và `data.complete=false`, kể cả khi mọi ID trong phần đã chạy đều được xác minh.

### 3.2. Gửi request và kiểm tra phản hồi

`ApiClient.query()` gửi danh sách ID bằng arXiv Atom API. `parse_feed()` kiểm tra payload XML, entry lỗi, ID trả về ngoài batch và tính đầy đủ của phản hồi. HTTP 200 không tự động đồng nghĩa với thành công: nội dung vẫn phải là Atom feed hợp lệ.

Client có timeout 30 giây, tối đa 3 lần gửi và khoảng cách mặc định 3 giây giữa request. Các lỗi mạng, HTTP 429 và một số lỗi server (500, 502, 503, 504) có thể được retry; nếu có `Retry-After`, client tôn trọng thời gian máy chủ yêu cầu.

### 3.3. Xác minh ID còn mơ hồ

Nếu batch có nhiều ID nhưng phản hồi không đủ để kết luận, module có thể truy vấn riêng từng ID. Một ID chỉ được đưa vào `excluded_ids` khi phản hồi riêng hợp lệ và đầy đủ nhưng không có entry tương ứng. Các trường hợp không xác minh được vẫn nằm trong `unresolved_ids`.

### 3.4. Checkpoint và chạy tiếp

Discovery độc lập qua CLI chỉ xuất preview sau khi hàm xử lý kết thúc; nó không tự lưu checkpoint. Khi chạy qua T5, `DiscoveryModule` có thể nhận `CheckpointStore`. Runner lưu kết quả phân loại theo batch trong namespace `discovery_batches`; batch đã xác minh được dùng lại, chỉ ID unresolved cần truy vấn lại. Checkpoint được kiểm tra owner, cấu hình dải, số batch và danh sách ID để tránh dùng nhầm dữ liệu của scope khác.

## 4. Status của Result

| Điều kiện | Status | Ý nghĩa |
|---|---|---|
| Duyệt hết dải và không còn ID unresolved | `success` | Discovery hoàn tất |
| Bị giới hạn số candidate hoặc còn ID unresolved nhưng vẫn có kết quả hữu ích | `partial` | Có dữ liệu nhưng chưa hoàn tất |
| Không xác minh được dữ liệu hữu ích | `failed` | Không có kết quả đủ tin cậy |

Trong `Result.data`, các trường chính là `papers`, `unresolved_ids`, `excluded_ids` và `complete`. `provenance` ghi nguồn API, cấu hình dải, tổng số candidate, số đã kiểm tra và phương pháp xác minh.

## 5. So sánh nguồn và lựa chọn

Trong repository hiện tại, Discovery thực tế dùng **arXiv Atom API**. OAI-PMH arXivRaw được dùng ở T2 để lấy metadata và lịch sử phiên bản, không phải một phương án Discovery song song. Không tìm thấy module tích hợp Kaggle trong source code được cung cấp, vì vậy báo cáo không khẳng định Kaggle đã được triển khai hoặc benchmark. Nếu cần trình bày so sánh các nguồn như một phần nghiên cứu, phải ghi rõ đó là đánh giá thiết kế, không phải kết quả thực nghiệm của code hiện tại.

## 6. Dữ liệu và biểu đồ từ run thật

Từ dữ liệu hợp nhất `m1_final_corpus.json`, toàn nhóm đã rà soát tổng cộng **179.012 ID ứng viên** để thu được đúng **25.000 bài báo hợp lệ** (5.000 bài/thành viên). Hai dải bắc ngang ranh giới tháng (`trong`: `2504.17523–2505.00665` quét `83.142` ID; `khang`: `2506.20788–2507.01658` quét `80.870` ID) phải quét cạn tới `99999` của tháng đầu trước khi chuyển tháng mới, trong khi 3 dải nội tháng (`hoang`, `man-nhi`, `huynh-nhi`) quét đúng `5.000` ID.

Riêng dải của Mẫn Nhi (`2501.12642` – `2501.17641`):
- Số ID ứng viên đã kiểm tra: `5.000 / 5.000` (chia 50 batch, `0` `excluded_ids`, `0` `unresolved_ids`).
- Thời gian thực thi Discovery: `168,5` giây trong đợt chạy S2-Batch (`m1_batch_summary.json`).

```{code-cell} python
:tags: [remove-input]
import sys
from pathlib import Path
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m1 = unified.load_json("m1_final_corpus")
owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
candidates = [m1["by_owner"][o]["range"]["discovery_candidates"] for o in owners]
found = [m1["by_owner"][o]["papers"] for o in owners]

fig = go.Figure(data=[
    go.Bar(name="ID ứng viên đã quét", x=owners, y=candidates, marker_color="#94a3b8", text=[f"{v:,}" for v in candidates], textposition="outside"),
    go.Bar(name="Bài hợp lệ tìm thấy", x=owners, y=found, marker_color="#2563eb", text=[f"{v:,}" for v in found], textposition="outside"),
])
fig.update_layout(
    title=f"Discovery toàn nhóm: {m1['total_discovery_candidates']:,} ứng viên → {m1['total_papers']:,} bài báo",
    yaxis_type="log",
    yaxis_title="Số lượng ID (thang log)",
    barmode="group",
    template="plotly_white",
)
unified.render_plotly(fig, height=380)
```


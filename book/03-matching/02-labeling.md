---
kernelspec:
  name: python3
  display_name: Python 3
---
# 3.2 Gán nhãn thủ công & tự động

> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Phúc Khang (`@khang1108`) / Huy Hoàng (`@huynhhuyhoang2006@gmail.com`)

---

## 1. Tổng quan nguồn nhãn (`pool_and_split`)

Trong Milestone 3, tập dữ liệu gán nhãn gồm **2.525 bài báo** (`505` bài/thành viên) được tách theo bài báo (`make_split`) thành `2.505` bài huấn luyện, `10` bài kiểm định (`valid`) và `10` bài kiểm tra (`test`):

- **Nhãn thủ công (`manual`):** `25` bài báo (`5` bài/thành viên; `15` train / `5` valid / `5` test), tổng cộng `2.519` dòng kiểm tra và **1.880 cặp khớp (`matched`)**.
- **Nhãn tự động (`automatic`):** `2.500` bài báo (`500` bài/thành viên = đúng `10%` quy mô `5.000` bài/dải; `2.490` train / `5` valid / `5` test), tạo ra `98.922` dòng nhãn và **33.493 cặp khớp (`matched`)**.

Trên toàn bộ 6 bảng phát hành cuối cùng (`predictions`), tổng cộng có **101.441 dòng** thuộc `1.934` bài có BibTeX (`591` bài còn lại không có BibTeX nên không phát sinh truy vấn đối sánh).

---

## 2. Quy trình gán nhãn thủ công (25 bài báo)

Mỗi thành viên nhận một mẫu đối chiếu thủ công (`generate_manual_template`) gồm tối thiểu **5 bài báo** thuộc dải của mình và bắt buộc đạt tối thiểu **20 cặp khớp (`matched`) mỗi bài**. Bộ kiểm tra `validate_labels` xác nhận:

- **Không trùng khóa** (`duplicate_keys = 0`) và **không trùng nhãn chuẩn** trong cùng một bài (`duplicate_gt_in_paper = 0`).
- Tất cả 25 bài đều vượt ngưỡng tối thiểu 20 cặp khớp/bài (thấp nhất là `26` cặp ở `2503.08548`, cao nhất là `226` cặp ở `2501.13104`).

| Thành viên | Số bài | Tổng dòng | `matched` | `no_match` | `unreviewed` | Thấp nhất / bài |
|---|---:|---:|---:|---:|---:|---:|
| `man-nhi` | 5 | 1.262 | **882** | 380 | 0 | 128 |
| `huynh-nhi` | 5 | 637 | **510** | 0 | 127 | 99 |
| `trong` | 5 | 278 | **189** | 0 | 89 | 27 |
| `hoang` | 5 | 183 | **157** | 0 | 26 | 26 |
| `khang` | 5 | 159 | **142** | 17 | 0 | 27 |
| **Tổng cộng** | **25** | **2.519** | **1.880** | **397** | **242** | **26** |

*(Lưu ý: các mục không khớp còn để trạng thái `unreviewed` ở `huynh-nhi`, `trong`, `hoang` đều không nằm trong tập truy vấn đánh giá `MRR@5`, vì chỉ những mục `matched` mới có đích chuẩn để xếp hạng.)*

---

## 3. Bộ quy tắc heuristic 3 tầng tự động (`heuristic-v1.0.0`)

Đối với `2.500` bài báo tự động, hàm `match_bibtex_entry_to_candidates` trong `arxiv_pipeline.matching.labeling` áp dụng 3 tầng quy tắc tất định hoàn toàn độc lập với bộ đặc trưng học máy:

1. **Tầng 1 — Khớp trực tiếp theo mã arXiv (`direct_arxiv_id_match`):**
   Trích mã arXiv từ các trường `url`, `doi`, `journal`, `title` của BibTeX (`extract_arxiv_id`). Nếu mã trích được có trong tập ứng viên `references` của bài $\rightarrow$ gán `matched`. **Quy tắc chặn lỗi:** nếu BibTeX ghi rõ một mã arXiv nhưng mã đó *không có* trong tập `references` đã crawl, hệ thống trả về `no_match` (`explicit_arxiv_id_not_in_references`) và tuyệt đối không rơi xuống so khớp tiêu đề để tránh gán nhầm bài khác.
2. **Tầng 2 — Khớp chính xác tiêu đề chuẩn hóa (`exact_normalized_title_match`):**
   Chuẩn hóa tiêu đề (`normalize_title`: bỏ macro LaTeX, dấu câu, chữ thường), đồng thời kiểm tra tính nhất quán số phần (`extract_part_spec`: không cho khớp `Part I` với `Part II`). Nếu có nhiều hơn 1 ứng viên trùng tiêu đề, tiếp tục lọc theo họ tác giả (`exact_title_author_disambiguated`); nếu vẫn không phân tách được thì gán `ambiguous`.
3. **Tầng 3 — So khớp mờ có kiểm soát (`high_similarity_match`):**
   Yêu cầu tiêu đề dài tối thiểu `8` ký tự, chặn xung đột số phần và chặn xung đột từ ghép gạch nối (ví dụ `LoRA-FA` vs `LoRA`), kiểm tra cả `jaccard_similarity >= 0.65` và `min_contain >= 0.65`. Điểm tổng hợp `final_score` cộng thưởng tác giả (`+0.08`), năm xuất bản khớp hoặc lệch $\le 1$ (`+0.04`), và phạt `-0.15` nếu lệch $> 3$ năm. Chỉ gán `matched` khi `final_score >= 0.82`, `title_score >= 0.70`, và khoảng cách với ứng viên đứng nhì đạt tối thiểu `AMBIGUITY_MARGIN = 0.10`.

---

## 4. Kiểm toán chất lượng heuristic (Thí nghiệm E4)

Chạy kiểm toán `heuristic-v1.0.0` đối chiếu trên đúng 25 bài báo gán nhãn thủ công (`experiments["E4_heuristic"]`):

- **Precision:** **98,72%** (`1.858 / 1.882`)
- **Recall:** **98,83%** (`1.858 / 1.880`)
- **Phân rã kết quả:** `1.858` `correct`, `373` `correct_no_match`, `24` `false_match` (toàn bộ `24/24` ca dương tính giả phát sinh ở Tầng 3 `high_similarity_match`, nơi chỉ đạt `5/29` chính xác do ngưỡng lọc token ngắn `len <= 2`), và `22` `missed` (`21/22` ca bỏ sót bắt nguồn từ `explicit_arxiv_id_not_in_references` khi mã cũ như `cs.CV/...` chưa chuẩn hóa về `cs/...`, và `1` ca từ `no_valid_candidate_scores`).

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

m3 = unified.load_json("m3_unified_summary")
labels = m3["labels"]
status_dist = labels["status_distribution"]
s_labels = ["no_match", "matched", "unreviewed", "ambiguous"]
s_vals = [status_dist.get(k, 0) for k in s_labels]

manual_by_owner = labels["manual_audit"]["by_owner"]
owners = ["man-nhi", "huynh-nhi", "trong", "hoang", "khang"]
m_matched = [manual_by_owner[o]["status_counts"].get("matched", 0) for o in owners]
m_other = [manual_by_owner[o]["rows"] - manual_by_owner[o]["status_counts"].get("matched", 0) for o in owners]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        f"Phân bố trạng thái trên {labels['total_rows']:,} dòng predictions",
        f"Nhãn thủ công theo thành viên ({labels['manual_audit']['totals']['matched']:,} matched)",
    ),
)
fig.add_trace(
    go.Bar(
        name="predictions",
        x=s_labels,
        y=s_vals,
        marker_color=["#64748b", "#16a34a", "#f59e0b", "#ef4444"],
        text=[f"{v:,}" for v in s_vals],
        textposition="outside",
    ),
    row=1, col=1,
)
fig.add_trace(go.Bar(name="matched", x=owners, y=m_matched, marker_color="#2563eb"), row=1, col=2)
fig.add_trace(go.Bar(name="no_match / unreviewed", x=owners, y=m_other, marker_color="#cbd5e1"), row=1, col=2)
fig.update_yaxes(type="log", title_text="Số dòng (thang log)", row=1, col=1)
fig.update_yaxes(title_text="Số cặp nhãn thủ công", row=1, col=2)
fig.update_layout(
    title="Tổng hợp phân bố nhãn toàn cục & kiểm toán gán nhãn thủ công (Milestone 3)",
    barmode="stack",
    template="plotly_white",
)
unified.render_plotly(fig, height=400)
```

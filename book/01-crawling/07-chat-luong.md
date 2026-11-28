---
kernelspec:
  name: python3
  display_name: Python 3
---
# 1.7 Chất lượng dữ liệu và bảng dữ liệu

> **Người phụ trách:** Huỳnh Nhi (`@TrinhNhi3011`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
import pandas as pd

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m1 = unified.load_json("m1_final_corpus")
batch = unified.load_json("m1_batch_summary")
OWNERS = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
```

Mục này trả lời hai câu hỏi về dữ liệu thu được ở Milestone 1: dữ liệu có đúng cấu trúc không, và dữ liệu đã đủ chưa. Sau đó mục này trình bày cách các bản ghi `Result` của pipeline được ánh xạ sang hai bảng `papers` và `references` mà đề yêu cầu. Các chỉ số tổng hợp như tỷ lệ thành công hay số reference trung bình nằm ở mục 1.6.

## 1. Hai báo cáo: `validation.json` và `quality.json`

Mỗi lần runner lưu checkpoint, nó ghi bộ file bàn giao (handoff) trong `runs/<run_id>/`: `scope.json`, `accepted_results.jsonl`, `validation.json` và `quality.json`. Hai file sau đều có dạng `{"valid": bool, "issues": [...]}`, nhưng trả lời hai câu hỏi khác nhau.

| | `validation.json` | `quality.json` |
|---|---|---|
| Câu hỏi | Bộ handoff có đúng cấu trúc và nhất quán không? | Dữ liệu đã thu thập đủ chưa? |
| Hàm kiểm tra | `validate_handoff` (`validation/corpus.py`) và `validate_result` (`validation/results.py`) | `validate_corpus` và `paper_issues` (`validation/corpus.py`) |
| Khi `valid = false` | Không được dùng bộ dữ liệu; runner không ghi `scope.json` và `accepted_results.jsonl` mới | Dữ liệu vẫn dùng được nhưng còn việc chưa xong; phải ghi rõ phạm vi khi báo cáo |
| Ví dụ issue | Sai kiểu trường, trùng task, kết quả thuộc run khác, nguồn của phiên bản chưa được metadata xác minh | Discovery còn ID chưa xử lý, metadata chưa `success`, phiên bản thiếu TeX, references chưa xong |

Như vậy một run có thể có `validation.valid = true` (dữ liệu đúng) nhưng `quality.valid = false` (dữ liệu chưa đủ), chẳng hạn khi run dừng giữa chừng do giới hạn thời gian của Colab. Ngược lại, chỉ cần `validation.valid = false` là toàn bộ handoff không được dùng.

Các bộ phận khác của hệ thống đều dựa trên quy ước này. Bộ thu gom (`collection/inspector.py`) chỉ nhận một run khi `validation.json` đúng bằng `{"valid": true, "issues": []}`. Trước khi xuất `quality.json`, runner tự chạy lại `validate_handoff`, nên mọi issue cấu trúc cũng xuất hiện trong `quality.json`.

### 1.1. Các luật kiểm tra cấu trúc (validation)

Mỗi `Result` được kiểm tra riêng trước, sau đó cả tập được kiểm tra chéo:

1. Kiểu và trường: đúng schema 1.2, không thiếu và không thừa trường, giá trị JSON hữu hạn, `run_id` chỉ gồm chữ, số, `_`, `-`.
2. Trạng thái hợp lệ theo bước: ví dụ `unsupported` chỉ có ở `sources`, `empty` chỉ có ở `references`, `not_found` không có ở `discovery`.
3. Chủ thể: `discovery` có `arxiv_id = null` (một kết quả cho cả dải); các bước khác phải có arXiv ID hợp lệ. Chỉ `sources` có `version ≥ 1`.
4. Nhất quán giữa `status`, `data` và `error`: `failed`/`not_found` phải có `data = null` và có `error`; `success`/`empty`/`unsupported` không được có `error` hay `missing_fields`; mọi JSON Pointer trong `missing_fields` phải trỏ tới trường có thật.
5. Thời gian: `finished_at` không sớm hơn `started_at`; `attempts` và `duration_seconds` không âm.
6. Kiểm tra chéo trong handoff: mỗi task (owner, step, arxiv_id, version) chỉ có một kết quả được chấp nhận; mọi kết quả thuộc đúng run và đúng chế độ mock/thật của `scope.json`; bài nằm trong dải được giao cho owner; số đếm trong `scope.json` khớp; mỗi phiên bản có nguồn phải nằm trong `versions` của metadata đã chấp nhận; cờ `versions_complete` của scope khớp với metadata.

Luật 6 bảo đảm rằng run thật không bao giờ trộn với dữ liệu mock: nếu có, đó là lỗi cấu trúc, không bị âm thầm lọc bỏ.

### 1.2. Các luật kiểm tra độ đầy đủ (quality)

Với mỗi dải ID được giao, kết quả discovery phải không lỗi và không còn `unresolved_ids`. Với mỗi bài trong scope (`paper_issues`):

- metadata phải có trạng thái `success`;
- mọi phiên bản trong `versions` phải có `Result` sources với trạng thái `success`;
- references phải có trạng thái `success` hoặc `empty` (bài thật sự không có tài liệu tham khảo).

Luật này khắt khe hơn những gì được chấp nhận về cấu trúc: một phiên bản `unsupported` là kết quả hợp lệ (không có lỗi validation) nhưng vẫn bị tính là "TeX source unavailable or incomplete" trong `quality.json`, vì bài đó không có đủ nguồn TeX cho Milestone 2.

### 1.3. Kết quả trên dữ liệu chốt 25,000 bài

Đợt chạy S2-Batch có 5 run chính thức (mỗi thành viên một run, 5000 bài). [](#tbl-1-7-validation) ghi lại hai báo cáo của từng run. Bốn run có `validation.valid = true` và không có issue cấu trúc. Run của Khang có `validation.valid = false` với đúng một issue: "Handoff is being updated; wait for a successful checkpoint" (ở bước discovery), do bộ handoff được lưu lúc runner đang cập nhật checkpoint. Vì vậy file `assignment-statistics-schema12.json` không được sinh cho Khang, và các số đo theo schema 1.2 của Khang là `null`; số liệu cấp bài của Khang trong báo cáo lấy từ phần `assignment`.

Về độ đầy đủ, `quality_valid` là `false` ở bốn run có ghi nhận (Huỳnh Nhi, Hoàng, Trọng, Khang) và không có giá trị ở run của Mẫn Nhi. Điều này đúng với luật ở mục 1.2: còn các phiên bản `unsupported` (không có TeX) và một số bài chưa đủ references, nên dữ liệu dùng được nhưng không phải bài nào cũng đủ cả ba bước.

```{code-cell} python
:tags: [remove-input]
:label: tbl-1-7-validation
:caption: Kết quả validation và quality của năm run S2-Batch (nguồn m1_batch_summary.json)
rows = []
for o in OWNERS:
    d = batch["by_owner"][o]
    qv = d["quality_valid"]
    rows.append({
        "Thành viên": o,
        "validation.valid": d["validation"]["valid"],
        "Số issue validation": len(d["validation"]["issues"]),
        "quality.valid": "không có" if qv is None else qv,
        "Bài hoàn tất (assignment)": d["assignment"]["papers_complete"],
        "Tỷ lệ hoàn tất (%)": round(d["assignment"]["paper_success_rate"] * 100, 2),
    })
pd.DataFrame(rows)
```

Toàn nhóm có 24,732 / 25,000 bài (98.93%) hoàn tất theo định nghĩa `assignment`; số bài có đủ cả ba bước theo định nghĩa chặt của schema 1.2 thấp hơn, như đã nêu ở mục 1.4.

## 2. Ánh xạ sang bảng `papers`

Đề quy định bảng `papers` có một dòng cho mỗi bài. Mỗi dòng được lấy từ `data` của `Result` có `step = "metadata"` (mục 1.3):

| Cột của đề | Kiểu theo đề | Lấy từ `Result` metadata |
|---|---|---|
| `arxiv_id` | string, non-null | `data.arxiv_id` |
| `title` | string | `data.title` |
| `authors` | list of strings | `data.authors` |
| `submission_date` | ISO string | `data.submission_date` (ngày nộp v1) |
| `revised_dates` | list of strings | `data.revised_dates` (ngày nộp v2…vN) |
| `venue` | string, nullable | `data.venue` (lấy từ `journal-ref`) |

Các trường còn lại của `Result` (`versions`, `versions_complete`, `missing_fields`, `provenance`) không đưa vào bảng nhưng được dùng để kiểm tra chất lượng như trên. Bảng `papers` cuối cùng có 25,000 dòng, dung lượng Parquet 3,908,515 byte. [](#tbl-1-7-papers-sample) là 12 dòng thật lấy từ file Parquet (cột danh sách hiển thị dạng JSON; cột `venue` rỗng nghĩa là `null`).

```{code-cell} python
:tags: [remove-input]
:label: tbl-1-7-papers-sample
:caption: 12 dòng thật của bảng papers
unified.load_sample_csv("papers")
```

## 3. Ánh xạ sang bảng `references`

Bảng `references` có một dòng cho mỗi cặp (bài trích dẫn, bài được trích dẫn). Mỗi dòng lấy từ từ điển `data.references` của `Result` có `step = "references"` (mục 1.5), với khóa là arXiv ID đã chuẩn hóa của bài được trích dẫn:

| Cột của đề | Kiểu theo đề | Lấy từ `Result` references |
|---|---|---|
| `arxiv_id` | string, non-null | `arxiv_id` của `Result` (bài trích dẫn) |
| `ref_arxiv_id` | string, non-null | khóa của `data.references` |
| `ref_title` | string | `data.references[id].title` |
| `ref_authors` | list of strings | `data.references[id].authors` |
| `ref_submission_date` | string | `data.references[id].submission_date` (lấy từ arXiv API, không dùng `publicationDate` của Semantic Scholar) |
| `ref_s2_id` | string | `data.references[id].semantic_scholar_id` |

Chỉ những tài liệu tham khảo có arXiv ID mới trở thành dòng của bảng `references`, vì bảng này dùng arXiv ID làm khóa và là tập đối sánh cho Milestone 3. Danh sách đầy đủ mà Semantic Scholar trả về, kể cả các mục không có arXiv ID, vẫn được giữ cục bộ trong `data.raw_references` theo yêu cầu của đề, nhưng không đưa vào bảng và không đưa lên repo.

Bảng `references` cuối cùng có 466,763 dòng từ 20,878 bài có ít nhất một tham khảo arXiv (83.51% số bài), dung lượng Parquet 78,657,673 byte. Có 465,709 dòng (99.77%) đủ các trường bắt buộc. [](#tbl-1-7-references-sample) là 12 dòng thật.

```{code-cell} python
:tags: [remove-input]
:label: tbl-1-7-references-sample
:caption: 12 dòng thật của bảng references
unified.load_sample_csv("references")
```

## 4. Ghi chú về việc công bố dữ liệu

Đề không cho phép nộp dữ liệu ở Milestone 1 và 2. Bảng `papers` và `references` được xuất thành Parquet trên Hugging Face ở bước cuối (mỗi thành viên một repo cá nhân, xem mục 3.3). Repo sách chỉ chứa các file tổng hợp nhỏ trong `data/unified/` và vài dòng ví dụ ở trên.

## 5. Tài liệu tham khảo

- Bryan, P. & Nottingham, M. (2013). *JavaScript Object Notation (JSON) Pointer*, RFC 6901. https://www.rfc-editor.org/rfc/rfc6901
- Semantic Scholar. *Academic Graph API*. https://api.semanticscholar.org/api-docs/graph

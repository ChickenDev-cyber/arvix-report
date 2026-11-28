---
kernelspec:
  name: python3
  display_name: Python 3
---
# 1.4 Nguồn TeX/BibTeX và loại hình

> **Người phụ trách:** Huỳnh Nhi (`@TrinhNhi3011`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

```{code-cell} python
:tags: [remove-cell]
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "myst.yml").exists())
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from book.lib import unified

m1 = unified.load_json("m1_final_corpus")
OWNERS = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
```

Bước T3 tải gói nguồn mà tác giả đã nộp lên arXiv cho từng phiên bản của mỗi bài, giải nén an toàn, chỉ giữ lại file `.tex` và `.bib`, và ghi lại năm số đo dung lượng. Đây là đầu vào của Milestone 2 (Chương 2). Mã nguồn nằm trong `src/arxiv_pipeline/sources/`: `api.py` tải file, `extractor.py` nhận diện định dạng, `handlers/` giải nén theo từng định dạng, và `service.py` đóng gói kết quả thành `Result`.

## 1. Tải nguồn theo từng phiên bản

Nguồn của phiên bản N được tải từ endpoint:

```text
https://export.arxiv.org/src/<arxiv_id>v<N>
```

Danh sách phiên bản lấy từ `Result` metadata đã được chấp nhận (mục 1.3), nên mỗi bài có N phiên bản sẽ sinh ra N bản ghi `Result` với `step = "sources"` và `version = N`. Mỗi phiên bản được xử lý độc lập: một phiên bản lỗi không làm mất các phiên bản khác của cùng bài.

Client tải theo luồng (streaming) bằng `urllib.request`, giãn cách tối thiểu 3 giây giữa hai request như các bước khác, và từ chối file lớn hơn 200 MiB. Lần tải và các lần giải nén lại dùng chung một ngân sách tối đa 3 lần gửi request. Một file gzip bị cắt cụt (thường do đường truyền) được coi là lỗi có thể thử lại; các lỗi cấu trúc khác thì không.

Kết quả chốt trên corpus 25,000 bài: metadata khai báo tổng cộng 40,896 phiên bản; trong đó 37,963 phiên bản (92.83%) tải và giải nén thành công, 2,751 phiên bản (6.73%) là `unsupported` (không có TeX) và 182 phiên bản (0.45%) chưa giải quyết được (`unresolved`). [](#tbl-1-4-owner) tách theo từng thành viên.

```{code-cell} python
:tags: [remove-input]
:label: tbl-1-4-owner
:caption: Kết quả tải nguồn theo phiên bản của từng thành viên (nguồn m1_final_corpus.json)
rows = []
for o in OWNERS:
    s = m1["by_owner"][o]["colab_statistics_snapshot"]
    rows.append({
        "Thành viên": o,
        "Phiên bản khai báo": s["source_versions_expected"],
        "Thành công": s["source_versions_success"],
        "Unsupported": s["source_versions_unsupported"],
        "Chưa giải quyết": s["source_versions_unresolved"],
        "Tỷ lệ thành công (%)": round(s["source_success_rate"] * 100, 2),
    })
df = pd.DataFrame(rows)
tot = df.drop(columns=["Thành viên", "Tỷ lệ thành công (%)"]).sum()
tot["Thành viên"] = "Tổng"
tot["Tỷ lệ thành công (%)"] = round(tot["Thành công"] / tot["Phiên bản khai báo"] * 100, 2)
pd.concat([df, pd.DataFrame([tot])], ignore_index=True)
```

Đợt chạy S2-Batch (5000 bài mỗi người) ghi riêng số liệu cấp bài: 24,732 / 25,000 bài (98.93%) có đủ kết quả theo định nghĩa của `assignment`, trong đó phiên bản `unsupported` (PDF-only, DOCX) được tính là đã phủ vì chúng là kết quả hợp lệ. Định nghĩa chặt hơn của schema 1.2 chỉ đếm bài mà mọi phiên bản đều có nguồn TeX, nên cho tỷ lệ thấp hơn (khoảng 84% đến 92% tùy thành viên).

## 2. Nhận diện định dạng

arXiv trả nguồn ở nhiều dạng mà không ghi rõ định dạng trong tên file, vì vậy hàm `detect_source_kind` đọc vài byte đầu (magic bytes) để phân loại.

| Loại nguồn (source_kind) | Cách nhận diện | Xử lý |
|---|---|---|
| `tar_gzip` | Bắt đầu bằng `1f 8b` (gzip) và bên trong là tar | Giải nén tar, lọc file |
| `tar` | Tar không nén | Giải nén tar, lọc file |
| `gzip_tex` | Gzip của một file văn bản (bài chỉ có một file `.tex`) | Giải nén thành một file `.tex` |
| `tex` | Văn bản thuần, không phải trang HTML | Giữ nguyên làm file `.tex` |
| `pdf_only` | Bắt đầu bằng `%PDF-` (tác giả chỉ nộp PDF) | `unsupported`, giữ bản ghi rỗng |
| `other` | Không thuộc các loại trên (gồm gói DOCX) | DOCX được xác minh thì `unsupported`; còn lại là lỗi `invalid_source` |

Một file văn bản được coi là TeX khi không chứa byte NUL, giải mã được bằng UTF-8 hoặc latin-1, và không phải trang HTML (để tránh nhận nhầm trang báo lỗi thành mã nguồn). Bước này không bắt buộc phải có lệnh TeX ở đầu file, vì nhiều bài mở đầu bằng một đoạn chú thích dài; việc phân tích cú pháp TeX thuộc về Milestone 2.

## 3. Lọc file: giữ `.tex`/`.bib`, giữ lệnh hình trong TeX

Sau khi giải nén, mỗi file được phân vào một trong ba nhóm theo phần mở rộng (không phân biệt hoa thường):

| Nhóm | Phần mở rộng | Xử lý |
|---|---|---|
| Giữ lại | `.tex`, `.bib` | Lưu vào thư mục nguồn của phiên bản |
| Hình | `.png`, `.pdf`, `.jpg`, `.jpeg`, `.eps`, `.ps`, `.svg`, `.gif`, `.bmp`, `.tiff`, `.tif` | Bỏ, cộng vào `removed_figure_bytes` |
| Khác | mọi file còn lại (`.sty`, `.cls`, `.bbl`, `README`, …) | Bỏ, cộng vào `removed_other_bytes` |

Chỉ file hình bị bỏ, còn nội dung TeX được giữ nguyên: các lệnh `\begin{figure}`, `\includegraphics{...}`, `\caption{...}` vẫn còn trong file `.tex`. Milestone 2 cần các lệnh này để dựng nút Figure trong cây phân cấp, nên bước T3 không được sửa nội dung TeX.

File `.bbl` (danh mục tham khảo do BibTeX sinh sẵn) thuộc nhóm "khác" nên bị bỏ. Những bài chỉ khai báo tài liệu tham khảo bằng `\bibitem` ngay trong `.tex` thì vẫn giữ được, còn những bài chỉ có `.bbl` mà không có `.bib` sẽ không còn danh mục tham khảo dạng file. Ở Chương 2, những bài này mang nhãn `bbl_missing` (3,182 bài).

## 4. Phiên bản không có TeX vẫn được ghi nhận

Một phiên bản được ghi `status = "unsupported"` khi tác giả chỉ nộp PDF (`pdf_only`), nộp gói Word (DOCX), hoặc gói tar không chứa file `.tex` nào. Bản ghi này không bị bỏ qua: nó có `files = []`, `retained_source_bytes = 0` và `error = null`. Đề Milestone 2 yêu cầu phiên bản không có TeX phải được ghi là rỗng và tính vào độ phủ phiên bản, nên bản ghi rỗng này là cần thiết. Các trạng thái của `Result` sources:

| Trạng thái (status) | Khi nào |
|---|---|
| `success` | Có ít nhất một file `.tex` sau khi lọc |
| `unsupported` | PDF-only, DOCX, hoặc gói không có `.tex`; vẫn giữ bản ghi rỗng |
| `not_found` | arXiv xác nhận không có nguồn cho phiên bản này |
| `failed` | Lỗi mạng, lỗi định dạng (`invalid_source`), gói không an toàn (`unsafe_archive`) hoặc vượt giới hạn (`extract_limit`) |

## 5. Giải nén an toàn

Gói nguồn là dữ liệu do người ngoài tải lên, nên các handler không dùng `extractall` mà kiểm tra từng thành phần trước khi ghi ra đĩa:

- Đường dẫn: từ chối đường dẫn tuyệt đối, có `..`, dấu `\`, ký tự ổ đĩa Windows (`C:`) hoặc byte NUL, để không ghi được ra ngoài thư mục đích (lỗ hổng *path traversal*). Lỗi này được ghi là `unsafe_archive`.
- Loại thành phần: chỉ chấp nhận file thường và thư mục; symlink, hardlink và file thiết bị bị từ chối.
- Trùng lặp: hai thành phần cùng đường dẫn, hoặc một đường dẫn vừa là file vừa là thư mục, bị từ chối.
- Giới hạn kích thước (chống *zip bomb*): tối đa 10.000 thành phần, 200 MiB mỗi file và 1 GiB tổng sau giải nén. Dung lượng được đếm trong lúc đọc dữ liệu chứ không chỉ tin vào header. Vượt giới hạn thì ghi `extract_limit`.

Giải nén diễn ra trong thư mục tạm; chỉ khi thành công, thư mục kết quả mới được chuyển sang vị trí chính thức. Vì vậy một lần chạy lỗi không để lại nguồn dở dang.

## 6. Năm số đo dung lượng

Mỗi `Result` sources có năm số đo trong `metrics`:

| Trường | Ý nghĩa |
|---|---|
| `download_bytes` | Kích thước file tải về (đã nén) |
| `extracted_bytes_before_filter` | Tổng dung lượng mọi file sau giải nén, trước khi lọc |
| `retained_source_bytes` | Tổng dung lượng các file `.tex`/`.bib` được giữ |
| `removed_figure_bytes` | Tổng dung lượng file hình bị bỏ |
| `removed_other_bytes` | Tổng dung lượng các file khác bị bỏ |

Ba phần cuối phải cộng lại bằng dung lượng trước lọc:

$$
\text{extracted\_bytes\_before\_filter} = \text{retained\_source\_bytes} + \text{removed\_figure\_bytes} + \text{removed\_other\_bytes}
$$

Với phiên bản `unsupported`, dung lượng trước lọc và hai phần bị bỏ là `null` (không giải nén nên không đo), còn `retained_source_bytes = 0`. Bất biến này được bộ kiểm tra handoff kiểm trên mọi phiên bản có đủ số đo.

Các số đo ở mục này tính theo phiên bản, trên 37,963 phiên bản có số đo. Trung bình mỗi phiên bản có 5,543,702 byte (5.29 MiB) trước lọc và 322,043 byte (0.31 MiB) sau lọc, tức giảm 94.19% ([](#fig-1-4-size)). Phần lớn dung lượng của một gói nguồn là hình và file phụ trợ, trong khi văn bản TeX mà Milestone 2 cần chỉ chiếm phần nhỏ. Kích thước trung bình mỗi bài (cộng mọi phiên bản), theo đúng câu hỏi của đề, được trình bày ở mục 1.6.

```{code-cell} python
:tags: [remove-input]
:label: fig-1-4-size
:caption: Dung lượng nguồn trung bình mỗi phiên bản trước và sau khi lọc, theo từng thành viên (MiB)
before = [m1["by_owner"][o]["colab_statistics_snapshot"]["mean_extracted_bytes_before_filter"] / 2**20 for o in OWNERS]
after = [m1["by_owner"][o]["colab_statistics_snapshot"]["mean_retained_source_bytes"] / 2**20 for o in OWNERS]
fig = go.Figure()
fig.add_bar(name="Trước lọc", x=OWNERS, y=[round(v, 2) for v in before])
fig.add_bar(name="Sau lọc (.tex/.bib)", x=OWNERS, y=[round(v, 2) for v in after])
fig.update_layout(barmode="group", yaxis_title="MiB mỗi phiên bản", margin=dict(t=30, b=40))
unified.render_plotly(fig, height=360)
```

## 7. Tài liệu tham khảo

- arXiv. *Accessing arXiv source files*. https://info.arxiv.org/help/bulk_data.html
- arXiv. *Terms of Use for arXiv APIs*. https://info.arxiv.org/help/api/tou.html
- Python Software Foundation. *tarfile: Extraction filters*. https://docs.python.org/3/library/tarfile.html#extraction-filters

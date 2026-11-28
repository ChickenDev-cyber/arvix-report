---
kernelspec:
  name: python3
  display_name: Python 3
---
# 2.1 Phân tích cú pháp phân cấp

> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Phúc Khang (`@khang1108`) / Huy Hoàng (`@huynhhuyhoang2006@gmail.com`)

---

## 1. Mục tiêu và phạm vi

Mục tiêu của bước phân tích cú pháp phân cấp là chuyển đổi kho mã nguồn LaTeX của từng phiên bản bài báo (đầu ra Milestone 1) thành một cấu trúc cây phân cấp có kiểm chứng (`VersionHierarchy`). Quá trình này gồm hai công đoạn nối tiếp trong `arxiv_pipeline`:

1. **Tập hợp và giải quyết đường dẫn (`arxiv_pipeline.gathering`):** Xác định file gốc chứa `\documentclass`, mở rộng đệ quy các lệnh `\input`, `\include`, `\subfile` theo đúng thứ tự biên dịch, đồng thời ghi nhận các phiên bản không có mã nguồn TeX.
2. **Dựng cây phân cấp (`arxiv_pipeline.hierarchy`):** Quét luồng nội dung văn bản, dựng cây gồm nút gốc `document`, các nút vùng chứa (`section`, `subsection`, `subsubsection`, `paragraph`, `itemize`, `enumerate`, `item`) và các nút lá (`sentence`, `formula`, `figure`), loại trừ phần Tài liệu tham khảo nhưng giữ lại `Acknowledgements` và `Appendix`.

---

## 2. Xác định file gốc và hợp nhất nguồn TeX (`gathering`)

Một phiên bản bài báo trên arXiv thường chứa nhiều file `.tex` (chương, phụ lục, macro, hoặc bản nháp cũ). Module `arxiv_pipeline.gathering` thực hiện hợp nhất nguồn theo 3 bước:

### 2.1. Phân loại trạng thái nguồn (`SourceGatherer`)

`SourceTree` quét toàn bộ cây thư mục của phiên bản để liệt kê các file `.tex`, `.bib`, `.bbl`:
- Nếu không có file `.tex` nào (chỉ có PDF/DOCX), `SourceGatherer` trả về `status="empty_source"` với `merged_tex=""`. Phiên bản này không sinh nút nào nhưng vẫn được ghi nhận là **phiên bản rỗng** trong thống kê độ phủ.
- Nếu có `.tex` nhưng không có file nào chứa `\documentclass` hoặc `\documentstyle` (ngoài vùng comment), hệ thống trả về `status="no_root_file"`.

### 2.2. Xếp hạng ứng viên file gốc (`RootFinder`)

Để chọn đúng file LaTeX chính mà arXiv dùng để biên dịch, `RootFinder` quét tất cả file `.tex` trên bản sao đã che comment (`mask_comments`), tìm những file có `\documentclass` rồi sắp xếp theo khóa thứ tự từ điển 9 tiêu chí (`RootCandidate.sort_key()`) và chọn ứng viên nhỏ nhất:

$$K(p) = \bigl(k_1(p),\, k_2(p),\, k_3(p),\, k_4(p),\, k_5(p),\, k_6(p),\, -L_{\text{exp}}(p),\, d(p),\, p\bigr)$$

| Thành phần | Tiêu chí (`0` ưu tiên hơn `1`) | Ý nghĩa |
|---:|---|---|
| $k_1(p)$ | Không phải tệp tạm trình soạn thảo | Loại các tệp như `_region_.tex` (AUCTeX) |
| $k_2(p)$ | Có `\begin{document}` | Ưu tiên tài liệu hoàn chỉnh thay vì tệp cấu hình |
| $k_3(p)$ | Không phải lớp `standalone` / `subfiles` | Tránh chọn nhầm hình vẽ hoặc chương lẻ |
| $k_4(p)$ | Không bị tệp `.tex` khác `\input` / `\include` | File gốc là điểm vào cao nhất |
| $k_5(p)$ | Nằm ở thư mục gốc phiên bản (`"/" not in p`) | Tránh chọn bản sao trong thư mục con (`OldFiles/`, `doc/`) |
| $k_6(p)$ | Tên tệp phổ biến | Ưu tiên `main.tex`, `ms.tex`, `paper.tex`, `article.tex`, `manuscript.tex` |
| $-L_{\text{exp}}(p)$ | Âm độ dài sau mở rộng (`-merged_chars`) | Chọn tệp biên dịch ra nội dung đầy đủ nhất |
| $d(p), p$ | Độ sâu thư mục và tên đường dẫn | Phá hòa tất định khi các tiêu chí trên bằng nhau |

### 2.3. Mở rộng đệ quy `\input` / `\include` (`IncludeExpander`)

Từ `root_file` được chọn, `IncludeExpander` duyệt và chèn nội dung các tệp được gọi qua `\input`, `\include`, `\subfile`:
- **Thứ tự tìm tệp:** Thư mục chứa `root_file` $\rightarrow$ thư mục chứa tệp đang gọi $\rightarrow$ thư mục gốc nguồn.
- **Xử lý lệnh đặc biệt:** Dừng đọc tệp tại `\endinput`; với `\subfile{x}`, chỉ trích phần thân giữa `\begin{document}` và `\end{document}` để bỏ preamble trùng; hỗ trợ mở rộng macro đường dẫn đơn giản từ `\newcommand` và `\def`.
- **Chống lặp vô hạn:** Giới hạn độ sâu đệ quy `DEFAULT_MAX_DEPTH = 64`. Nếu tệp đích đã nằm trên ngăn xếp gọi hiện tại, hệ thống ghi nhận vào danh sách `cycles` và bỏ qua để tránh vòng lặp; các tệp không tìm thấy được ghi vào `missing`.

---

## 3. Dựng cây phân cấp tài liệu (`hierarchy`)

Sau khi có `GatheredSource` với `merged_tex`, `HierarchyBuilder` dựng cây `VersionHierarchy` theo luồng xử lý sau:

```{mermaid}
flowchart TD
    A["GatheredSource (merged_tex)"] --> B{"status == empty_source?"}
    B -->|Có| C["Trả về nodes = [] (phiên bản rỗng)"]
    B -->|Không| D["strip_comments + strip_comment_environments"]
    D --> E["extract_title + extract_document_body + clean_latex"]
    E --> F["Khởi tạo HierarchyStack (root: document, level 0)"]
    F --> G["Quét luồng bằng STREAM_DELIMITER_RE"]
    G --> H{"Loại delimiter?"}
    H -->|"section / subsection / ..."| I["Đóng stack có level >= mới, push_section"]
    H -->|"itemize / enumerate / item"| J["push_list_container / push_item / pop_list_container"]
    H -->|"thebibliography / References"| K["Bật cờ in_references (loại trừ nội dung)"]
    H -->|"block_math / figure / table"| L["Chuẩn hóa & add_leaf (formula / figure)"]
    H -->|"Văn xuôi (prose)"| M["process_prose_block -> add_leaf (sentence)"]
    I --> N["validate_version_hierarchy"]
    J --> N
    K --> N
    L --> N
    M --> N
    N --> O["VersionHierarchy"]
```

### 3.1. Tiền xử lý và lọc comment

Trước khi quét cấu trúc, `HierarchyBuilder.build_from_source` loại bỏ các chú thích LaTeX qua hai lớp:
- `strip_comments`: Xóa phần từ dấu `%` chưa escape (số lượng dấu `\` đứng trước là số chẵn) đến hết dòng, giữ nguyên `\%`.
- `strip_comment_environments`: Xóa toàn bộ vùng `\begin{comment}...\end{comment}`, nhưng **bảo toàn nguyên vẹn** nội dung bên trong `\begin{verbatim}`, `\begin{lstlisting}`, `\begin{minted}` và `\verb|...|`.

Tiếp theo, tiêu đề tài liệu được trích từ `\title[short]{long}` (`extract_title`), và phần thân văn bản được cắt từ `\begin{document}` đến `\end{document}` (`extract_document_body`) để tránh các khai báo macro ở preamble lọt vào cây nội dung.

### 3.2. Các loại nút và quy tắc ngăn xếp (`HierarchyStack`)

`HierarchyStack` duy trì ngăn xếp các vùng chứa đang mở để gán `parent_temp_id` cho mọi phần tử mới:

| Nhóm | Loại nút (`ElementKind`) | Mức (`level`) / Vai trò | Quy tắc xử lý |
|---|---|---|---|
| Gốc | `document` | `0` (gốc duy nhất) | Khởi tạo mặc định, `parent_temp_id = None` |
| Phân mục | `section` (gồm cả `chapter`), `subsection`, `subsubsection`, `paragraph` | `2` (hoặc `1` cho `chapter`), `3`, `4`, `5` | Khi mở mục mới ở mức $L$, tự động `pop` các mục/item có `level >= L` (dừng trước `document`) |
| Danh sách | `itemize`, `enumerate`, `item` | `parent_level + 10` và `+ 1` | `item` mới tự đóng `item` anh em trước đó; `\end{itemize}` / `\end{enumerate}` kiểm tra tồn tại trên stack trước khi `pop` |
| Nút lá | `sentence`, `formula`, `figure` | Nút tận cùng (không đẩy vào stack) | Gắn trực tiếp vào `current_parent_id` |

Ba loại nút lá được tạo bởi `leaf_parser`:
- **`sentence`:** Văn bản xuôi giữa các dấu phân cách cấu trúc được lọc nhãn/wrapper (`strip_prose_markup`), chuẩn hóa định dạng và tách câu bằng `process_prose_block`.
- **`formula`:** Các công thức khối (`equation`, `align`, `gather`, `multline`, `eqnarray`, `flalign`, `alignat`, `displaymath`, `\[...\]`, `$$...$$`) được đưa về dạng chuẩn `\begin{equation}...\end{equation}`.
- **`figure`:** Các môi trường `figure`, `table`, `wrapfigure`, `wraptable`, `tabular`, `longtable` (kể cả dạng có dấu `*`) được gộp chung vào `kind="figure"` sau khi làm sạch lệnh dàn trang.

### 3.3. Loại trừ Tài liệu tham khảo và giữ Phụ lục

`STREAM_DELIMITER_RE` nhận diện các khối tham khảo để loại trừ khỏi cây nội dung:
- Các môi trường `\begin{thebibliography}`, `bibdiv`, `biblist` và các lệnh `\bibliography`, `\bibliographystyle`, `\addbibresource`, `\printbibliography`, `\putbib`.
- Các mục `\section{...}` có tiêu đề sau chuẩn hóa thuộc `REFERENCE_TITLES` (`references`, `reference`, `bibliography`, `works cited`, `literature cited`) sẽ bật cờ `in_references = True` để bỏ qua nội dung bên trong.
- Khi gặp `\appendix` hoặc một `\section` thông thường mới, cờ `in_references` được tắt để **giữ lại đầy đủ** phần `Acknowledgements` và các phụ lục (`Appendix`).

---

## 4. Kiểm tra toàn vẹn cây (`validate_version_hierarchy`)

Mỗi `VersionHierarchy` sinh ra bắt buộc đi qua hàm `validate_version_hierarchy` với 6 ràng buộc:

1. Nếu `nodes` rỗng, cây được xem là hợp lệ cho phiên bản không có TeX (`empty_source`).
2. Nếu `nodes` không rỗng, phải có **đúng một** nút có `parent_temp_id = None` và `kind == "document"`.
3. Mọi `temp_id` trong cùng phiên bản phải không rỗng và duy nhất.
4. Mọi `kind` phải thuộc tập hợp `ElementKind` hợp lệ.
5. Mọi nút khác gốc phải có `parent_temp_id` trỏ tới một nút tồn tại trong cây.
6. Đồ thị cha–con không được chứa chu trình (kiểm tra bằng duyệt ngược tới gốc cho từng nút).

---

## 5. Hợp nhất thư mục tham khảo và 4 rào chắn an toàn (`arxiv_pipeline.bibtex`)

Song song với việc dựng cây nội dung, module `arxiv_pipeline.bibtex` trích xuất tài liệu tham khảo từ ba nguồn (`extract_from_gathered_source`): các file `.bib` được khai báo, khối `\begin{thebibliography}` / `\thebibliography` nội tuyến (`\bibitem`), và khối AMSRefs (`\begin{biblist}` / `\bib`). Sau đó `unify_entries` hợp nhất qua mọi phiên bản của bài báo theo 4 rào chắn an toàn để chống trộn nhầm các tài liệu khác nhau:

1. **Chặn trùng khóa trong cùng phiên bản (`ambiguous` / `duplicate_key_different_reference`):** Nếu cùng một `citation_key` xuất hiện nhiều lần trong cùng một phiên bản nhưng khác DOI hoặc khác tiêu đề chuẩn hóa, hệ thống không gộp theo khóa và không thực hiện đổi tên `\cite{}` cho khóa nhập nhằng đó.
2. **Bất biến DOI (`doi != candidate_doi`):** Hai mục có DOI khác nhau tuyệt đối không được gộp chung kể cả khi tiêu đề gần giống; bản ghi không có DOI không được dùng làm cầu nối giữa hai DOI xung đột.
3. **Kiểm tra độ tin cậy tiêu đề (`is_reliable_title`):** Chỉ cho phép dùng `title:` làm khóa định danh gộp khi tiêu đề đạt độ tin cậy, tránh gộp nhầm các tiêu đề ngắn hoặc chung chung.
4. **Hợp nhất đơn trị (`len(candidates) == 1`):** Chỉ thực hiện hợp nhất trường (hợp danh sách tác giả không trùng, điền bổ sung `year`/`doi`/`journal`/`url`) khi chỉ có **duy nhất một** mục chuẩn ứng viên khớp; nếu có nhiều ứng viên cạnh tranh thì giữ tách biệt thành mục mới.

---

## 6. Kết quả thực nghiệm toàn nhóm (25.000 bài báo)

Từ dữ liệu hợp nhất `m2_unified_summary.json` trên toàn bộ **25.000 bài báo** (`40.896` phiên bản khai báo), công đoạn phân tích cú pháp phân cấp đạt:

| Chỉ số toàn nhóm | Giá trị | Ghi chú |
|---|---:|---|
| Số bài báo dựng được cây | **22.961** (`91,84%`) | `2.039` bài rỗng hoàn toàn (`8,16%`) |
| Số phiên bản dựng được cây | **37.967 / 40.896** (`92,84%`) | Trung bình `426,3` cạnh/phiên bản có cây |
| Phần tử duy nhất (`elements`) | **11.098.189** | Giảm `31,59%` từ `16.223.222` phần tử thô |
| Tổng số cạnh cha–con (`hierarchy`) | **16.185.255** | Kết nối toàn bộ 11 loại nút `ElementKind` |
| Tổng mục `bibtex` sau hợp nhất | **975.674** | Trên `19.204` bài có thư mục tham khảo |

Riêng trên dải của **Mẫn Nhi** (`2501.12642` – `2501.17641`): `4.544` bài dựng được cây (`90,88%`), `456` bài rỗng, `7.592 / 8.251` phiên bản có cây (`92,01%`), `2.221.136` phần tử duy nhất (giảm `32,22%` từ `3.276.789`), `3.269.197` cạnh `hierarchy`, và `195.360` mục `bibtex` trên `3.819` bài.

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

m2 = unified.load_json("m2_unified_summary")
kinds = m2["element_kind_distribution"]
k_labels = list(kinds.keys())
k_vals = [kinds[k] for k in k_labels]

owners = ["huynh-nhi", "man-nhi", "hoang", "trong", "khang"]
v_rate = [round(m2["by_owner"][o]["parsed_version_rate"] * 100, 2) for o in owners]
edges = [m2["by_owner"][o]["hierarchy_edges"] for o in owners]

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=(
        f"Phân bố 11 loại nút elements ({m2['total_unique_elements']:,} nút)",
        f"Số cạnh hierarchy & tỷ lệ phiên bản có cây ({m2['total_hierarchy_edges']:,} cạnh)",
    ),
)
fig.add_trace(
    go.Bar(name="elements", x=k_labels, y=k_vals, marker_color="#2563eb", text=[f"{v:,}" for v in k_vals], textposition="outside"),
    row=1, col=1,
)
fig.add_trace(
    go.Bar(name="Cạnh hierarchy", x=owners, y=edges, marker_color="#0ea5e9", text=[f"{v/1e6:.2f}M" for v in edges], textposition="outside"),
    row=1, col=2,
)
fig.update_yaxes(type="log", title_text="Số lượng (thang log)", row=1, col=1)
fig.update_yaxes(title_text="Số cạnh hierarchy", row=1, col=2)
fig.update_xaxes(tickangle=-25, row=1, col=1)
fig.update_layout(
    title="Kết quả phân tích cú pháp phân cấp toàn nhóm (25.000 bài)",
    showlegend=False,
    template="plotly_white",
)
unified.render_plotly(fig, height=420)
```

---

## 7. Tài liệu tham khảo

- Đề bài Milestone 2: [Parsing Statement](https://hcmus-cs-ta.github.io/lab-book/intro-ds/statement/parsing)
- Mã nguồn `arxiv_pipeline.gathering` (`root_finder.py`, `expander.py`, `service.py`, `latex_scan.py`), `arxiv_pipeline.hierarchy` (`builder.py`, `stack.py`, `leaf_parser.py`, `latex_utils.py`, `validation.py`), và `arxiv_pipeline.bibtex` (`parser.py`, `deduplicator.py`, `service.py`).

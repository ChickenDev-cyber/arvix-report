# 1.9 Hạn chế và cơ chế chạy tiếp

> **Người phụ trách:** Mẫn Nhi (`@NhiNgo49`)  
> **Reviewer:** Hoàng (`huynhhuyhoang2006@gmail.com`)

---

## 1. Hạn chế của nguồn dữ liệu và quá trình thu thập

1. **Phụ thuộc dịch vụ bên ngoài.** Discovery và ngày nộp v1 phụ thuộc arXiv API; metadata phụ thuộc OAI-PMH; references phụ thuộc Semantic Scholar. Lỗi mạng, HTTP 429, lỗi server hoặc payload thay đổi có thể làm một task thành `partial`/`failed`.
2. **Nguồn references không phải kho lưu trữ đầy đủ tuyệt đối.** T4 chỉ thu được những mục Semantic Scholar trả về tại thời điểm truy vấn. Số mục có arXiv ID là một tập con của `raw_references`; không nên diễn giải số này thành tổng số trích dẫn của bài báo.
3. **Metadata có thể thiếu.** Ngày nộp của một reference chỉ được bổ sung nếu arXiv API trả về ID tương ứng và trường `published` hợp lệ. Module ghi nhận trường thiếu thay vì suy đoán.
4. **Discovery cần xác minh đầy đủ.** ID không xuất hiện trong phản hồi chưa đầy đủ không được xem là không tồn tại. Điều này làm tăng request khi phải xác minh riêng các ID còn mơ hồ.
5. **Giới hạn trang và tốc độ API.** T4 mặc định giới hạn 50 trang mới trong một lượt và phải tuân thủ khoảng chờ/rate limit của từng nguồn. Một bài có nhiều references hoặc gặp 429 có thể cần nhiều lần chạy.
6. **Benchmark phải có phạm vi rõ ràng.** Thời gian, RAM và dung lượng phụ thuộc môi trường, cache mode, số bài và trạng thái mạng. Không dùng benchmark mock hoặc máy cá nhân thay cho kết quả Colab CPU chính thức nếu yêu cầu môn học quy định môi trường đó.

## 2. Cơ chế phục hồi

T5 quản lý trạng thái task bằng SQLite theo `run_id`. Runner dùng `OutputLock`, khôi phục trạng thái và artifact đã xuất, kiểm tra task có thể dùng lại, sau đó chỉ chạy lại task cần thiết. Các kết quả được xác nhận mới được ghi vào accepted results và event log.

T1 Discovery hỗ trợ checkpoint theo batch khi được runner truyền store. Các batch đã phân loại được giữ lại; batch chưa xác minh có thể tiếp tục mà không phải làm lại toàn bộ dải.

T4 References lưu checkpoint sau mỗi trang hợp lệ, cache ngày nộp arXiv và lịch chờ API. Khi khởi động lại cùng run, module đọc các trang đã lưu và tiếp tục từ offset tiếp theo. Nếu checkpoint bị hỏng hoặc không khớp owner/ID/page size/fields, module báo lỗi thay vì bỏ qua dữ liệu lỗi.

## 3. Hướng cải tiến và tối ưu đã áp dụng

- **Dò biên tháng theo tìm kiếm nhị phân $O(\log K)$:** Với các dải ID xuyên ranh giới tháng (`trong` quét `83.142` ID, `khang` quét `80.870` ID), việc quét tuyến tính $O(K)$ toàn bộ phần cuối tháng gây lãng phí hàng nghìn request. Chuyển sang dò tìm biên cuối tháng theo thuật toán tìm kiếm nhị phân $O(\log K)$ giúp giảm mạnh số lượt gọi Atom API.
- **Chuyển sang Semantic Scholar POST batch (`S2 POST batch`):** Thay cho truy vấn đơn lẻ, cơ chế gọi lô giúp giảm thời gian chạy toàn bộ 5.000 bài/người xuống còn **`16,57` – `22,77` giờ** (giảm **`31,69%` – `47,72%`** so với mốc `26,02` – `35,48` giờ ngày 06/11), tổng `74.323` lượt gọi HTTP và hoàn tất `24.732 / 25.000` bài (`98,93%`).
- **Tối ưu retry và kiểm toán:** Theo dõi tỷ lệ `unresolved`, `partial`, `failed` theo nguồn và theo run; chỉ chạy lại các task có lỗi retryable sau thời gian chờ phù hợp, không retry lỗi dữ liệu không hợp lệ hoặc ID sai.

## 4. Tình trạng xác nhận trên dữ liệu thật (25.000 bài)

Trên dữ liệu hợp nhất cuối cùng (`m1_final_corpus.json` và `m1_batch_summary.json`):
- **Toàn nhóm (25.000 bài):** Discovery hoàn tất `179.012` ứng viên $\rightarrow$ `25.000` bài; `40.896` phiên bản khai báo; `466.763` arXiv references (`99,77%` đủ metadata).
- **Riêng dải Mẫn Nhi (`man-nhi`):** `5.000/5.000` bài Discovery; `4.951/5.000` bài hoàn tất theo quy ước bài tập (`99,02%`); `4.995` bài hoàn tất truy vấn References (`78.771` arXiv refs trong `m1_batch_summary.json`, `78.635` arXiv refs xuất sang Parquet cuối với `100%` đủ metadata).

*(Lưu ý: các file `statistics/baseline-001.json` và `benchmarks/baseline-001.json` trong thư mục gốc của repo code vẫn giữ `is_mock=true` để phục vụ kiểm thử tự động và không được trộn vào kết quả thực nghiệm.)*


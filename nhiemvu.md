Tôi là TV1 của dự án FPTUniQA. Tôi đã hoàn thành bước thu thập và đóng gói dữ liệu thô.

File ZIP:
H:\PythonProject\FPTUniQA\fptuniqa_raw_crawler_starter\fpt_raw_crawler\fptuniqa_raw_data_20260921.zip

Nhiệm vụ của bạn:
1. Đọc README và kiểm tra cấu trúc project hiện tại trước khi thay đổi.
2. Giải nén hoặc sao chép dữ liệu từ ZIP vào vị trí raw data phù hợp trong project.
3. Không chỉnh sửa, ghi đè hoặc xóa dữ liệu raw gốc.
4. Dùng crawl_manifest.jsonl để truy xuất nguồn và trạng thái crawl.
5. Thực hiện cleaning, normalization, metadata extraction, chunking và tạo corpus trong các thư mục processed/interim phù hợp với schema hiện có.
6. Phân loại nội dung theo các chủ đề như tuyển sinh, học phí, học bổng, nhập học, campus, ngành học và năm/khóa nếu nguồn có nêu rõ.
7. Không tự suy diễn thông tin khi tài liệu không hỗ trợ; ghi nhận trường hợp thiếu hoặc mơ hồ.
8. Kiểm tra nội dung trùng lặp, trang lỗi, trang ít nội dung và lỗi trích xuất.
9. Thực hiện coverage audit: xác định chủ đề nào có dữ liệu, chủ đề nào còn thiếu và đề xuất URL hoặc nguồn chính thức cần thu thập thêm.
10. Báo cáo các file đầu ra đã tạo, số lượng tài liệu/chunks, lỗi phát hiện và những việc TV1 cần bổ sung.

Thông tin kiểm kê ban đầu:
- HTTP 200: 219 bản ghi
- HTTP 404: 7 bản ghi
- Seed URL thành công: 13/13
- HTML files: 170
- PDF files: 0
- ZIP: 5.71 MB, 173 entries

Không coi các số liệu kiểm kê này là bằng chứng rằng dữ liệu đã đầy đủ hoặc đáp ứng mọi câu hỏi của hệ thống.
Hãy bắt đầu bằng việc kiểm tra cấu trúc dữ liệu và báo cáo kế hoạch xử lý trước khi sửa các file quan trọng.
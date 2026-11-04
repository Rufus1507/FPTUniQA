# NHẬT KÝ ĐỐI CHIẾU MÂU THUẪN THỰC NGHIỆM (DISCREPANCY LOG)

> **Dự án:** FPTUniQA — Hệ thống Hỏi đáp Quy chế Đào tạo và Biểu phí Đại học FPT  
> **Vai trò:** Kiểm toán viên Thực nghiệm Độc lập (Experiment Auditor)  
> **Thời điểm lập:** 04/11/2026  
> **Mã Commit:** `develop` (HEAD) | **Môi trường:** Python 3.10.11, Windows 11 Enterprise

---

## 1. Mâu thuẫn Mẫu số Recall@5 (Doc ID & Equiv) trong Bảng Ablation
- **Hiện tượng mâu thuẫn:** Các tỷ lệ Recall@5 trong báo cáo cũ ghi: C1=26,92%, C2=46,15%, C3=61,54%, C3p=57,69%, C4-hard=47,12%, C4-soft=50,00%, C5=34,62%, C6=34,62%. Nếu chia cho $N=100$ thì các số này không thể xuất hiện (bội số của 1/100 là 0.01).
- **Kết quả điều tra thực nghiệm:**
  - File `data/evaluation/benchmark_v2/retrieval_gold.json` có tổng cộng 117 câu hỏi.
  - Tuy nhiên, trong tập 100 câu hỏi chạy Ablation Benchmark V2, **chỉ có đúng 26 câu hỏi** có mặt trong `retrieval_gold.json` (74 câu còn lại là 63 câu học phí tra bảng SSOT và 11 câu OOD ngoài phạm vi).
  - Code `scripts/aggregate_ablation.py` (dòng 301-321) chỉ tính `recalls.append(...)` khi `q_id in ret_gold`.
  - Do đó, **mẫu số thực tế của Recall@5 là $N = 26$** (hoặc $N = 52$ ở C4-hard và C6 do file log cũ bị ghi đúp 2 lần nối tiếp).
  - Kiểm chứng phép chia chính xác:
    + C1: $7 / 26 = 0,26923 \approx 26,92\%$ (Doc ID), $11 / 26 = 0,42308 \approx 42,31\%$ (Equiv).
    + C2: $12 / 26 = 0,46154 \approx 46,15\%$ (Doc ID), $14,5 / 26 = 0,55769 \approx 55,77\%$ (Equiv).
    + C3: $16 / 26 = 0,61538 \approx 61,54\%$ (Doc ID), $17 / 26 = 0,65385 \approx 65,38\%$ (Equiv).
    + C3p: $15 / 26 = 0,57692 \approx 57,69\%$ (Doc ID), $17 / 26 = 0,65385 \approx 65,38\%$ (Equiv).
    + C4-hard (dedup): $12 / 26 = 0,46154 \approx 46,15\%$ (Doc ID), $16 / 26 = 0,61538 \approx 61,54\%$ (Equiv). (Nếu tính cả 52 câu bị lặp là $24,5 / 52 = 47,12\%$).
    + C4-soft: $13 / 26 = 0,50000 = 50,00\%$ (Doc ID), $15 / 26 = 0,57692 \approx 57,69\%$ (Equiv).
    + C5: $9 / 26 = 0,34615 \approx 34,62\%$ (Doc ID), $9,5 / 26 = 0,36538 \approx 36,54\%$ (Equiv).
    + C6 (dedup): $9 / 26 = 0,34615 \approx 34,62\%$ (Doc ID), $9,5 / 26 = 0,36538 \approx 36,54\%$ (Equiv).
- **Cách xử lý chuẩn hóa:** Trong Báo cáo v3, nêu rõ mẫu số là $N=26$ câu hỏi có nhãn văn bản quy chế, dedup triệt để C4-hard và C6 về đúng 26 câu, ghi rõ số câu trúng ($k/26$) bên cạnh tỷ lệ phần trăm.

---

## 2. Lệch pha giữa Bảng Bootstrap và Bảng Ablation (C3p vs C3)
- **Hiện tượng mâu thuẫn:** Bảng Bootstrap ghi $\Delta\text{recall} = -0,0100$ và $\Delta\text{MRR} = -0,0133$, trong khi Bảng Ablation ghi giảm từ 61,54% xuống 57,69% ($\Delta = -3,85\%$) và MRR từ 0,5897 xuống 0,5385 ($\Delta = -0,0512$).
- **Kết quả điều tra thực nghiệm:**
  - Trong `scripts/aggregate_ablation.py` (dòng 329-334 và dòng 445-452), mảng lưu điểm `per_query_scores` lưu kết quả cho **tất cả 100 câu hỏi**. Với 74 câu hỏi không có nhãn retrieval gold, code gán mặc định `recall = 0.0` và `mrr = 0.0`.
  - Khi chạy `paired_bootstrap_test`, hàm tính trung bình vi mô trên cả 100 câu hỏi:
    $$\Delta\mu_{\text{recall}} = \frac{15 - 16}{100} = -0,0100$$
    $$\Delta\mu_{\text{MRR}} = \frac{\sum \text{MRR}_{3p} - \sum \text{MRR}_3}{100} = -0,0133$$
  - Khi quy đổi về mẫu số 26 câu retrieval:
    $$-0,0100 \times \frac{100}{26} = -0,03846 \approx -3,85\%$$
    $$-0,0133 \times \frac{100}{26} = -0,05115 \approx -0,0512$$
- **Cách xử lý chuẩn hóa:** Đã tính lại Bootstrap với $B=10.000$ lặp, seed 42 cố định trên đúng 26 câu retrieval:
  - $\Delta\text{recall} = -0,0385$, 95% CI: $[-0,0962, +0,0000]$, $p = 0,2628$ (không suy giảm có ý nghĩa).
  - $\Delta\text{equiv\_recall} = 0,0000$, 95% CI: $[0,0000, 0,0000]$, $p = 1,0000$ (bảo toàn tuyệt đối 17/17 câu).
  - $\Delta\text{latency} = -2.150,20 \text{ ms}$, 95% CI: $[-2.611,78, -1.677,46]$, $p < 0,0001$ (giảm độ trễ có ý nghĩa rất cao).

---

## 3. Khảo sát Tính tất định của Song song hóa (C3 vs C3p)
- **Hiện tượng:** Cần làm rõ vì sao song song hóa C3p lại làm thay đổi top-5 so với tuần tự C3 trong log cũ.
- **Kết quả đo thực nghiệm:** Chạy lặp lại 5 lần độc lập cho C3 và 5 lần độc lập cho C3p trên 26 câu vàng (`experiments/audit/test_repeatability_c3_c3p.py`):
  - C3 chạy 5 lần: 0 / 26 câu không tất định (100% tái lập).
  - C3p chạy 5 lần: 0 / 26 câu không tất định (100% tái lập).
  - So sánh trực tiếp C3p vs C3 hiện tại: 26 / 26 câu top-5 trùng khớp hoàn toàn.
- **Nguyên nhân trong log cũ:**
  - Đối chiếu file log cũ (`c3_hybrid.jsonl` vs `c3p_hybrid_parallel.jsonl`) phát hiện có 2 câu bị lệch hit Doc ID: `V2_B05_002` và `V2_B05_003`.
  - Phân tích chi tiết: Ở 2 câu này, khi gộp RRF đa luồng, các chunk có cùng điểm số RRF bị hoán đổi vị trí giải hòa (*tie-breaking*), đẩy chunk `doc_fpt_k22_0299` vào thay thế cho `doc_fpt_k17_0605`. Cả hai chunk này đều thuộc cùng một nhóm điều khoản quy chế tương đương (`equiv_group`). Do đó Recall Doc ID bị giảm nhẹ nhưng Recall Equiv được bảo toàn 100%.

---

## 4. Bản chất và Chiều đọc của Chỉ số Wrong-Cohort Rate (0/6 vs 6/6)
- **Định nghĩa mã nguồn:** Trong `FPTUniQA/evaluation/retrieval_metrics.py`, `compute_wrong_cohort_rate` trả về `1.0` nếu trong top-5 có **bất kỳ tài liệu nào thuộc khóa khác** với `expected_cohorts`, và `0.0` nếu 100% tài liệu top-5 đều đúng khóa (hoặc là tài liệu chung không gắn khóa). Chiều đọc: **0.00% là Tốt (không vi phạm), 100% là Xấu (vi phạm)**.
- **Giải thích vì sao C1/C2 = 0/6 trong khi C3 = 6/6:**
  - Trích xuất bảng 6 câu có định danh khóa (`experiments/audit/wrong_cohort_detailed_table.json`):
    + C1 (BM25): Chỉ bắt từ khóa chính xác của câu hỏi (chứa "K17" hoặc "K18"), cả 5 chunk top-5 đều là chunk của chính khóa đó $\rightarrow$ vi phạm = 0/6.
    + C2 (FAISS Dense): Do độ tương đồng ngữ nghĩa hẹp, chỉ gom các chunk của chính khóa đó $\rightarrow$ vi phạm = 0/6.
    + C3 (Hybrid RRF): Kết hợp BM25 và FAISS, mở rộng ứng viên top-10 trước khi chọn 5. Do quy chế các khóa K17, K18, K20 có nội dung ngữ nghĩa học phí/học vụ giống nhau, RRF kéo các chunk K20, K21 vào vị trí 4 và 5 $\rightarrow$ cả 6 câu đều có ít nhất 1 chunk khóa khác lọt vào top-5 $\rightarrow$ vi phạm = 6/6 (100%).
    + C4-hard (Hard Filter): Ép lọc cứng `cohort == detected_cohort`, loại bỏ 100% chunk khóa khác $\rightarrow$ vi phạm trở về 0/6 (0,00%).
    + C4-soft (Soft Boost): Chỉ tăng trọng số mềm chứ không loại bỏ, các chunk khóa khác vẫn còn bám ở vị trí 4, 5 ở 5/6 câu $\rightarrow$ vi phạm = 5/6 (83,33%).

---

## 5. Phân tích Nguyên nhân C4-hard Tụt Recall (61,54% xuống 46,15%)
- **Số liệu kiểm toán:** Có chính xác **5 câu hỏi** bị mất hit Doc ID khi chuyển từ C3 sang C4-hard: `V2_B05_002`, `V2_B05_003`, `V2_B07_002`, `V2_B07_005`, `V2_B07_006`.
- **Phân loại nguyên nhân:**
  1. **80% (4 / 5 ca - V2_B05_002, B05_003, B07_005, B07_006):** Là hiện tượng trượt giả do tài liệu tương đương (`EquivHit = 1.0`). Khi lọc cứng theo khóa, hệ thống giữ lại tài liệu của khóa chỉ định, vốn có cùng điều khoản quy chế nhưng khác mã Doc ID so với nhãn vàng đơn lẻ ban đầu.
  2. **20% (1 / 5 ca - V2_B07_002):** Lỗi cascading từ Parser. Parser nhận diện nhầm alias thực thể, khiến Hard Filter gạt bỏ tài liệu đúng và kéo các tài liệu không liên quan vào top-5 (`EquivHit = 0.0`).

---

## 6. Xác nhận Đường Retrieval C5 vs C6 và Kiểm định Faithfulness
- **Đường truy xuất:** Kiểm tra 100 câu hỏi giữa C5 và C6, có **95 / 100 câu hỏi có top-5 doc_ids HOÀN TOÀN TRÙNG KHỚP NHAU Y HỆT** (vì 2 cấu hình cùng sử dụng chung module Hybrid Retrieval).
- **Kiểm định Faithfulness C6 vs C5:**
  - Mean F5 = 0,8656, Mean F6 = 0,8291 (tính trên các câu hỏi không đúp).
  - Chênh lệch $\Delta\mu = -0,0365$, khoảng tin cậy 95% CI: $[-0,0932, +0,0148]$, $p = 0,1892 \ge 0,05$.
  - **Kết luận kiểm toán:** Không có bằng chứng thống kê cho thấy Semantic Parser của C6 làm tăng Faithfulness so với C5 trên tập benchmark này.

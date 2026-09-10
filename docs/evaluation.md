# 📊 Phương Pháp Đo Lường & Đánh Giá Thực Nghiệm (Evaluation Specs)

## 1. Các chỉ số tầng Retrieval

### 1.1. Hit Rate @ K (Hit@K)
Tỷ lệ các câu hỏi mà trong danh sách Top-K tài liệu trả về có chứa ít nhất 1 tài liệu đúng (Ground Truth):
$$\text{Hit@K} = \frac{1}{|Q|} \sum_{q \in Q} \mathbb{I}(\text{TopK}(q) \cap G_q \neq \emptyset)$$

### 1.2. Mean Reciprocal Rank (MRR)
Nghịch đảo của vị trí xuất hiện đầu tiên của tài liệu đúng trong danh sách kết quả:
$$\text{MRR} = \frac{1}{|Q|} \sum_{q \in Q} \frac{1}{\text{rank}_1(q)}$$

### 1.3. Normalized Discounted Cumulative Gain (NDCG@K)
Đánh giá chất lượng sắp xếp thứ bậc, tài liệu liên quan càng ở trên đầu thì điểm càng cao:
$$\text{DCG@K} = \sum_{i=1}^K \frac{rel_i}{\log_2(i + 1)}, \quad \text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$

---

## 2. Các chỉ số tầng Generation & Chống ảo giác

### 2.1. Faithfulness (Độ trung thực)
Tỷ lệ các nhận định/thông tin trong câu trả lời có thể được truy nguyên trực tiếp từ văn bản ngữ cảnh được cung cấp.
$$\text{Faithfulness} = \frac{\text{Số nhận định có bằng chứng trong Context}}{\text{Tổng số nhận định trong câu trả lời}}$$

### 2.2. OOD Rejection Accuracy (Độ chính xác từ chối ngoài miền)
Khả năng hệ thống từ chối các câu hỏi không liên quan đến quy chế đại học (nấu ăn, bóng đá, thời tiết...):
$$\text{OOD Rejection Acc} = \frac{\text{Số câu hỏi OOD được từ chối thành công}}{\text{Tổng số câu hỏi OOD kiểm thử}}$$

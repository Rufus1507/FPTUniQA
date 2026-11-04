# KẾT QUẢ THỰC NGHIỆM: TÁC ĐỘNG CỦA CROSS-ENCODER RERANKER TRÊN C4-HARD

Đánh giá trên tập Canonical N=117 câu hỏi.

| Cấu hình | Recall@5 (Doc ID) | Recall@5 (Equiv) | MRR@5 | Wrong-Cohort Rate | Latency p50 / p95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **C4-hard (No Rerank - Baseline)** | 65.81% | 67.52% | 0.6597 | 0.00% | 80.1 / 95.0 |
| **C4-hard + CrossEncoder (cand_k=15)** | 47.44% | 48.72% | 0.4105 | 0.00% | 5435.7 / 6196.6 |
| **C4-hard + CrossEncoder (cand_k=25)** | 44.02% | 44.44% | 0.3707 | 0.00% | 7613.7 / 9236.0 |
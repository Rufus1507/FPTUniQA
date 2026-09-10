"""Script thực thi đo lường toàn bộ bộ test khoa học và xuất báo cáo."""

from pathlib import Path
from university_qa.evaluation.evaluator import RAGEvaluator
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.utils.config import load_config
from university_qa.utils.io import read_jsonl, write_json
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.evaluate")


def main():
    config = load_config(config_path="configs/evaluation.yaml")
    questions_path = config.get("data", {}).get("questions_path", "data/evaluation/questions.jsonl")
    ood_path = config.get("data", {}).get("ood_questions_path", "data/evaluation/ood_questions.jsonl")

    logger.info("Khởi tạo RAG Pipeline và tải Corpus...")
    pipeline = RAGPipeline()
    pipeline.load_corpus()

    evaluator = RAGEvaluator(pipeline)

    logger.info(f"Nạp tập câu hỏi kiểm thử từ: {questions_path}")
    questions = read_jsonl(questions_path)

    logger.info("Đang tính toán các chỉ số Retrieval (Hit@K, Recall@K, MRR, NDCG)...")
    retrieval_metrics = evaluator.evaluate_retrieval(questions, k_list=[1, 3, 5])

    ood_questions = read_jsonl(ood_path)
    logger.info("Đang kiểm tra khả năng từ chối câu hỏi ngoài miền (OOD)...")
    ood_metrics = evaluator.evaluate_ood(ood_questions)

    final_report = {
        "dataset_size": len(questions),
        "ood_dataset_size": len(ood_questions),
        "retrieval_metrics": retrieval_metrics,
        "ood_metrics": ood_metrics,
    }

    report_path = Path("experiments/baseline/evaluation_report.json")
    write_json(final_report, report_path)
    logger.info(f"Báo cáo kết quả đã được ghi tại: {report_path}")

    print("\n" + "=" * 50)
    print("           KẾT QUẢ ĐÁNH GIÁ THỰC NGHIỆM")
    print("=" * 50)
    for k, v in retrieval_metrics.items():
        print(f"  {k:15s}: {v}")
    for k, v in ood_metrics.items():
        print(f"  {k:15s}: {v}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()

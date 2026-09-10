"""Script chạy thử nghiệm pipeline RAG trực tiếp từ Terminal."""

import argparse
from university_qa.pipeline.rag_pipeline import RAGPipeline
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.run_pipeline")


def main():
    parser = argparse.ArgumentParser(description="Chạy thử nghiệm University RAG Pipeline")
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="Sinh viên được đăng ký tối đa bao nhiêu tín chỉ trong một học kỳ?",
        help="Câu hỏi cần tra cứu",
    )
    parser.add_argument("--top_k", "-k", type=int, default=3, help="Số tài liệu trả về")
    args = parser.parse_args()

    pipeline = RAGPipeline()
    pipeline.load_corpus()

    print("\n" + "=" * 60)
    print(f"[*] CÂU HỎI: {args.query}")
    print("=" * 60)

    result = pipeline.run(args.query, top_k=args.top_k)

    print(f"\n[>] Ý ĐỊNH: {result['intent'].upper()}")
    print(f"\n[>] CÂU TRẢ LỜI:\n{result['answer']}")

    print("\n[>] NGUỒN TRÍCH DẪN (CITATIONS):")
    for cit in result["citations"]:
        print(f"  - [{cit.get('doc_id')}] {cit.get('title')} ({cit.get('section', '')})")

    print("\n[>] CÁC TÀI LIỆU TOP LIÊN QUAN:")
    for doc in result["retrieved_documents"]:
        print(f"  * [{doc.get('id')}] {doc.get('title')}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

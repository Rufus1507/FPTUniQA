"""Script tạo và lưu trữ chỉ mục BM25 từ file corpus.jsonl."""

from pathlib import Path
from university_qa.retrieval.bm25 import BM25Retriever
from university_qa.utils.config import load_config
from university_qa.utils.io import read_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.build_bm25")


def main():
    config = load_config()
    corpus_path = config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl")

    output_dir = Path("data/processed/bm25_index")

    logger.info(f"Đọc corpus từ: {corpus_path}")
    docs = read_jsonl(corpus_path)
    logger.info(f"Tổng số tài liệu: {len(docs)}")

    bm25_cfg = config.get("retrieval", {}).get("bm25", {})
    bm25 = BM25Retriever(
        k1=bm25_cfg.get("k1", 1.5),
        b=bm25_cfg.get("b", 0.75),
        tokenizer_type=bm25_cfg.get("tokenizer", "pyvi"),
    )
    logger.info("Đang xây dựng chỉ mục BM25...")
    bm25.index(docs)

    bm25.save(output_dir)
    logger.info(f"Đã lưu chỉ mục BM25 thành công tại: {output_dir}")


if __name__ == "__main__":
    main()

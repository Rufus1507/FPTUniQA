"""Script tính toán vector embeddings và lưu chỉ mục FAISS."""

from pathlib import Path
from university_qa.retrieval.dense import DenseRetriever
from university_qa.retrieval.embedding import EmbeddingModel
from university_qa.utils.config import load_config
from university_qa.utils.io import read_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.build_faiss")


def main():
    config = load_config()
    corpus_path = config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl")

    dense_cfg = config.get("retrieval", {}).get("dense", {})
    output_dir = Path("data/processed/faiss_index")

    logger.info(f"Đọc corpus từ: {corpus_path}")
    docs = read_jsonl(corpus_path)
    logger.info(f"Tổng số tài liệu: {len(docs)}")

    embedding_model = EmbeddingModel(
        model_name=dense_cfg.get("embedding_model", "intfloat/multilingual-e5-base"),
        device=dense_cfg.get("device", "cpu"),
    )

    retriever = DenseRetriever(
        embedding_model=embedding_model,
        dimension=dense_cfg.get("dimension", 768),
        metric=dense_cfg.get("metric", "inner_product"),
    )

    import time
    logger.info("Đang sinh vector embeddings và tạo chỉ mục FAISS...")
    start_time = time.time()
    retriever.build_index(docs)
    elapsed = time.time() - start_time
    logger.info(f"Thời gian lập chỉ mục FAISS: {elapsed:.2f}s")

    retriever.save(output_dir)
    logger.info(f"Đã lưu chỉ mục FAISS thành công tại: {output_dir}")


if __name__ == "__main__":
    main()

"""Script chạy toàn bộ quy trình ETL tiền xử lý dữ liệu từ raw -> interim -> processed."""

from pathlib import Path
from university_qa.data.chunker import TextChunker
from university_qa.data.cleaner import clean_vietnamese_text
from university_qa.data.loader import DocumentLoader
from university_qa.data.metadata import MetadataEnricher
from university_qa.utils.config import load_config
from university_qa.utils.io import write_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.ingest_data")


def main():
    config = load_config()
    raw_dir = Path(config.get("data", {}).get("raw_dir", "data/raw"))
    processed_corpus = Path(config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl"))

    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=512, chunk_overlap=64)
    enricher = MetadataEnricher()

    logger.info(f"Quét các tài liệu thô trong: {raw_dir}")
    raw_docs = loader.load_directory(raw_dir)
    logger.info(f"Tìm thấy {len(raw_docs)} tệp thô.")

    corpus_chunks = []
    chunk_counter = 1

    for doc in raw_docs:
        cleaned_text = clean_vietnamese_text(doc["content"])
        sections = chunker.chunk_by_legal_sections(cleaned_text)

        for sec in sections:
            enriched = enricher.enrich_chunk(
                chunk_id=f"doc_{chunk_counter:04d}",
                title=sec["title"],
                text=sec["text"],
                custom_metadata={"source_file": doc["source"]},
            )
            corpus_chunks.append(enriched)
            chunk_counter += 1

    if corpus_chunks:
        write_jsonl(corpus_chunks, processed_corpus)
        logger.info(f"Đã trích xuất và ghi {len(corpus_chunks)} chunks vào {processed_corpus}")
    else:
        logger.info("Chưa có tệp dữ liệu thô mới trong data/raw. Giữ nguyên corpus hiện hành.")


if __name__ == "__main__":
    main()

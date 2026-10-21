"""Script chạy toàn bộ quy trình ETL tiền xử lý dữ liệu từ raw -> interim -> processed."""

import sys
from pathlib import Path

# Thêm đường dẫn src vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from university_qa.data.chunker import TextChunker
from university_qa.data.cleaner import clean_vietnamese_text
from university_qa.data.loader import DocumentLoader
from university_qa.data.metadata import MetadataEnricher
from university_qa.utils.config import load_config
from university_qa.utils.io import write_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.ingest_data")


def detect_file_metadata(filename: str) -> dict:
    """Tự động phân tích cohort, campus, category từ tên tệp Sổ tay sinh viên."""
    fn = filename.lower()
    meta = {
        "cohort": "ALL",
        "campus": "ALL",
        "category": "dao_tao",
        "doc_type": "handbook",
        "effective_date": "2023-09-01",
    }

    # Nhận diện khóa
    if "k17" in fn:
        meta["cohort"] = "K17"
        meta["effective_date"] = "2021-09-01"
    elif "k18" in fn:
        meta["cohort"] = "K18"
        meta["effective_date"] = "2022-09-01"
    elif "k19" in fn:
        meta["cohort"] = "K19"
        meta["effective_date"] = "2023-09-01"
    elif "k20" in fn:
        meta["cohort"] = "K20"
        meta["effective_date"] = "2024-09-01"
    elif "k21" in fn:
        meta["cohort"] = "K21"
        meta["effective_date"] = "2025-09-01"
    elif "k22" in fn:
        meta["cohort"] = "K22"
        meta["effective_date"] = "2026-09-01"

    # Nhận diện cơ sở (Campus)
    if "fuhl" in fn or "hòa lạc" in fn or "hoa lac" in fn:
        meta["campus"] = "FUHL"
    elif "hn" in fn or "hà nội" in fn or "ha noi" in fn:
        meta["campus"] = "HN"
    elif "hcm" in fn or "hồ chí minh" in fn or "ho chi minh" in fn:
        meta["campus"] = "HCM"

    # Nhận diện phân loại
    if "tài chính" in fn or "tai chinh" in fn or "học phí" in fn or "phi" in fn:
        meta["category"] = "hoc_phi"
        meta["doc_type"] = "finance_regulation"

    return meta


def main():
    config = load_config()
    raw_dir = Path(config.get("data", {}).get("raw_dir", "data/raw"))
    processed_corpus = Path(config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl"))

    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=1500, chunk_overlap=200, min_chunk_size=150)
    enricher = MetadataEnricher()

    logger.info(f"Quét các tài liệu thô trong: {raw_dir}")
    raw_docs = loader.load_directory(raw_dir)
    logger.info(f"Tìm thấy {len(raw_docs)} tệp thô.")

    corpus_chunks = []
    chunk_counter = 1

    for doc in raw_docs:
        # Bỏ qua các file không thuộc định dạng văn bản quy chế
        if not doc["source"].lower().endswith((".pdf", ".txt", ".md", ".docx", ".xlsx")):
            continue

        file_meta = detect_file_metadata(doc["source"])
        cohort = file_meta.get("cohort", "ALL")
        logger.info(f"Đang xử lý tệp: {doc['source']} (Khóa: {cohort}, Cơ sở: {file_meta['campus']})")

        cleaned_text = clean_vietnamese_text(doc["content"])
        sections = chunker.chunk_by_legal_sections(cleaned_text)
        logger.info(f"  -> Sinh ra {len(sections)} chunks ngữ nghĩa.")

        for sec in sections:
            doc_id = f"doc_fpt_{cohort.lower()}_{chunk_counter:04d}"
            payload = None
            title_lower = sec["title"].lower()
            if (
                file_meta["doc_type"] == "finance_regulation"
                or file_meta["category"] == "hoc_phi"
                or "học phí" in title_lower
                or "tài chính" in title_lower
                or "bảng phí" in title_lower
            ):
                payload = {
                    "tuition_fee_per_term": 28700000,
                    "credit_price_vnd": 650000,
                    "specialized_terms": 9,
                    "english_prep_fee_per_level": 11300000,
                    "english_prep_levels": 6,
                    "dorm_fee_per_term": 4500000,
                    "currency": "VND",
                }

            enriched = enricher.enrich_chunk(
                chunk_id=doc_id,
                title=sec["title"],
                text=sec["text"],
                custom_metadata={
                    "source_file": doc["source"],
                    "cohort": cohort,
                    "campus": file_meta["campus"],
                    "category": file_meta["category"],
                    "doc_type": file_meta["doc_type"],
                    "effective_date": file_meta["effective_date"],
                },
                structured_payload=payload,
            )
            corpus_chunks.append(enriched)
            chunk_counter += 1

    if corpus_chunks:
        write_jsonl(corpus_chunks, processed_corpus)
        logger.info(f"HOÀN TẤT: Đã trích xuất và ghi {len(corpus_chunks)} chunks sạch vào {processed_corpus}")
    else:
        logger.warning("Không có tệp dữ liệu thô mới trong data/raw.")


if __name__ == "__main__":
    main()

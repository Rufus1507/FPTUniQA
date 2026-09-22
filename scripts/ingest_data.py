"""
Script chạy toàn bộ quy trình ETL tiền xử lý dữ liệu từ raw -> interim -> processed.

Luồng xử lý:
1. Nạp tệp HTML thô từ data/raw/fpt_admission/html/ kèm crawl_manifest.jsonl
2. Lọc và kiểm tra chất lượng (loại bỏ trang lỗi, trùng lặp, ít nội dung)
3. Làm sạch văn bản và chuẩn hóa định dạng
4. Phân đoạn (chunking) bảo tồn bảng biểu và cấu trúc heading
5. Gán metadata đầy đủ (doc_type, campus, cohort, effective_date, URL)
6. Xuất corpus.jsonl, structured_data.json, discarded_pages.jsonl
"""

import json
from pathlib import Path

from university_qa.data.chunker import TextChunker
from university_qa.data.cleaner import clean_document_text
from university_qa.data.loader import DocumentLoader
from university_qa.data.metadata import MetadataEnricher
from university_qa.data.structured import extract_structured_tuition_from_html_files
from university_qa.utils.config import load_config
from university_qa.utils.io import write_jsonl
from university_qa.utils.logger import get_logger

logger = get_logger("scripts.ingest_data")

# Ngưỡng số từ tối thiểu để không bị xếp là trang rác
MIN_WORD_COUNT = 80
# Ngưỡng tỷ lệ ký tự boilerplate tối đa (menu, nav, footer)
MAX_BOILERPLATE_RATIO = 0.75


def is_low_quality(doc: dict) -> tuple[bool, str]:
    """
    Kiểm tra chất lượng tài liệu, trả về (True, reason) nếu cần loại bỏ.
    """
    content = doc.get("content", "")
    word_count = len(content.split())

    if word_count < MIN_WORD_COUNT:
        return True, f"low_content ({word_count} words < {MIN_WORD_COUNT})"

    status_code = doc.get("status_code")
    if status_code is not None and status_code != 200:
        return True, f"non_200_status ({status_code})"

    return False, ""


def main():
    config = load_config()
    raw_html_dir = Path("data/raw/fpt_admission/html")
    manifest_path = Path("data/raw/crawl_manifest.jsonl")
    processed_corpus = Path(config.get("data", {}).get("corpus_path", "data/processed/corpus.jsonl"))
    structured_path = Path(config.get("data", {}).get("structured_path", "data/processed/structured_data.json"))
    interim_dir = Path(config.get("data", {}).get("interim_dir", "data/interim"))
    discarded_path = interim_dir / "discarded_pages.jsonl"

    # Đảm bảo thư mục tồn tại
    processed_corpus.parent.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Bước 1: Nạp tài liệu thô
    # ------------------------------------------------------------------ #
    loader = DocumentLoader()
    chunker = TextChunker(chunk_size=512, chunk_overlap=64)
    enricher = MetadataEnricher()

    logger.info(f"Quét tài liệu HTML trong: {raw_html_dir}")
    logger.info(f"Manifest: {manifest_path}")

    raw_docs = loader.load_directory(raw_html_dir, manifest_path=manifest_path)
    logger.info(f"Tìm thấy {len(raw_docs)} tệp thô.")

    # ------------------------------------------------------------------ #
    # Bước 2: Lọc trùng lặp theo content_hash
    # ------------------------------------------------------------------ #
    seen_hashes: set = set()
    unique_docs = []
    for doc in raw_docs:
        ch = doc.get("content_hash", "")
        if ch and ch in seen_hashes:
            continue
        if ch:
            seen_hashes.add(ch)
        unique_docs.append(doc)

    logger.info(f"Sau khi lọc trùng lặp content_hash: {len(unique_docs)} tài liệu.")

    # ------------------------------------------------------------------ #
    # Bước 3: Kiểm tra chất lượng và phân loại
    # ------------------------------------------------------------------ #
    good_docs = []
    discarded = []

    for doc in unique_docs:
        low, reason = is_low_quality(doc)
        if low:
            discarded.append({
                "source": doc.get("source"),
                "url": doc.get("url"),
                "word_count": len(doc.get("content", "").split()),
                "reason": reason,
            })
        else:
            good_docs.append(doc)

    logger.info(f"Tài liệu đạt chất lượng: {len(good_docs)}")
    logger.info(f"Tài liệu bị loại bỏ: {len(discarded)}")

    # Ghi báo cáo loại bỏ
    write_jsonl(discarded, discarded_path)
    logger.info(f"Đã ghi {len(discarded)} bản ghi loại bỏ vào {discarded_path}")

    # ------------------------------------------------------------------ #
    # Bước 4: Làm sạch, Chunking, Gán Metadata
    # ------------------------------------------------------------------ #
    corpus_chunks = []
    chunk_counter = 1

    for doc in good_docs:
        raw_content = doc.get("content", "")
        tables_md = doc.get("tables_md", [])
        title = doc.get("title") or doc.get("h1") or doc.get("source", "")

        # Làm sạch văn bản (chuẩn hóa Unicode, VND amounts, khoảng trắng)
        cleaned_text = clean_document_text(raw_content, normalize_numbers=True)

        # Chunking: bảo tồn bảng biểu, phân đoạn heading
        chunks = chunker.chunk_document(
            text=cleaned_text,
            tables_md=tables_md,
            title=title,
        )

        for chunk_dict in chunks:
            chunk_text = chunk_dict.get("text", "").strip()
            chunk_title = chunk_dict.get("title", title)

            if not chunk_text:
                continue

            chunk_id = f"fpt_{chunk_counter:06d}"

            enriched = enricher.enrich_from_document(
                chunk_id=chunk_id,
                title=chunk_title,
                text=chunk_text,
                doc=doc,
            )
            corpus_chunks.append(enriched)
            chunk_counter += 1

    # ------------------------------------------------------------------ #
    # Bước 5: Xuất corpus.jsonl
    # ------------------------------------------------------------------ #
    if corpus_chunks:
        write_jsonl(corpus_chunks, processed_corpus)
        logger.info(f"Đã ghi {len(corpus_chunks)} chunks vào {processed_corpus}")
    else:
        logger.warning("Không có chunks nào được tạo ra. Kiểm tra lại thư mục raw.")

    # ------------------------------------------------------------------ #
    # Bước 6: Trích xuất Structured Data (bảng học phí K22)
    # ------------------------------------------------------------------ #
    logger.info("Trích xuất bảng học phí có cấu trúc từ HTML...")
    structured_data = extract_structured_tuition_from_html_files(
        html_dir=raw_html_dir,
        manifest_path=manifest_path,
    )

    tuition_count = len(structured_data.get("tuition_flat_list", []))
    campuses = structured_data.get("campuses_extracted", [])

    if structured_data:
        with open(structured_path, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã ghi structured_data.json với {tuition_count} bản ghi học phí, {len(campuses)} campus.")
    else:
        logger.warning("Không trích xuất được dữ liệu học phí có cấu trúc.")

    # ------------------------------------------------------------------ #
    # Báo cáo tổng kết
    # ------------------------------------------------------------------ #
    logger.info("=" * 60)
    logger.info("BÁO CÁO TỔNG KẾT INGEST DATA")
    logger.info(f"  Tổng tệp thô: {len(raw_docs)}")
    logger.info(f"  Sau lọc trùng: {len(unique_docs)}")
    logger.info(f"  Tài liệu đạt chất lượng: {len(good_docs)}")
    logger.info(f"  Tài liệu loại bỏ: {len(discarded)}")
    logger.info(f"  Corpus chunks tạo ra: {len(corpus_chunks)}")
    logger.info(f"  Bản ghi học phí có cấu trúc: {tuition_count}")
    logger.info(f"  Campus học phí đã trích xuất: {campuses}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

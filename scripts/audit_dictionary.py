"""Script kiểm tra và đánh giá toàn diện Bộ từ điển FPTUniQA (Domain Dictionary & EntityNormalizer).

Các khía cạnh kiểm tra:
1. Data Integrity & Schema Validation (Tính toàn vẹn dữ liệu, kiểm tra trùng lặp ID, resolves_to, aliases).
2. Entity Statistics & Coverage Breakdown (Thống kê số lượng thực thể, alias theo từng danh mục).
3. Disambiguation & Edge Cases (Khử đa nghĩa ngữ cảnh 'AI', 'SE', 'IS', đại từ, không dấu).
4. Slots Hint Extraction Compatibility (Độ tương thích với Contract 3 ParsedQuery).
5. Pipeline Integration Inspection (Kiểm tra sự hiện diện của từ điển trong các module cốt lõi).
6. Performance & Throughput (Đo độ trễ nạp từ điển và độ trễ chuẩn hóa trên 500 truy vấn).
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.normalization.engine import EntityNormalizer, get_entity_normalizer


def audit_dictionary():
    dict_dir = Path("data/dictionary")
    print(f"\n{'='*85}")
    print(f"▶ BẮT ĐẦU ĐÁNH GIÁ TOÀN DIỆN BỘ TỪ ĐIỂN HỌC VỤ FPTUniQA")
    print(f"Thư mục: {dict_dir.resolve()}")
    print(f"{'='*85}\n")

    if not dict_dir.exists():
        print(f"❌ LỖI: Thư mục {dict_dir} không tồn tại!")
        return

    # ---------------------------------------------------------
    # 1. KIỂM TRA TÍNH TOÀN VẸN & SCHEMA
    # ---------------------------------------------------------
    print("1. KIỂM TRA TÍNH TOÀN VẸN DỮ LIỆU & SCHEMA (DATA INTEGRITY)")
    print("-" * 70)

    json_files = list(dict_dir.glob("*.json"))
    schema_file = dict_dir / "schema.json"
    data_files = [f for f in json_files if f.name != "schema.json"]

    all_entity_ids: Set[str] = set()
    id_duplicates: List[str] = []
    alias_count = 0
    file_stats = []
    resolves_to_checks = []

    for fpath in data_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"   ⚠️ {fpath.name}: Định dạng cấp cao nhất phải là một danh sách (list)!")
                continue

            file_eids = set()
            file_aliases = 0
            missing_fields = []

            for idx, entry in enumerate(data):
                eid = entry.get("entity_id")
                etype = entry.get("entity_type")
                cname = entry.get("canonical_name")
                aliases = entry.get("aliases", [])

                if not eid or not etype or not cname:
                    missing_fields.append((idx, eid or "UNKNOWN"))

                if eid in all_entity_ids:
                    id_duplicates.append(eid)
                all_entity_ids.add(eid)
                file_eids.add(eid)

                file_aliases += len(aliases)
                alias_count += len(aliases)

                if "resolves_to" in entry and entry["resolves_to"]:
                    resolves_to_checks.append((eid, entry["resolves_to"], fpath.name))

            file_stats.append({
                "file": fpath.name,
                "entities": len(file_eids),
                "aliases": file_aliases,
                "missing": len(missing_fields),
            })

        except Exception as exc:
            print(f"   ❌ Lỗi khi đọc {fpath.name}: {exc}")

    # In thống kê file
    print(f"{'Tệp từ điển':<25} | {'Số thực thể':<15} | {'Số bí danh (Alias)':<20} | {'Lỗi trường':<10}")
    print(f"{'-'*75}")
    for fs in file_stats:
        print(f"{fs['file']:<25} | {fs['entities']:<15} | {fs['aliases']:<20} | {fs['missing']:<10}")
    print(f"{'-'*75}")
    print(f"▶ Tổng số thực thể độc nhất: {len(all_entity_ids)}")
    print(f"▶ Tổng số biến thể/bí danh (aliases): {alias_count}")

    # Kiểm tra trùng ID
    if id_duplicates:
        print(f"   ❌ CẢNH BÁO: Phát hiện {len(id_duplicates)} entity_id bị trùng lặp: {id_duplicates}")
    else:
        print("   ✅ Xác nhận: 100% entity_id là độc nhất, không có trùng lặp.")

    # Kiểm tra tính toàn vẹn của resolves_to
    resolves_errors = []
    for src_id, target_id, fname in resolves_to_checks:
        if target_id not in all_entity_ids:
            resolves_errors.append((src_id, target_id, fname))

    if resolves_errors:
        print(f"   ❌ Lỗi tham chiếu resolves_to: {len(resolves_errors)} thực thể trỏ đến ID không tồn tại!")
        for src, tgt, fn in resolves_errors[:5]:
            print(f"      - [{fn}] {src} -> {tgt} (Không tìm thấy!)")
    else:
        print(f"   ✅ Xác nhận: 100% tham chiếu resolves_to ({len(resolves_to_checks)} liên kết) hợp lệ và toàn vẹn.")

    # ---------------------------------------------------------
    # 2. KIỂM TRA ĐỘNG CƠ ENTITY NORMALIZER
    # ---------------------------------------------------------
    print(f"\n2. KIỂM TRA ĐỘNG CƠ ENTITY NORMALIZER (MATCHING & DISAMBIGUATION)")
    print("-" * 70)

    t_init_start = time.perf_counter()
    normalizer = EntityNormalizer(dict_dir=dict_dir)
    t_init_ms = (time.perf_counter() - t_init_start) * 1000.0
    print(f"▶ Thời gian nạp từ điển & tiền biên dịch Regex: {t_init_ms:.2f} ms")

    test_scenarios = [
        # (Truy vấn, Tiêu chí mong đợi, Mô tả)
        (
            "Học phí ngành AI khóa K22 tại Cần Thơ là bao nhiêu?",
            {"slots": {"program": "AI", "cohort": "K22", "campus": "Cần Thơ"}},
            "Nhận diện đầy đủ 3 slot: program, cohort, campus",
        ),
        (
            "Học phí ngành Trí tuệ nhân tạo khóa 2026 ở ct",
            {"slots": {"program": "AI", "cohort": "K22", "campus": "Cần Thơ"}},
            "Chuẩn hóa alias tiếng Việt + năm tuyển sinh 2026 + viết tắt 'ct'",
        ),
        (
            "hoc phi nganh ky thuat phan mem khoa 2025 tai hoa lac",
            {"slots": {"program": "KTPM", "cohort": "K21", "campus": "Hà Nội"}},
            "Xử lý tiếng Việt KHÔNG DẤU hoàn toàn + Hòa Lạc -> Hà Nội",
        ),
        (
            "mon prf192 hoc o ky may va co bao nhieu tin chi",
            {"slots": {"course_code": "PRF192"}},
            "Nhận diện mã môn không dấu + trích xuất course_code",
        ),
        (
            "Giáo trình môn Cơ sở lập trình C là sách gì?",
            {"slots": {"course_code": "PRF192", "course_aspect": "textbook"}},
            "Nhận diện môn qua Tên tiếng Việt và aspect textbook",
        ),
        (
            "Ai là người sáng lập Đại học FPT?",
            {"forbidden_entity": "MAJOR_AI"},
            "Khử đa nghĩa: 'Ai' trong câu hỏi không được nhận nhầm là ngành AI",
        ),
        (
            "Học phí phân hiệu Quy Nhơn ngành Thiết kế vi mạch bán dẫn",
            {"slots": {"campus": "Quy Nhơn", "program": "Vi mạch bán dẫn"}},
            "Ngành mới Vi mạch bán dẫn và campus Quy Nhơn",
        ),
        (
            "phi ktx o hl la bn tien",
            {"slots": {"campus": "Hà Nội"}},
            "Từ viết tắt: hl -> Hà Nội, ktx -> ký túc xá",
        ),
        (
            "Học phí ngành IS tại TP.HCM",
            {"slots": {"program": "Hệ thống thông tin", "campus": "TP. Hồ Chí Minh"}},
            "Viết tắt IS -> Hệ thống thông tin",
        ),
        (
            "Lệ phí thi lại và học lại tính theo một tín chỉ",
            {"slots": {"topic": "tin_chi"}},
            "Thuật ngữ học vụ: tín chỉ / học lại / thi lại",
        ),
    ]

    passed_scenarios = 0
    for idx, (query, criteria, desc) in enumerate(test_scenarios, 1):
        res = normalizer.normalize(query)
        eids = [e.entity_id for e in res.entities]
        slots = res.slots_hint

        failed_reasons = []

        # Kiểm tra slots mong đợi
        if "slots" in criteria:
            for k, v in criteria["slots"].items():
                if slots.get(k) != v:
                    failed_reasons.append(f"Slot '{k}' kỳ vọng '{v}', thực tế '{slots.get(k)}'")

        # Kiểm tra forbidden_entity
        if "forbidden_entity" in criteria:
            if criteria["forbidden_entity"] in eids:
                failed_reasons.append(f"Dính entity cấm '{criteria['forbidden_entity']}'")

        if not failed_reasons:
            passed_scenarios += 1
            print(f"[{idx:02d}/10] ✅ PASS | {desc}")
            print(f"       Câu: '{query}' -> Slots: {slots}")
        else:
            print(f"[{idx:02d}/10] ❌ FAIL | {desc}")
            print(f"       Câu: '{query}'")
            print(f"       Lỗi: {', '.join(failed_reasons)}")
            print(f"       Thực thể tìm thấy: {eids}")
            print(f"       Slots thực tế: {slots}")

    print(f"\n▶ Kết quả bài test kiểm thử chức năng Normalizer: {passed_scenarios}/{len(test_scenarios)} ({passed_scenarios/len(test_scenarios)*100:.1f}%)")

    # ---------------------------------------------------------
    # 3. ĐO HIỆU NĂNG VÀ ĐỘ TRỄ (BENCHMARK THROUGHPUT)
    # ---------------------------------------------------------
    print(f"\n3. ĐO LƯỜNG HIỆU NĂNG & ĐỘ TRỄ (PERFORMANCE)")
    print("-" * 70)

    sample_queries = [
        "Học phí chuyên ngành Kỹ thuật phần mềm khóa K22 tại phân hiệu Hà Nội là bao nhiêu?",
        "Môn Cấu trúc dữ liệu và giải thuật CSD201 học giáo trình gì?",
        "Sinh viên vắng bao nhiêu phần trăm số buổi thì bị cấm thi?",
        "Học phí ngành Trí tuệ nhân tạo khóa 2026 tại cơ sở Cần Thơ",
        "thế còn ở phân hiệu Quy Nhơn thì sao hả admin?",
    ]

    total_runs = 500
    t_start = time.perf_counter()
    for i in range(total_runs):
        normalizer.normalize(sample_queries[i % len(sample_queries)])
    total_time_ms = (time.perf_counter() - t_start) * 1000.0
    avg_per_query = total_time_ms / total_runs

    print(f"▶ Chạy thành công {total_runs} lượt chuẩn hóa truy vấn.")
    print(f"▶ Tổng thời gian: {total_time_ms:.2f} ms")
    print(f"▶ Độ trễ trung bình trên mỗi câu: {avg_per_query:.3f} ms / truy vấn")
    print(f"▶ Throughput tương đương: {int(1000 / avg_per_query):,} truy vấn / giây trên 1 core CPU")

    # ---------------------------------------------------------
    # 4. KIỂM TRA TÍCH HỢP HỆ THỐNG (PIPELINE INTEGRATION)
    # ---------------------------------------------------------
    print(f"\n4. KIỂM TRA MỨC ĐỘ TÍCH HỢP HỆ THỐNG (SYSTEM INTEGRATION)")
    print("-" * 70)

    modules_to_check = [
        ("src/FPTUniQA/query/rewriting.py", "Query Rewriter"),
        ("src/FPTUniQA/query/semantic_parser.py", "Semantic Parser"),
        ("src/FPTUniQA/query/router.py", "Router"),
    ]

    for mpath, mname in modules_to_check:
        p = Path(mpath)
        if not p.exists():
            print(f"   ⚠️ {mname} ({mpath}): Tệp không tồn tại!")
            continue
        content = p.read_text(encoding="utf-8")
        has_normalizer = "normalization.engine" in content or "get_entity_normalizer" in content or "EntityNormalizer" in content
        if has_normalizer:
            print(f"   ✅ {mname:<20}: ĐÃ ĐƯỢC TÍCH HỢP EntityNormalizer.")
        else:
            print(f"   ℹ️ {mname:<20}: Chưa import trực tiếp EntityNormalizer (sử dụng slot từ hợp đồng đầu vào).")

    print(f"\n{'='*85}")
    print("HOÀN TẤT ĐÁNH GIÁ BỘ TỪ ĐIỂN")
    print(f"{'='*85}\n")


if __name__ == "__main__":
    audit_dictionary()

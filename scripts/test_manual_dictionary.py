"""Bộ công cụ kiểm thử thủ công và tự động cho Từ điển học vụ FPTUniQA.

Hỗ trợ 2 chế độ:
1. Chạy bộ câu hỏi mẫu kiểm tra độ chính xác (so sánh Thực tế vs Mong đợi).
2. Chế độ tương tác nhập trực tiếp bằng bàn phím (Interactive CLI mode).
"""

import argparse
import sys
import time
from typing import Any, Dict, List, Optional
from FPTUniQA.normalization.engine import get_entity_normalizer


# ---------------------------------------------------------------------------
# BỘ CÂU HỎI KIỂM THỬ THỦ CÔNG (ĐA DẠNG CÁC NHÓM NGỮ CẢNH)
# ---------------------------------------------------------------------------
MANUAL_TEST_SUITE: List[Dict[str, Any]] = [
    # --- NHÓM 1: Khử đa nghĩa từ "Ai" (Disambiguation) ---
    {
        "id": "TC_01",
        "category": "Disambiguation (Đại từ nghi vấn)",
        "query": "Ai là người sáng lập Đại học FPT?",
        "expected_slots": {},
        "forbidden_eids": ["MAJOR_AI"],
        "description": "'Ai' ở đầu câu là đại từ hỏi người, tuyệt đối không nhận nhầm là ngành AI.",
    },
    {
        "id": "TC_02",
        "category": "Disambiguation (Đại từ nghi vấn)",
        "query": "Em cần gặp ai để nộp đơn xin bảo lưu học phần?",
        "expected_slots": {},
        "forbidden_eids": ["MAJOR_AI"],
        "description": "'gặp ai' là đại từ nghi vấn nhân sự, không được gán MAJOR_AI.",
    },
    {
        "id": "TC_03",
        "category": "Disambiguation (Định nghĩa thuật ngữ)",
        "query": "AI là gì vậy ad?",
        "expected_slots": {"program": "AI"},
        "expected_eids": ["MAJOR_AI"],
        "description": "'AI là gì' hỏi về định nghĩa ngành/thuật ngữ Trí tuệ nhân tạo.",
    },
    {
        "id": "TC_04",
        "category": "Disambiguation (Môn học vs Ngành học)",
        "query": "Thầy cô nào dạy môn AI kỳ này?",
        "expected_slots": {},
        "forbidden_eids": ["MAJOR_AI"],
        "description": "'môn AI' đi kèm tiền tố 'môn' nên khử phân giải, không phải ngành AI.",
    },
    {
        "id": "TC_05",
        "category": "Disambiguation (Ngành học đầy đủ ngữ cảnh)",
        "query": "Học phí chuyên ngành AI khóa K22 tại Cần Thơ",
        "expected_slots": {"program": "AI", "cohort": "K22", "campus": "Cần Thơ"},
        "expected_eids": ["MAJOR_AI", "COHORT_K22", "CAMPUS_CANTHO"],
        "description": "Nhận diện đủ 3 slot học vụ quan trọng.",
    },

    # --- NHÓM 2: Từ viết tắt học vụ & Tiếng lóng sinh viên (Abbreviations & Slang) ---
    {
        "id": "TC_06",
        "category": "Abbreviations (Viết tắt & Tiếng lóng)",
        "query": "phi ktx o hl la bn tien",
        "expected_slots": {"campus": "Hà Nội"},
        "expected_eids": ["TERM_KY_TUC_XA", "CAMPUS_HANOI"],
        "description": "hl -> Phân hiệu Hà Nội, ktx -> Ký túc xá.",
    },
    {
        "id": "TC_07",
        "category": "Abbreviations (Viết tắt & Tiếng lóng)",
        "query": "hoc phi nganh is o tphcm la bao nhieu",
        "expected_slots": {"program": "Hệ thống thông tin", "campus": "TP. Hồ Chí Minh"},
        "expected_eids": ["MAJOR_HTTT", "CAMPUS_HCM"],
        "description": "is -> Hệ thống thông tin, tphcm -> TP. Hồ Chí Minh.",
    },
    {
        "id": "TC_08",
        "category": "Abbreviations (Viết tắt & Tiếng lóng)",
        "query": "sv can bao nhieu tin chi de duoc di ojt",
        "expected_slots": {"topic": "tin_chi"},
        "expected_eids": ["TERM_SINH_VIEN", "TERM_TIN_CHI", "TERM_OJT"],
        "description": "sv -> Sinh viên, ojt -> Thực tập doanh nghiệp.",
    },
    {
        "id": "TC_09",
        "category": "Abbreviations (Viết tắt & Tiếng lóng)",
        "query": "lich thi pe va eos mon prf192 xem o dau",
        "expected_slots": {"course_code": "PRF192"},
        "expected_eids": ["TERM_PE", "TERM_EOS", "COURSE_PRF192"],
        "description": "pe -> Thi thực hành, eos -> Thi cuối kỳ, prf192 -> Môn PRF192.",
    },
    {
        "id": "TC_10",
        "category": "Abbreviations (Viết tắt & Tiếng lóng)",
        "query": "diem gpa va cgpa duoi bao nhieu thi bi canh bao hoc vu",
        "expected_slots": {},
        "expected_eids": ["TERM_GPA", "TERM_CGPA", "TERM_CANH_BAO_HOC_VU"],
        "description": "gpa -> Điểm TB học kỳ, cgpa -> Điểm tích lũy, cảnh báo học vụ.",
    },

    # --- NHÓM 3: Tiếng Việt không dấu hoàn toàn (Diacritic Folding) ---
    {
        "id": "TC_11",
        "category": "Unaccented (Tiếng Việt không dấu)",
        "query": "hoc phi nganh ky thuat phan mem khoa 2026 tai hoa lac",
        "expected_slots": {"program": "KTPM", "cohort": "K22", "campus": "Hà Nội"},
        "expected_eids": ["MAJOR_KTPM", "COHORT_K22", "CAMPUS_HANOI"],
        "description": "Xử lý không dấu: ky thuat phan mem -> KTPM, 2026 -> K22, hoa lac -> Hà Nội.",
    },
    {
        "id": "TC_12",
        "category": "Unaccented (Tiếng Việt không dấu)",
        "query": "diem chuan nganh thiet ke do hoa o qn",
        "expected_slots": {"program": "Thiết kế đồ họa và mỹ thuật số", "campus": "Quy Nhơn"},
        "expected_eids": ["MAJOR_TKDH", "CAMPUS_QUYNHON"],
        "description": "thiet ke do hoa -> Thiết kế đồ họa và mỹ thuật số, qn -> Quy Nhơn.",
    },
    {
        "id": "TC_13",
        "category": "Unaccented (Tiếng Việt không dấu)",
        "query": "nganh an toan thong tin co so dn hoc phi the nao",
        "expected_slots": {"program": "An toàn thông tin", "campus": "Đà Nẵng"},
        "expected_eids": ["MAJOR_ATTT", "CAMPUS_DANANG"],
        "description": "an toan thong tin -> ATTT, dn -> Đà Nẵng.",
    },

    # --- NHÓM 4: Môn học, Giáo trình & Môn tiên quyết ---
    {
        "id": "TC_14",
        "category": "Courses (Môn học & Giáo trình)",
        "query": "Giao trinh mon Co so lap trinh C la sach gi?",
        "expected_slots": {"course_code": "PRF192", "course_aspect": "textbook"},
        "expected_eids": ["COURSE_PRF192"],
        "description": "Nhận diện qua tên tiếng Việt không dấu 'Co so lap trinh C' -> PRF192.",
    },
    {
        "id": "TC_15",
        "category": "Courses (Môn học & Giáo trình)",
        "query": "Mon PRJ301 co bao nhieu tin chi va hoc o ky may?",
        "expected_slots": {"course_code": "PRJ301", "topic": "tin_chi"},
        "expected_eids": ["COURSE_PRJ301", "TERM_TIN_CHI"],
        "description": "Mã môn trực tiếp PRJ301, tin chi -> topic tin_chi.",
    },
    {
        "id": "TC_16",
        "category": "Courses (Môn học & Giáo trình)",
        "query": "Mon tien quyet cua mon Cau truc du lieu va giai thuat la gi?",
        "expected_slots": {"course_code": "CSD201"},
        "expected_eids": ["COURSE_CSD201", "TERM_TIEN_QUYET"],
        "description": "Nhận diện tên môn tiếng Việt CSD201 + môn tiên quyết.",
    },

    # --- NHÓM 5: Ngành mới & Khóa học tương lai ---
    {
        "id": "TC_17",
        "category": "New Programs & Cohorts",
        "query": "Nganh Thiet ke vi mach ban dan hoc phi bao nhieu tai phan hieu Quy Nhon",
        "expected_slots": {"program": "Vi mạch bán dẫn", "campus": "Quy Nhơn"},
        "expected_eids": ["MAJOR_SEMICONDUCTOR", "CAMPUS_QUYNHON"],
        "description": "Ngành mới Vi mạch bán dẫn tại Quy Nhơn.",
    },
    {
        "id": "TC_18",
        "category": "New Programs & Cohorts",
        "query": "Hoc phi khoa 2028 nganh AI la bao nhieu",
        "expected_slots": {"program": "AI"},
        "expected_eids": ["MAJOR_AI", "RAW_YEAR_2028"],
        "description": "Năm 2028 chưa verified -> gắn RAW_YEAR_2028 với verified=False an toàn.",
    },
    {
        "id": "TC_19",
        "category": "New Programs & Cohorts",
        "query": "Sinh vien khoa K21 nganh KTPM co can hoc Vovinam khong",
        "expected_slots": {"cohort": "K21", "program": "KTPM"},
        "expected_eids": ["COHORT_K21", "MAJOR_KTPM", "TERM_GDTC"],
        "description": "Vovinam -> ánh xạ chuẩn sang TERM_GDTC (Giáo dục thể chất).",
    },
    {
        "id": "TC_20",
        "category": "Academic Rules (Quy chế học vụ)",
        "query": "Le phi thi lai va hoc lai tinh theo mot tin chi la bao nhieu",
        "expected_slots": {"topic": "tin_chi"},
        "expected_eids": ["TERM_LE_PHI_THI_LAI", "TERM_LE_PHI_HOC_LAI", "TERM_TIN_CHI"],
        "description": "Trích xuất cả 3 thực thể tài chính: thi lại, học lại, tín chỉ.",
    },
]


def run_automated_suite(verbose: bool = True) -> int:
    """Chạy toàn bộ bộ kiểm thử thủ công và in bảng so sánh trực quan."""
    normalizer = get_entity_normalizer()
    total = len(MANUAL_TEST_SUITE)
    passed = 0

    print("=" * 90)
    print(f"▶ CHẠY BỘ KIỂM THỬ THỦ CÔNG TỪ ĐIỂN HỌC VỤ FPTUniQA ({total} CA KIỂM THỬ)")
    print("=" * 90)

    for tc in MANUAL_TEST_SUITE:
        qid = tc["id"]
        category = tc["category"]
        query = tc["query"]
        exp_slots = tc.get("expected_slots", {})
        exp_eids = tc.get("expected_eids", [])
        forbid_eids = tc.get("forbidden_eids", [])

        t0 = time.perf_counter()
        res = normalizer.normalize(query)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        actual_eids = [e.entity_id for e in res.entities]
        actual_slots = res.slots_hint

        # Kiểm tra tiêu chí
        errors = []
        for k, v in exp_slots.items():
            if actual_slots.get(k) != v:
                errors.append(f"Slot '{k}' kỳ vọng '{v}', thực tế '{actual_slots.get(k)}'")

        for eid in exp_eids:
            if eid not in actual_eids:
                errors.append(f"Thiếu thực thể kỳ vọng '{eid}'")

        for eid in forbid_eids:
            if eid in actual_eids:
                errors.append(f"Dính thực thể bị cấm '{eid}'")

        is_ok = len(errors) == 0
        if is_ok:
            passed += 1
            status_str = "✓ PASS"
        else:
            status_str = "✗ FAIL"

        if verbose or not is_ok:
            print(f"\n[{qid}] {status_str} | [{category}] ({latency_ms:.2f}ms)")
            print(f"   Câu hỏi: \"{query}\"")
            print(f"   Thực thể: {actual_eids}")
            print(f"   Slots   : {actual_slots}")
            if not is_ok:
                for err in errors:
                    print(f"   Lý do lỗi -> {err}")
            print(f"   Ghi chú : {tc.get('description', '')}")

    print("\n" + "=" * 90)
    print(f"KẾT QUẢ TỔNG HỢP: {passed}/{total} ca đạt chuẩn ({passed / total * 100:.1f}%)")
    print("=" * 90)
    return 0 if passed == total else 1


def interactive_mode():
    """Chế độ nhập tương tác từ bàn phím để kiểm tra câu hỏi tùy ý."""
    normalizer = get_entity_normalizer()
    print("\n" + "=" * 70)
    print("CHẾ ĐỘ TƯƠNG TÁC THỬ NGHIỆM TỪ ĐIỂN FPTUniQA (Interactive Mode)")
    print("Nhập câu hỏi bất kỳ để xem kết quả chuẩn hóa (gõ 'exit' hoặc 'quit' để thoát).")
    print("=" * 70)

    while True:
        try:
            query = input("\n[FPTUniQA Query] > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Tạm biệt!")
                break

            t0 = time.perf_counter()
            res = normalizer.normalize(query)
            latency_ms = (time.perf_counter() - t0) * 1000.0

            print(f"--- KẾT QUẢ CHUẨN HÓA ({latency_ms:.2f} ms) ---")
            print(f"Original Query   : {res.original_query}")
            print(f"Normalized Query : {res.normalized_query}")
            print(f"Slots Hint       : {res.slots_hint}")
            print(f"Detected Entities ({len(res.entities)}):")
            for idx, e in enumerate(res.entities, 1):
                status_v = "Verified" if e.verified else "Unverified"
                print(
                    f"  {idx}. [{e.entity_type.upper()}] ID={e.entity_id} | "
                    f"Tên='{e.canonical_name_vi}' | Khớp='{e.matched_alias}' | "
                    f"Span={e.span} | {status_v}"
                )

        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát chế độ tương tác.")
            break


def main():
    parser = argparse.ArgumentParser(description="Bộ kiểm thử thủ công Từ điển học vụ FPTUniQA")
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Bật chế độ tương tác nhập câu hỏi trực tiếp từ bàn phím"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Chỉ in các ca bị lỗi"
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        sys.exit(run_automated_suite(verbose=not args.quiet))


if __name__ == "__main__":
    main()

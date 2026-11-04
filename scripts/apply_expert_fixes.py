import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def apply_improvements():
    # 2. router.py
    router_path = ROOT / "src" / "FPTUniQA" / "query" / "router.py"
    router_content = router_path.read_text(encoding="utf-8")
    if "is_unconfident_fallback" not in router_content:
        old_router = """    # 0. Kiểm tra ngưỡng tin cậy an toàn (Tuần 6 Guardrail)
    if parsed.confidence is not None and parsed.confidence < 0.5:
        return RouteResult(
            "uncertain",
            "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể.",
            level=10,
        )"""

        new_router = """    # 0. Kiểm tra ngưỡng tin cậy an toàn (Tuần 6 Guardrail) & Fallback không xác định
    is_low_conf = parsed.confidence is not None and parsed.confidence < 0.5
    is_unconfident_fallback = getattr(parsed, "fallback_used", False) and not parsed.slots and parsed.intent in ("policy_lookup", "OOD") and (parsed.confidence is None or parsed.confidence <= 0.5)
    if is_low_conf or is_unconfident_fallback:
        return RouteResult(
            "uncertain",
            "Hệ thống chưa chắc chắn về câu hỏi này (độ tin cậy phân tích thấp). Vui lòng diễn đạt rõ hơn hoặc cung cấp thêm thông tin học vụ cụ thể.",
            level=10,
        )"""
        assert old_router in router_content, "old_router not found in router.py"
        router_content = router_content.replace(old_router, new_router, 1)
        router_path.write_text(router_content, encoding="utf-8")
        print("2. Đã cập nhật router.py (kích hoạt uncertain cho fallback)")
    else:
        print("2. router.py đã được cập nhật trước đó.")

    # 3. retriever.py
    ret_path = ROOT / "src" / "FPTUniQA" / "retrieval" / "retriever.py"
    ret_content = ret_path.read_text(encoding="utf-8")
    if "parallel: bool = False" not in ret_content:
        old_ret = "parallel: bool = True,"
        new_ret = "parallel: bool = False,  # Mặc định tuần tự để tránh overhead thread/GIL trên CPU"
        assert old_ret in ret_content, "old_ret not found in retriever.py"
        ret_content = ret_content.replace(old_ret, new_ret, 1)
        ret_path.write_text(ret_content, encoding="utf-8")
        print("3. Đã cập nhật retriever.py (parallel = False)")
    else:
        print("3. retriever.py đã được cập nhật trước đó.")

    # 4. safety_gate.py & external_orgs.json
    sg_path = ROOT / "src" / "FPTUniQA" / "query" / "safety_gate.py"
    sg_content = sg_path.read_text(encoding="utf-8")

    # Add privilege escalation patterns
    old_pat = '"api_key", "secret_key", "database password", "admin password"'
    new_pat = '"api_key", "secret_key", "database password", "admin password",\n    "tôi là trưởng phòng", "tôi là hiệu trưởng", "tôi ra lệnh", "ra lệnh cho bạn", "đóng vai trưởng phòng", "cấp bằng ngay lập tức", "xác nhận tốt nghiệp ngay"'
    
    ext_path = ROOT / "data" / "dictionary" / "external_orgs.json"
    ext_content = ext_path.read_text(encoding="utf-8")
    if "tôi là trưởng phòng" not in ext_content:
        ext_content = ext_content.replace(old_pat, new_pat, 1)
        ext_path.write_text(ext_content, encoding="utf-8")
        print("4a. Đã bổ sung mẫu mạo danh thẩm quyền vào external_orgs.json")
    else:
        print("4a. external_orgs.json đã có mẫu mạo danh.")

    # Update safety_gate.py whitelist
    if "is_transfer" not in sg_content:
        target_block = """    # 2. Kiểm tra câu hỏi trường khác (Near-OOD) và học bổng ngoài FPT
    # Lưu ý: Whitelist nếu câu hỏi nhấn mạnh Đại học FPT
    is_fpt_mention = "fpt" in q_lower or "đại học fpt" in q_lower

    for uni in _EXTERNAL_UNIS:"""

        replacement_block = """    # 2. Kiểm tra câu hỏi trường khác (Near-OOD) và học bổng ngoài FPT
    # Lưu ý: Whitelist nếu câu hỏi nhấn mạnh hỏi thủ tục chuyển trường sang FPT
    is_fpt_mention = "fpt" in q_lower or "đại học fpt" in q_lower or "dh fpt" in q_lower
    is_transfer = any(w in q_lower for w in ["chuyển trường", "chuyen truong", "chuyển sang", "chuyen sang", "so sánh"])
    if is_fpt_mention and is_transfer:
        return None  # Whitelist hợp lệ: sinh viên hỏi chuyển tiếp vào FPT

    for uni in _EXTERNAL_UNIS:"""

        assert target_block in sg_content, "target_block not found in safety_gate.py"
        sg_content = sg_content.replace(target_block, replacement_block, 1)
        sg_path.write_text(sg_content, encoding="utf-8")
        print("4b. Đã cập nhật safety_gate.py (whitelist chuyển trường)")
    else:
        print("4b. safety_gate.py đã có whitelist chuyển trường.")

if __name__ == "__main__":
    apply_improvements()
    print("HOÀN THÀNH TẤT CẢ CÁC BƯỚC CẢI TIẾN KỸ THUẬT!")

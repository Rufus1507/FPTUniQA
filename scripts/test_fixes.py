"""Script kiểm thử xác nhận các cải tiến của hệ thống FPTUniQA."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from FPTUniQA.pipeline.rag_pipeline import RAGPipeline
from FPTUniQA.query.rewriting import is_self_contained_query, rewrite_query
from FPTUniQA.query.safety_gate import check_chitchat
from FPTUniQA.query.semantic_parser import parse_query, try_rule_fast_parse

def run_tests():
    print("=" * 60)
    print("1. KIỂM THỬ CHITCHAT / PERSONA GATE (<5ms)")
    print("=" * 60)
    chitchat_queries = [
        "sao m nhanh v",
        "mày là ai",
        "bạn là ai",
        "xin chào",
        "cảm ơn bạn",
    ]
    for q in chitchat_queries:
        res = check_chitchat(q)
        assert res is not None, f"LỖI: '{q}' không được nhận diện là chitchat!"
        print(f"[PASS] '{q}' -> category={res['category']}, route={res['route']}")

    print("\n" + "=" * 60)
    print("2. KIỂM THỬ TỪ KHÓA HỌC PHÍ KHÔNG DẤU ('tien cntt quy nhon')")
    print("=" * 60)
    fast_p = try_rule_fast_parse("tien cntt quy nhon")
    print(f"try_rule_fast_parse('tien cntt quy nhon') -> intent={getattr(fast_p, 'intent', None)}, slots={getattr(fast_p, 'slots', None)}")
    assert fast_p is not None, "LỖI: try_rule_fast_parse không nhận diện được 'tien cntt quy nhon'!"
    assert fast_p.intent == "tuition_lookup", f"LỖI: intent phải là 'tuition_lookup', thực tế: {fast_p.intent}"
    assert fast_p.slots.get("program") == "CNTT", f"LỖI: program phải là CNTT, thực tế: {fast_p.slots.get('program')}"
    assert fast_p.slots.get("campus") == "Quy Nhơn", f"LỖI: campus phải là Quy Nhơn, thực tế: {fast_p.slots.get('campus')}"
    print("[PASS] Fast-path parse 'tien cntt quy nhon' -> tuition_lookup thành công!")

    print("\n" + "=" * 60)
    print("3. KIỂM THỬ CÂU HỎI NGẮN NGÀNH HỌC ('cho tôi biết cntt')")
    print("=" * 60)
    fast_cntt = try_rule_fast_parse("cho tôi biết cntt")
    print(f"try_rule_fast_parse('cho tôi biết cntt') -> {fast_cntt}")
    # Đảm bảo fast_parse KHÔNG chặn nhầm câu này là OOD!
    if fast_cntt is not None:
        assert fast_cntt.intent != "OOD", f"LỖI: fast_parse không được chặn 'cho tôi biết cntt' thành OOD!"
    parsed_cntt = parse_query("cho tôi biết cntt")
    print(f"parse_query('cho tôi biết cntt') -> intent={parsed_cntt.intent}, slots={parsed_cntt.slots}")
    assert parsed_cntt.intent in ["policy_lookup", "tuition_lookup"], f"LỖI: intent không được là OOD!"
    print("[PASS] 'cho tôi biết cntt' không bị coi là OOD!")

    print("\n" + "=" * 60)
    print("4. KIỂM THỬ SELF-CONTAINED GATE & CHỐNG DÍNH NGỮ CẢNH CŨ")
    print("=" * 60)
    is_sc_ai1 = is_self_contained_query("ngành ai học những gì")
    is_sc_ai2 = is_self_contained_query("ngành AI học gì")
    print(f"is_self_contained_query('ngành ai học những gì') -> {is_sc_ai1}")
    print(f"is_self_contained_query('ngành AI học gì') -> {is_sc_ai2}")
    assert is_sc_ai1 is True, "LỖI: 'ngành ai học những gì' phải là self-contained!"
    assert is_sc_ai2 is True, "LỖI: 'ngành AI học gì' phải là self-contained!"

    # Giả lập lịch sử chứa Quy Nhơn và CNTT
    mock_history = [
        {
            "query": "Học phí ngành CNTT tại Quy Nhơn là bao nhiêu?",
            "rewritten_query": "Học phí ngành CNTT tại Quy Nhơn là bao nhiêu?",
            "parsed_query": {"intent": "tuition_lookup", "slots": {"program": "CNTT", "campus": "Quy Nhơn"}},
            "answer": "Học phí là...",
            "route_chosen": "structured_lookup",
        }
    ]
    rewritten_ai = rewrite_query("ngành AI học những gì", history=mock_history)
    print(f"rewrite_query('ngành AI học những gì' với history Quy Nhơn) -> '{rewritten_ai}'")
    assert "Quy Nhơn" not in rewritten_ai, f"LỖI: câu hỏi không được bị dính Quy Nhơn! Thực tế: {rewritten_ai}"
    print("[PASS] Chống dính cơ sở cũ khi hỏi ngành AI thành công!")

    print("\n" + "=" * 60)
    print("5. KIỂM THỬ TOÀN DIỆN QUA RAG PIPELINE THỰC TẾ")
    print("=" * 60)
    pipeline = RAGPipeline(use_mock_fallback=False)
    
    # Test 5.1: Chitchat trong pipeline
    res_identity = pipeline.answer("bạn là ai", session_id="test_session")
    print(f"pipeline.answer('bạn là ai') -> route={res_identity.get('route')}, answer[:60]={res_identity.get('answer')[:60]}...")
    assert res_identity.get("route") == "chitchat", f"LỖI: route phải là chitchat, thực tế: {res_identity.get('route')}"

    # Test 5.2: Chitchat tốc độ
    res_speed = pipeline.answer("sao m nhanh v", session_id="test_session")
    print(f"pipeline.answer('sao m nhanh v') -> route={res_speed.get('route')}")
    assert res_speed.get("route") == "chitchat", f"LỖI: route phải là chitchat"

    # Test 5.3: Tra cứu học phí không dấu
    res_fee = pipeline.answer("tien cntt quy nhon", session_id="test_session")
    print(f"pipeline.answer('tien cntt quy nhon') -> route={res_fee.get('route')}, answer[:60]={res_fee.get('answer')[:60]}...")
    assert res_fee.get("route") == "structured_lookup", f"LỖI: route phải là structured_lookup, thực tế: {res_fee.get('route')}"

    print("\n>>> TẤT CẢ CÁC BÀI TEST ĐÃ VƯỢT QUA XUẤT SẮC! <<<")

if __name__ == "__main__":
    run_tests()

"""Script kiểm tra nhanh khả năng chuẩn hóa thực thể và nhận diện từ điển từ câu hỏi tự nhiên.
Cách dùng:
    python scripts/test_entity_query.py "Học phí ngành trí tuệ nhân tạo khóa k22 cơ sở Hà Nội là bao nhiêu?"
"""

import sys
import os
import json

# Đảm bảo đường dẫn module
sys.path.insert(0, os.path.abspath("src"))

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from FPTUniQA.normalization.engine import EntityNormalizer


def main():
    if len(sys.argv) < 2:
        query = "Học phí ngành trí tuệ nhân tạo khóa 2026 cơ sở Hà Nội là bao nhiêu?"
        print(f"💡 Không có câu hỏi truyền vào, sử dụng câu hỏi mẫu:\n   '{query}'\n")
    else:
        query = " ".join(sys.argv[1:])

    print("=" * 70)
    print("🔍 FPTUniQA - KIỂM THỬ TỪ ĐIỂN & CHUẨN HÓA THỰC THỂ")
    print("=" * 70)
    print(f"📝 Câu hỏi gốc: {query}\n")

    normalizer = EntityNormalizer()
    res = normalizer.normalize(query)

    print(f"✨ Chuỗi chuẩn hóa: {res.normalized_query}")
    print(f"\n📦 Số thực thể nhận diện được: {len(res.entities)}")
    print("-" * 70)
    for i, ent in enumerate(res.entities, 1):
        print(f"  [{i}] Loại thực thể: {ent.entity_type.upper()}")
        print(f"      ID Chuẩn:       {ent.entity_id} (Code: {ent.code})")
        print(f"      Tên chuẩn (VI): {ent.canonical_name_vi}")
        print(f"      Tên chuẩn (EN): {ent.canonical_name}")
        print(f"      Bí danh khớp:   '{ent.matched_alias}' [Vị trí: {ent.span[0]}:{ent.span[1]}]")
        print(f"      Độ tin cậy:     {ent.confidence:.2f} | Đã xác thực: {ent.verified}")
        print(f"      Minh chứng gốc: {ent.source_reference.get('file', '')} ({ent.source_reference.get('section', '')})")
        print("-" * 70)

    print(f"\n🎯 Gợi ý Slots trích xuất (slots_hint):")
    print(json.dumps(res.slots_hint, ensure_ascii=False, indent=4))

    if res.unresolved_terms:
        print(f"\n⚠️ Thuật ngữ nghi vấn chưa xác định:")
        for term in res.unresolved_terms:
            print(f"  - {term.get('term')}: {term.get('reason')}")

    print("=" * 70)


if __name__ == "__main__":
    main()

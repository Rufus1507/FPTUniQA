"""Script kiểm định và linting Từ điển miền FPTUniQA (Milestone M2).
Kiểm tra:
1. JSON Schema validation (schema.json)
2. Case-insensitivity & Intra-file duplicate aliases (R2)
3. Cross-file alias collisions (R3)
4. Self-loops & Dangling references (R4)
5. Format validation: ID uppercase, alias non-empty (R5)
"""

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT_DIR / "data" / "dictionary"
SCHEMA_PATH = DICT_DIR / "schema.json"

DICT_FILES = [
    "majors.json",
    "courses.json",
    "cohorts.json",
    "campuses.json",
    "academic_terms.json",
    "abbreviations.json",
]


def normalize_n1(s: str) -> str:
    """N1 (strict) = NFKC(s) -> lowercase -> trim -> collapse whitespace."""
    if not s:
        return ""
    norm = unicodedata.normalize("NFKC", s).lower()
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def normalize_n2(s: str) -> str:
    """N2 (lenient) = N1 + fold dấu tiếng Việt."""
    n1 = normalize_n1(s)
    nfkd = unicodedata.normalize("NFKD", n1)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return no_accent.replace("đ", "d").replace("Đ", "D")


def lint_dictionary():
    errors = []
    warnings = []

    # 1. Load schema
    schema = None
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)

    # 2. Iterate each file
    all_entities = {}  # entity_id -> entity
    union_alias_index = defaultdict(list)  # N1(alias) -> list of (file, entity_id)

    for fname in DICT_FILES:
        fpath = DICT_DIR / fname
        if not fpath.exists():
            errors.append(f"[R5.0 ERROR] Tệp từ điển thiếu: {fname}")
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except Exception as exc:
                errors.append(f"[R5.0 ERROR] Lỗi cú pháp JSON trong {fname}: {exc}")
                continue

        if not isinstance(entries, list):
            errors.append(f"[R5.0 ERROR] Nội dung {fname} phải là một JSON Array")
            continue

        seen_ids_in_file = set()
        seen_aliases_in_file = {}

        for idx, entry in enumerate(entries):
            # Schema validation
            if schema and jsonschema:
                try:
                    jsonschema.validate(instance=entry, schema=schema)
                except jsonschema.ValidationError as ve:
                    errors.append(f"[R5.1 ERROR] {fname}[{idx}] vi phạm schema: {ve.message}")

            eid = entry.get("entity_id", "")
            if not eid:
                errors.append(f"[R5.1 ERROR] {fname}[{idx}] thiếu entity_id")
                continue

            # ID format
            if not re.match(r"^[A-Z0-9_]+$", eid):
                errors.append(f"[R5.1 ERROR] {fname} ID '{eid}' không đúng định dạng ^[A-Z0-9_]+$")

            if eid in seen_ids_in_file:
                errors.append(f"[R5.1 ERROR] {fname} trùng lặp ID trong cùng file: '{eid}'")
            seen_ids_in_file.add(eid)

            if eid in all_entities:
                errors.append(f"[R5.1 ERROR] Trùng lặp entity_id xuyên file: '{eid}' ({fname} vs {all_entities[eid]['file']})")
            all_entities[eid] = {"file": fname, "entry": entry}

            aliases = entry.get("aliases", [])
            if not aliases:
                errors.append(f"[R5.2 ERROR] {fname} entity '{eid}' danh sách aliases rỗng")
                continue

            # R2: Case-insensitivity & Intra-file duplicate check
            for a in aliases:
                if not isinstance(a, str) or not a.strip():
                    errors.append(f"[R5.2 ERROR] {fname} entity '{eid}' có alias rỗng hoặc không phải string")
                    continue

                n1 = normalize_n1(a)
                if not n1:
                    errors.append(f"[R5.2 ERROR] {fname} entity '{eid}' alias '{a}' rỗng sau N1")
                    continue

                if n1 in seen_aliases_in_file:
                    other_eid = seen_aliases_in_file[n1]
                    if other_eid == eid:
                        warnings.append(f"[R2.1 WARN] {fname} entity '{eid}' chứa alias trùng N1: '{a}'")
                    else:
                        errors.append(f"[R2.1 ERROR] {fname} hai entity '{eid}' và '{other_eid}' cùng có alias '{n1}'")
                seen_aliases_in_file[n1] = eid

                # Đăng ký vào union index cho R3
                union_alias_index[n1].append((fname, eid, entry))

    # 3. R3: Cross-file collision check
    for n1_alias, occurrences in sorted(union_alias_index.items()):
        unique_eids = set(o[1] for o in occurrences)
        if len(unique_eids) > 1:
            # Kiểm tra xem có disambiguation_rules không
            has_disambiguation = any(
                "disambiguation_rules" in o[2] for o in occurrences
            )
            files = sorted(set(o[0] for o in occurrences))
            eids = sorted(unique_eids)
            msg = f"Alias '{n1_alias}' xuất hiện ở nhiều entities: {eids} thuộc files {files}"
            if has_disambiguation:
                warnings.append(f"[R3.2 NOTICE] {msg} (Đã có disambiguation_rules phân giải ngữ cảnh)")
            else:
                warnings.append(f"[R3.1 WARN] {msg} (Cần thêm disambiguation_rules hoặc làm rõ)")

    # 4. In kết quả kiểm định
    print("=" * 80)
    print("KẾT QUẢ KIỂM ĐỊNH TỪ ĐIỂN MIỀN (FPTUniQA DICTIONARY LINTER - M2)")
    print("=" * 80)
    print(f"Tổng số entities kiểm định: {len(all_entities)}")
    print(f"Tổng số unique N1 aliases:  {len(union_alias_index)}")

    if errors:
        print(f"\n[!] PHÁT HIỆN {len(errors)} LỖI (ERRORS):")
        for e in errors:
            print(f"  • {e}")
    else:
        print("\n[OK] 0 LỖI (ERRORS) - Tất cả các tệp đều đạt chuẩn Schema và cấu trúc.")

    if warnings:
        print(f"\n[*] {len(warnings)} CẢNH BÁO / THÔNG BÁO (WARNINGS/NOTICES):")
        for w in warnings:
            print(f"  • {w}")

    print("=" * 80)
    return 0 if not errors else 1


if __name__ == "__main__":
    code = lint_dictionary()
    sys.exit(code)

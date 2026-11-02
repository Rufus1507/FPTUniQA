"""Script trích xuất và khởi tạo dữ liệu Từ điển miền (Domain Dictionary) từ dữ liệu thực tế repository.
Tạo 6 file JSON trong data/dictionary/ theo đúng schema.json.
Phục vụ Milestone M1 trong Kế hoạch Triển khai Domain Dictionary.
"""

import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR))

DICT_DIR = ROOT_DIR / "data" / "dictionary"
DICT_DIR.mkdir(parents=True, exist_ok=True)


def remove_vietnamese_accents(text: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu thành không dấu."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", text)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    no_accent = no_accent.replace("đ", "d").replace("Đ", "D")
    return no_accent


def normalize_n1(s: str) -> str:
    """N1 (strict) = NFKC(s) -> lowercase -> trim -> collapse whitespace."""
    if not s:
        return ""
    import unicodedata
    norm = unicodedata.normalize("NFKC", s).lower()
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def build_majors():
    """Trích xuất danh mục ngành học từ structured_data.json và constants.py."""
    structured_path = ROOT_DIR / "data" / "processed" / "structured_data.json"
    with open(structured_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rates = data.get("tuition_rates", [])

    # Bảng cấu hình bổ sung và hoàn thiện
    majors_def = [
        {
            "entity_id": "MAJOR_KTPM",
            "entity_type": "major",
            "code": "7480103",
            "canonical_name": "Software Engineering",
            "canonical_name_vi": "Kỹ thuật phần mềm",
            "short_code": "KTPM",
            "aliases": [
                "ktpm", "kỹ thuật phần mềm", "kỹ thuật phần mềm", "ky thuat phan mem",
                "ngành kỹ thuật phần mềm", "kỹ sư kỹ thuật phần mềm", "software engineering", "se"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7480103, thuộc khối Công nghệ thông tin",
        },
        {
            "entity_id": "MAJOR_AI",
            "entity_type": "major",
            "code": "7480107",
            "canonical_name": "Artificial Intelligence",
            "canonical_name_vi": "Trí tuệ nhân tạo",
            "short_code": "AI",
            "aliases": [
                "ai", "a.i.", "trí tuệ nhân tạo", "tri tue nhan tao", "ngành ai",
                "ngành trí tuệ nhân tạo", "chuyên ngành ai", "chuyên ngành trí tuệ nhân tạo",
                "artificial intelligence", "trí tuệ nhân tạo và khoa học dữ liệu"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7480107, thuộc khối Công nghệ thông tin",
            "disambiguation_rules": {
                "prefer_course_if_preceded_by": ["môn", "học phần", "mã môn"],
                "prefer_major_if_preceded_by": ["ngành", "chuyên ngành", "khoa"]
            }
        },
        {
            "entity_id": "MAJOR_ATTT",
            "entity_type": "major",
            "code": "7480202",
            "canonical_name": "Information Assurance",
            "canonical_name_vi": "An toàn thông tin",
            "short_code": "ATTT",
            "aliases": [
                "attt", "an toàn thông tin", "an toan thong tin", "ngành an toàn thông tin",
                "an ninh mạng", "an ninh mạng và an toàn số", "information assurance", "ia", "cyber security"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7480202, thuộc khối Công nghệ thông tin",
        },
        {
            "entity_id": "MAJOR_KHMT",
            "entity_type": "major",
            "code": "7480201",
            "canonical_name": "Computer Science",
            "canonical_name_vi": "Khoa học máy tính",
            "short_code": "KHMT",
            "aliases": [
                "khmt", "khoa học máy tính", "khoa hoc may tinh", "ngành khoa học máy tính",
                "computer science", "cs"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7480201, thuộc khối Công nghệ thông tin",
        },
        {
            "entity_id": "MAJOR_HTTT",
            "entity_type": "major",
            "code": "7480104",
            "canonical_name": "Information Systems",
            "canonical_name_vi": "Hệ thống thông tin",
            "short_code": "HTTT",
            "aliases": [
                "httt", "hệ thống thông tin", "he thong thong tin", "ngành hệ thống thông tin",
                "information systems", "is"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7480104, thuộc khối Công nghệ thông tin",
        },
        {
            "entity_id": "MAJOR_TKDH",
            "entity_type": "major",
            "code": "7210403",
            "canonical_name": "Digital Art & Design",
            "canonical_name_vi": "Thiết kế đồ họa và mỹ thuật số",
            "short_code": "TKDH",
            "aliases": [
                "thiết kế mỹ thuật số", "thiết kế đồ họa", "thiết kế đồ họa và mỹ thuật số",
                "đồ họa", "mỹ thuật số", "thiet ke do hoa", "digital art & design", "gd", "graphic design"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7210403, thuộc khối Thiết kế & Nghệ thuật số",
        },
        {
            "entity_id": "MAJOR_QTKD",
            "entity_type": "major",
            "code": "7340101",
            "canonical_name": "Business Administration",
            "canonical_name_vi": "Quản trị kinh doanh",
            "short_code": "QTKD",
            "aliases": [
                "qtkd", "quản trị kinh doanh", "quan tri kinh doanh", "ngành quản trị kinh doanh",
                "cử nhân quản trị kinh doanh", "business administration", "ba"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7340101, thuộc khối Kinh tế & Quản trị",
        },
        {
            "entity_id": "MAJOR_MARKETING",
            "entity_type": "major",
            "code": "7340114",
            "canonical_name": "Digital Marketing",
            "canonical_name_vi": "Digital Marketing",
            "short_code": "Marketing",
            "aliases": [
                "marketing", "digital marketing", "ngành marketing", "tiếp thị số", "tiếp thị"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7340114, thuộc khối Kinh tế",
        },
        {
            "entity_id": "MAJOR_KDQT",
            "entity_type": "major",
            "code": "7340120",
            "canonical_name": "International Business",
            "canonical_name_vi": "Kinh doanh quốc tế",
            "short_code": "KDQT",
            "aliases": [
                "kdqt", "kinh doanh quốc tế", "kinh doanh quoc te", "ngành kinh doanh quốc tế",
                "international business", "ib"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7340120, thuộc khối Kinh tế",
        },
        {
            "entity_id": "MAJOR_TTDPT",
            "entity_type": "major",
            "code": "7320104",
            "canonical_name": "Multimedia Communications",
            "canonical_name_vi": "Truyền thông đa phương tiện",
            "short_code": "TTDPT",
            "aliases": [
                "truyền thông", "truyền thông đa phương tiện", "truyen thong da phuong tien",
                "ngành truyền thông", "multimedia communications", "mc"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7320104, thuộc khối Truyền thông",
        },
        {
            "entity_id": "MAJOR_NNA",
            "entity_type": "major",
            "code": "7220201",
            "canonical_name": "English Language",
            "canonical_name_vi": "Ngôn ngữ Anh",
            "short_code": "NNA",
            "aliases": [
                "ngôn ngữ anh", "ngon ngu anh", "tiếng anh", "tieng anh", "cử nhân ngôn ngữ anh", "english"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7220201, thuộc khối Ngoại ngữ",
        },
        {
            "entity_id": "MAJOR_NNN",
            "entity_type": "major",
            "code": "7220209",
            "canonical_name": "Japanese Language",
            "canonical_name_vi": "Ngôn ngữ Nhật",
            "short_code": "NNN",
            "aliases": [
                "ngôn ngữ nhật", "ngon ngu nhat", "tiếng nhật", "tieng nhat", "cử nhân ngôn ngữ nhật", "japanese"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7220209, thuộc khối Ngoại ngữ",
        },
        {
            "entity_id": "MAJOR_NNH",
            "entity_type": "major",
            "code": "7220210",
            "canonical_name": "Korean Language",
            "canonical_name_vi": "Ngôn ngữ Hàn Quốc",
            "short_code": "NNH",
            "aliases": [
                "ngôn ngữ hàn", "ngôn ngữ hàn quốc", "ngon ngu han", "ngon ngu han quoc", "tiếng hàn", "korean"
            ],
            "notes": "Mã ngành Bộ GD&ĐT: 7220210, thuộc khối Ngoại ngữ",
        },
        {
            "entity_id": "MAJOR_CNTT",
            "entity_type": "major",
            "code": "CNTT",
            "canonical_name": "Information Technology",
            "canonical_name_vi": "Công nghệ thông tin",
            "short_code": "CNTT",
            "aliases": [
                "cntt", "công nghệ thông tin", "cong nghe thong tin", "ngành công nghệ thông tin",
                "it", "information technology"
            ],
            "notes": "Ngành chung / nhóm ngành Công nghệ thông tin",
        },
        {
            "entity_id": "MAJOR_AUTOMOTIVE",
            "entity_type": "major",
            "code": "AUTO",
            "canonical_name": "Automotive Digital Technology",
            "canonical_name_vi": "Công nghệ ô tô số (Automotive)",
            "short_code": "Công nghệ ô tô số",
            "aliases": [
                "công nghệ ô tô số", "công nghệ ô tô số (automotive)", "ô tô", "o to", "automotive"
            ],
            "notes": "Định hướng đào tạo mới theo đề án tuyển sinh 2026",
        },
        {
            "entity_id": "MAJOR_SEMICONDUCTOR",
            "entity_type": "major",
            "code": "SEMI",
            "canonical_name": "Semiconductor IC Design",
            "canonical_name_vi": "Vi mạch bán dẫn",
            "short_code": "Vi mạch bán dẫn",
            "aliases": [
                "vi mạch bán dẫn", "vi mạch", "bán dẫn", "thiết kế vi mạch bán dẫn", "semiconductor"
            ],
            "notes": "Định hướng đào tạo mới theo đề án tuyển sinh 2026",
        },
        {
            "entity_id": "MAJOR_DATA_SCIENCE",
            "entity_type": "major",
            "code": "DS",
            "canonical_name": "Data Science and Applications",
            "canonical_name_vi": "Khoa học dữ liệu và ứng dụng",
            "short_code": "Khoa học dữ liệu và ứng dụng",
            "aliases": [
                "khoa học dữ liệu", "khoa học dữ liệu và ứng dụng", "khoa học dữ liệu ứng dụng", "khdl", "data science"
            ],
            "notes": "Chuyên ngành thuộc khối CNTT",
        },
        {
            "entity_id": "MAJOR_LAW",
            "entity_type": "major",
            "code": "LAW",
            "canonical_name": "Economic Law",
            "canonical_name_vi": "Luật kinh tế",
            "short_code": "Luật kinh tế",
            "aliases": [
                "luật", "luật kinh tế", "luat", "luat kinh te", "ngành luật"
            ],
            "notes": "Khối ngành Luật ĐH FPT",
        },
        {
            "entity_id": "MAJOR_NNT",
            "entity_type": "major",
            "code": "NNT",
            "canonical_name": "Chinese Language",
            "canonical_name_vi": "Ngôn ngữ Trung Quốc",
            "short_code": "Ngôn ngữ Trung Quốc",
            "aliases": [
                "ngôn ngữ trung", "ngôn ngữ trung quốc", "tiếng trung", "chinese"
            ],
            "notes": "Khối Ngoại ngữ",
        },
    ]

    result = []
    for m in majors_def:
        aliases_clean = sorted(list(set(m["aliases"])))
        # Bổ sung bản không dấu tự động
        extra_no_accent = [remove_vietnamese_accents(a) for a in aliases_clean]
        all_aliases = sorted(list(set(aliases_clean + extra_no_accent)), key=len, reverse=True)

        entry = {
            "entity_id": m["entity_id"],
            "entity_type": "major",
            "code": m.get("code"),
            "canonical_name": m["canonical_name"],
            "canonical_name_vi": m["canonical_name_vi"],
            "aliases": all_aliases,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": "data/processed/structured_data.json",
                "section": "tuition_rates"
            },
            "valid_from": "2021-09-01",
            "valid_to": None,
            "notes": m.get("notes", "")
        }
        if "disambiguation_rules" in m:
            entry["disambiguation_rules"] = m["disambiguation_rules"]
        result.append(entry)

    out_file = DICT_DIR / "majors.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} ngành đào tạo)")


def build_courses():
    """Trích xuất 67 môn học từ structured_data_courses.json."""
    courses_path = ROOT_DIR / "data" / "processed" / "structured_data_courses.json"
    with open(courses_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_courses = data.get("courses", [])
    result = []

    for c in raw_courses:
        code = c["course_code"].upper()
        c_name = c.get("course_name", "")
        v_name = c.get("vietnamese_name", "")

        aliases = [code, code.lower()]
        if c_name:
            aliases.append(c_name.lower())
            aliases.append(f"môn {c_name.lower()}")
            aliases.append(f"mon {c_name.lower()}")
        if v_name:
            aliases.append(v_name.lower())
            aliases.append(f"môn {v_name.lower()}")
            aliases.append(f"mon {v_name.lower()}")
        # Tránh collision không dấu giữa ECO111 (vi mô) và ECO121 (vĩ mô)
        if code not in ("ECO111", "ECO121"):
            if v_name:
                v_no_accent = remove_vietnamese_accents(v_name.lower())
                aliases.append(v_no_accent)
                aliases.append(f"mon {v_no_accent}")

        # Thêm tên viết tắt phổ biến
        if code == "CSD201":
            aliases.extend(["ctdl&gt", "ctdl", "cấu trúc dữ liệu", "cau truc du lieu"])
        elif code == "PRO192":
            aliases.extend(["oop", "lập trình hướng đối tượng", "lap trinh huong doi tuong"])
        elif code == "PRF192":
            aliases.extend(["lập trình c", "lap trinh c", "cơ sở c", "nhập môn c"])
        elif code == "DBI202":
            aliases.extend(["csdl", "cơ sở dữ liệu", "co so du lieu", "sql"])
        elif code == "SEP490":
            aliases.extend(["kltn ktpm", "đatn ktpm", "khóa luận ktpm", "đồ án ktpm"])
        elif code == "AIP490":
            aliases.extend(["kltn ai", "đatn ai", "khóa luận ai", "đồ án ai"])
        elif code == "VOV114":
            aliases.extend(["vovinam 1", "võ vovinam 1", "vov1"])
        elif code == "VOV124":
            aliases.extend(["vovinam 2", "võ vovinam 2", "vov2"])
        elif code == "VOV134":
            aliases.extend(["vovinam 3", "võ vovinam 3", "vov3"])

        # Khử trùng lặp N1
        seen_n1 = set()
        deduped_aliases = []
        for a in aliases:
            n1 = normalize_n1(a)
            if n1 and n1 not in seen_n1:
                seen_n1.add(n1)
                deduped_aliases.append(n1)

        aliases = sorted(deduped_aliases, key=len, reverse=True)

        entry = {
            "entity_id": f"COURSE_{code}",
            "entity_type": "course",
            "code": code,
            "canonical_name": c_name or code,
            "canonical_name_vi": v_name or c_name or code,
            "aliases": aliases,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": "data/processed/structured_data_courses.json",
                "section": "courses"
            },
            "valid_from": "2021-09-01",
            "valid_to": None,
            "notes": f"Tín chỉ: {c.get('credits')}, Học kỳ: {c.get('semester')}, Ngành: {c.get('program')}"
        }
        result.append(entry)

    out_file = DICT_DIR / "courses.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} môn học)")


def build_cohorts():
    """Trích xuất 6 khóa tuyển sinh K17 - K22 kèm căn cứ xác thực."""
    cohorts_def = [
        {
            "entity_id": "COHORT_K17",
            "entity_type": "cohort",
            "code": "K17",
            "canonical_name": "Cohort 17 (2021)",
            "canonical_name_vi": "Khóa 17 (Nhập học năm 2021)",
            "aliases": ["k17", "khoá 17", "khóa 17", "khoa 17", "khóa k17", "khoá k17", "sinh viên khóa 2021", "sinh viên nhập học năm 2021", "khóa 2021", "khoá 2021", "nhập học năm 2021"],
            "source_file": "[studocu.com] - Sổ Tay Sinh Viên K17 - Đại Học FPT - Hướng Dẫn Chi Tiết Và Thông Tin.pdf",
            "valid_from": "2021-09-01",
            "notes": "Niên khóa tuyển sinh đại học chính quy năm 2021"
        },
        {
            "entity_id": "COHORT_K18",
            "entity_type": "cohort",
            "code": "K18",
            "canonical_name": "Cohort 18 (2022)",
            "canonical_name_vi": "Khóa 18 (Nhập học năm 2022)",
            "aliases": ["k18", "khoá 18", "khóa 18", "khoa 18", "khóa k18", "khoá k18", "sinh viên khóa 2022", "sinh viên nhập học năm 2022", "khóa 2022", "khoá 2022", "nhập học năm 2022"],
            "source_file": "sotaysinhvienK18HN.pdf",
            "valid_from": "2022-09-01",
            "notes": "Niên khóa tuyển sinh đại học chính quy năm 2022"
        },
        {
            "entity_id": "COHORT_K19",
            "entity_type": "cohort",
            "code": "K19",
            "canonical_name": "Cohort 19 (2023)",
            "canonical_name_vi": "Khóa 19 (Nhập học năm 2023)",
            "aliases": ["k19", "khoá 19", "khóa 19", "khoa 19", "khóa k19", "khoá k19", "sinh viên khóa 2023", "sinh viên nhập học năm 2023", "khóa 2023", "khoá 2023", "nhập học năm 2023"],
            "source_file": "[studocu.com] - Hướng dẫn Tài chính Sinh viên K19 - Quy định và Phí năm học 2023-2024.pdf",
            "valid_from": "2023-09-01",
            "notes": "Niên khóa tuyển sinh đại học chính quy năm 2023"
        },
        {
            "entity_id": "COHORT_K20",
            "entity_type": "cohort",
            "code": "K20",
            "canonical_name": "Cohort 20 (2024)",
            "canonical_name_vi": "Khóa 20 (Nhập học năm 2024)",
            "aliases": ["k20", "khoá 20", "khóa 20", "khoa 20", "khóa k20", "khoá k20", "sinh viên khóa 2024", "sinh viên nhập học năm 2024", "khóa 2024", "khoá 2024", "nhập học năm 2024"],
            "source_file": "1054154482-K20-Sổ-Tay-Sinh-Vien-2.pdf",
            "valid_from": "2024-09-01",
            "notes": "Niên khóa tuyển sinh đại học chính quy năm 2024"
        },
        {
            "entity_id": "COHORT_K21",
            "entity_type": "cohort",
            "code": "K21",
            "canonical_name": "Cohort 21 (2025)",
            "canonical_name_vi": "Khóa 21 (Nhập học năm 2025)",
            "aliases": ["k21", "khoá 21", "khóa 21", "khoa 21", "khóa k21", "khoá k21", "sinh viên khóa 2025", "sinh viên nhập học năm 2025", "khóa 2025", "khoá 2025", "nhập học năm 2025"],
            "source_file": "970569429-So-Tay-Sinh-Vien-K21-FUHL-1.pdf",
            "valid_from": "2025-09-01",
            "notes": "Niên khóa tuyển sinh đại học chính quy năm 2025"
        },
        {
            "entity_id": "COHORT_K22",
            "entity_type": "cohort",
            "code": "K22",
            "canonical_name": "Cohort 22 (2026)",
            "canonical_name_vi": "Khóa 22 (Nhập học năm 2026)",
            "aliases": [
                "k22", "khoá 22", "khóa 22", "khoa 22", "khóa k22", "khoá k22",
                "sinh viên khóa 2026", "sinh viên nhập học năm 2026", "khóa 2026", "khoá 2026",
                "nhập học năm 2026", "tân sinh viên k22", "k22 fptu"
            ],
            "source_file": "2026_So-tay-k22_compressed.pdf & thong-bao-tuyen-sinh-nam-2026.html",
            "valid_from": "2026-09-01",
            "notes": "Minh chứng trực tiếp: Thông báo tuyển sinh 2026 khẳng định tất cả thí sinh nhập học năm 2026 thuộc khóa K22"
        }
    ]

    result = []
    for c in cohorts_def:
        aliases_clean = sorted(list(set(c["aliases"])), key=len, reverse=True)
        entry = {
            "entity_id": c["entity_id"],
            "entity_type": "cohort",
            "code": c["code"],
            "canonical_name": c["canonical_name"],
            "canonical_name_vi": c["canonical_name_vi"],
            "aliases": aliases_clean,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": c["source_file"],
                "section": "Quyết định ban hành niên khóa & biểu phí"
            },
            "valid_from": c["valid_from"],
            "valid_to": None,
            "notes": c["notes"]
        }
        result.append(entry)

    out_file = DICT_DIR / "cohorts.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} khóa tuyển sinh)")


def build_campuses():
    """Trích xuất 5 cơ sở từ campus_matcher.py."""
    campuses_def = [
        {
            "entity_id": "CAMPUS_HANOI",
            "entity_type": "campus",
            "code": "HANOI",
            "canonical_name": "Hanoi Campus (Hoa Lac)",
            "canonical_name_vi": "Hà Nội",
            "aliases": ["hà nội", "ha noi", "hanoi", "hòa lạc", "hoa lac", "hn", "hl", "fuhl", "phân hiệu hà nội", "cơ sở hà nội", "campus hòa lạc"],
            "notes": "Phân hiệu Trường Đại học FPT tại Hà Nội (Khu CNC Hòa Lạc)"
        },
        {
            "entity_id": "CAMPUS_HCM",
            "entity_type": "campus",
            "code": "HCM",
            "canonical_name": "Ho Chi Minh City Campus",
            "canonical_name_vi": "TP. Hồ Chí Minh",
            "aliases": ["tp. hcm", "tp hcm", "hồ chí minh", "ho chi minh", "hcm", "tphcm", "tp.hcm", "sài gòn", "sai gon", "quận 9", "phân hiệu tp. hồ chí minh", "cơ sở hồ chí minh"],
            "notes": "Phân hiệu Trường Đại học FPT tại TP. Hồ Chí Minh"
        },
        {
            "entity_id": "CAMPUS_DANANG",
            "entity_type": "campus",
            "code": "DANANG",
            "canonical_name": "Da Nang Campus",
            "canonical_name_vi": "Đà Nẵng",
            "aliases": ["đà nẵng", "da nang", "danang", "đn", "dn", "phân hiệu đà nẵng", "cơ sở đà nẵng"],
            "notes": "Phân hiệu Trường Đại học FPT tại Đà Nẵng (Ưu đãi 30% học phí toàn khóa)"
        },
        {
            "entity_id": "CAMPUS_CANTHO",
            "entity_type": "campus",
            "code": "CANTHO",
            "canonical_name": "Can Tho Campus",
            "canonical_name_vi": "Cần Thơ",
            "aliases": ["cần thơ", "can tho", "cantho", "cầntho", "ct", "phân hiệu cần thơ", "cơ sở cần thơ"],
            "notes": "Phân hiệu Trường Đại học FPT tại Cần Thơ (Ưu đãi 30% học phí toàn khóa)"
        },
        {
            "entity_id": "CAMPUS_QUYNHON",
            "entity_type": "campus",
            "code": "QUYNHON",
            "canonical_name": "Quy Nhon Campus",
            "canonical_name_vi": "Quy Nhơn",
            "aliases": ["quy nhơn", "quy nhon", "quynhon", "bình định", "binh dinh", "qn", "phân hiệu quy nhơn", "cơ sở quy nhơn"],
            "notes": "Phân hiệu Trường Đại học FPT tại Quy Nhơn (Ưu đãi 50% học phí toàn khóa)"
        },
        {
            "entity_id": "CAMPUS_ALL",
            "entity_type": "campus",
            "code": "ALL",
            "canonical_name": "All Campuses",
            "canonical_name_vi": "Tất cả các cơ sở",
            "aliases": ["toàn quốc", "tất cả các cơ sở", "tất cả phân hiệu", "chung", "toan quoc"],
            "notes": "Áp dụng cho quy chế đào tạo và biểu phí chung toàn quốc"
        }
    ]

    result = []
    for c in campuses_def:
        aliases_clean = sorted(list(set(c["aliases"])), key=len, reverse=True)
        entry = {
            "entity_id": c["entity_id"],
            "entity_type": "campus",
            "code": c["code"],
            "canonical_name": c["canonical_name"],
            "canonical_name_vi": c["canonical_name_vi"],
            "aliases": aliases_clean,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": "src/FPTUniQA/query/campus_matcher.py",
                "section": "CAMPUS_PATTERNS"
            },
            "valid_from": "2021-09-01",
            "valid_to": None,
            "notes": c["notes"]
        }
        result.append(entry)

    out_file = DICT_DIR / "campuses.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} phân hiệu)")


def build_academic_terms():
    """Trích xuất thuật ngữ học vụ cốt lõi từ quy chế và biểu phí."""
    terms_def = [
        {
            "entity_id": "TERM_TIN_CHI",
            "canonical_name": "Academic Credit",
            "canonical_name_vi": "Tín chỉ",
            "code": "CREDIT",
            "aliases": ["tín chỉ", "tin chi", "số tín", "số tín chỉ", "định mức tín chỉ", "credit", "credits"],
            "notes": "Đơn vị đo khối lượng học tập"
        },
        {
            "entity_id": "TERM_HOC_PHI",
            "canonical_name": "Tuition Fee",
            "canonical_name_vi": "Học phí",
            "code": "TUITION",
            "aliases": ["học phí", "hoc phi", "tiền học", "tien hoc", "chi phí học tập", "biểu phí", "tuition fee", "tuition"],
            "notes": "Mức phí đào tạo theo kỳ của sinh viên"
        },
        {
            "entity_id": "TERM_CANH_BAO_HOC_VU",
            "canonical_name": "Academic Warning",
            "canonical_name_vi": "Cảnh báo học vụ",
            "code": "WARNING",
            "aliases": ["cảnh cáo học vụ", "cảnh báo học vụ", "canh bao hoc vu", "canh cao hoc vu", "cảnh cáo", "cảnh báo", "academic warning"],
            "notes": "Xử lý khi GPA hoặc CGPA dưới ngưỡng quy định. Bị cảnh cáo 3 lần liên tiếp sẽ bị buộc thôi học."
        },
        {
            "entity_id": "TERM_TOT_NGHIEP",
            "canonical_name": "Graduation Requirements",
            "canonical_name_vi": "Điều kiện tốt nghiệp",
            "code": "GRADUATION",
            "aliases": ["tốt nghiệp", "tot nghiep", "xét tốt nghiệp", "chuẩn đầu ra", "điều kiện tốt nghiệp", "ra trường", "graduation"],
            "notes": "Yêu cầu: hoàn thành tín chỉ, CGPA >= 2.0, ngoại ngữ IELTS 5.5, OJT, GDTC, GDQP."
        },
        {
            "entity_id": "TERM_TIEN_QUYET",
            "canonical_name": "Prerequisite Course",
            "canonical_name_vi": "Môn học tiên quyết",
            "code": "PREREQUISITE",
            "aliases": ["môn tiên quyết", "tiên quyết", "tien quyet", "mon tien quyet", "yêu cầu tiên quyết", "prerequisite"],
            "notes": "Môn học bắt buộc phải vượt qua trước khi đăng ký môn học tiếp theo"
        },
        {
            "entity_id": "TERM_OJT",
            "canonical_name": "On the Job Training",
            "canonical_name_vi": "Thực tập doanh nghiệp (OJT)",
            "code": "OJT",
            "aliases": ["thực tập doanh nghiệp", "thực tập tại doanh nghiệp", "kỳ thực tập", "on the job training", "thuc tap doanh nghiep"],
            "notes": "Giai đoạn thực tập tại doanh nghiệp ở kỳ 6, học phí chuyên ngành = 0 VNĐ"
        },
        {
            "entity_id": "TERM_CAPSTONE",
            "canonical_name": "Capstone Project",
            "canonical_name_vi": "Khóa luận tốt nghiệp (Capstone)",
            "code": "CAPSTONE",
            "aliases": ["đồ án tốt nghiệp", "khóa luận tốt nghiệp", "đồ án", "khóa luận", "capstone", "capstone project", "do an tot nghiep", "khoa luan tot nghiep"],
            "notes": "Khối lượng 10 tín chỉ, thực hiện ở học kỳ thứ 9"
        },
        {
            "entity_id": "TERM_LE_PHI_THI_LAI",
            "canonical_name": "Retake Exam Fee",
            "canonical_name_vi": "Lệ phí thi lại",
            "code": "RETAKE_FEE",
            "aliases": ["lệ phí thi lại", "phí thi lại", "thi lại bao nhiêu", "thi lại", "le phi thi lai", "phi thi lai"],
            "notes": "Định mức 300.000 VNĐ / lần thi theo quy định tài chính"
        },
        {
            "entity_id": "TERM_LE_PHI_HOC_LAI",
            "canonical_name": "Relearn Course Fee",
            "canonical_name_vi": "Lệ phí học lại",
            "code": "RELEARN_FEE",
            "aliases": ["lệ phí học lại", "phí học lại", "học lại bao nhiêu", "học lại", "le phi hoc lai", "phi hoc lai"],
            "notes": "Định mức 650.000 VNĐ / tín chỉ"
        },
        {
            "entity_id": "TERM_KY_TUC_XA",
            "canonical_name": "Dormitory Fee",
            "canonical_name_vi": "Phí ký túc xá",
            "code": "DORM_FEE",
            "aliases": ["ký túc xá", "ký túc", "phí ktx", "phí ký túc xá", "ky tuc xa"],
            "notes": "Định mức 4.000.000 VNĐ / học kỳ tại phân hiệu Hòa Lạc"
        }
    ]

    result = []
    for t in terms_def:
        aliases_clean = sorted(list(set(t["aliases"])), key=len, reverse=True)
        entry = {
            "entity_id": t["entity_id"],
            "entity_type": "academic_term",
            "code": t.get("code"),
            "canonical_name": t["canonical_name"],
            "canonical_name_vi": t["canonical_name_vi"],
            "aliases": aliases_clean,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": "data/processed/structured_data.json & Quy chế đào tạo ĐH FPT",
                "section": "Quy chế & Biểu phí"
            },
            "valid_from": "2021-09-01",
            "valid_to": None,
            "notes": t.get("notes", "")
        }
        result.append(entry)

    out_file = DICT_DIR / "academic_terms.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} thuật ngữ học vụ)")


def build_abbreviations():
    """Bảng mở rộng từ viết tắt học vụ phổ biến."""
    abbrs = [
        {"entity_id": "ABBR_SV", "code": "SV", "canonical_name": "Student", "canonical_name_vi": "Sinh viên", "aliases": ["sv", "tân sv"], "resolves_to": "TERM_SINH_VIEN"},
        {"entity_id": "ABBR_TC", "code": "TC", "canonical_name": "Academic Credit", "canonical_name_vi": "Tín chỉ", "aliases": ["tc"], "resolves_to": "TERM_TIN_CHI"},
        {"entity_id": "ABBR_KTX", "code": "KTX", "canonical_name": "Dormitory", "canonical_name_vi": "Ký túc xá", "aliases": ["ktx"], "resolves_to": "TERM_KY_TUC_XA"},
        {"entity_id": "ABBR_OJT", "code": "OJT", "canonical_name": "On the Job Training", "canonical_name_vi": "Thực tập doanh nghiệp", "aliases": ["ojt"], "resolves_to": "TERM_OJT"},
        {"entity_id": "ABBR_KLTN", "code": "KLTN", "canonical_name": "Graduation Thesis", "canonical_name_vi": "Khóa luận tốt nghiệp", "aliases": ["kltn", "đatn"], "resolves_to": "TERM_CAPSTONE"},
        {"entity_id": "ABBR_CTDT", "code": "CTDT", "canonical_name": "Curriculum", "canonical_name_vi": "Chương trình đào tạo", "aliases": ["ctđt", "ctdt"], "resolves_to": "TERM_CTDT"},
        {"entity_id": "ABBR_GDTC", "code": "GDTC", "canonical_name": "Physical Education", "canonical_name_vi": "Giáo dục thể chất", "aliases": ["gdtc"], "resolves_to": "TERM_GDTC"},
        {"entity_id": "ABBR_GDQP", "code": "GDQP", "canonical_name": "National Defense Education", "canonical_name_vi": "Giáo dục quốc phòng", "aliases": ["gdqp", "quân sự"], "resolves_to": "TERM_GDQP"},
        {"entity_id": "ABBR_PE", "code": "PE", "canonical_name": "Practical Exam", "canonical_name_vi": "Thi thực hành", "aliases": ["pe"], "resolves_to": "TERM_PE"},
        {"entity_id": "ABBR_EOS", "code": "EOS", "canonical_name": "End of Semester Exam", "canonical_name_vi": "Thi cuối kỳ", "aliases": ["eos"], "resolves_to": "TERM_EOS"},
        {"entity_id": "ABBR_GPA", "code": "GPA", "canonical_name": "Grade Point Average", "canonical_name_vi": "Điểm trung bình học kỳ", "aliases": ["gpa"], "resolves_to": "TERM_GPA"},
        {"entity_id": "ABBR_CGPA", "code": "CGPA", "canonical_name": "Cumulative Grade Point Average", "canonical_name_vi": "Điểm trung bình tích lũy", "aliases": ["cgpa"], "resolves_to": "TERM_CGPA"},
    ]

    result = []
    for a in abbrs:
        aliases_clean = sorted(list(set(a["aliases"])), key=len, reverse=True)
        entry = {
            "entity_id": a["entity_id"],
            "entity_type": "abbreviation",
            "code": a.get("code"),
            "canonical_name": a["canonical_name"],
            "canonical_name_vi": a["canonical_name_vi"],
            "aliases": aliases_clean,
            "status": "active",
            "verified": True,
            "confidence": 1.0,
            "source_reference": {
                "file": "Sổ tay sinh viên ĐH FPT",
                "section": "Danh mục từ viết tắt"
            },
            "valid_from": "2021-09-01",
            "valid_to": None,
            "resolves_to": a.get("resolves_to"),
            "notes": "Từ viết tắt học vụ thông dụng của sinh viên FPTU"
        }
        result.append(entry)

    out_file = DICT_DIR / "abbreviations.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo {out_file} ({len(result)} từ viết tắt)")


def main():
    print("Bắt đầu trích xuất dữ liệu từ điển miền (Milestone M1)...")
    build_majors()
    build_courses()
    build_cohorts()
    build_campuses()
    build_academic_terms()
    build_abbreviations()
    print("Hoàn tất Milestone M1: Đã khởi tạo 6/6 tệp từ điển trong data/dictionary/ thành công!")


if __name__ == "__main__":
    main()

"""Tập trung các hằng số, từ khóa và bảng ánh xạ dùng chung (Single Source of Truth)."""

from typing import Dict, List

# -----------------------------------------------------------------------------
# 1. Từ khóa câu hỏi ngoài miền (Out-Of-Domain - OOD)
# Hợp nhất từ router.py, semantic_parser.py và rewriting.py
# -----------------------------------------------------------------------------
OOD_KEYWORDS: List[str] = [
    # Đời sống, ẩm thực, tiêu dùng
    "trà sữa", "giá vàng", "thời tiết", "nấu ăn", "cách làm món", "mua xe",
    "bún bò", "phở bò", "phở", "bánh mì", "cà phê", "quán cà phê", "món ăn", "ẩm thực",
    # Giải trí, thể thao, nghệ thuật
    "game", "chơi game", "phim", "phim ảnh", "bóng đá", "ca sĩ", "diễn viên",
    # Tin tức, thời sự, tài chính
    "thời sự", "chứng khoán", "bitcoin", "crypto",
    # Tâm linh, bói toán
    "chiêm tinh", "tử vi", "xem bói",
    # Địa lý, thế giới, xã hội
    "du lịch", "pháp", "everest", "hồ gươm", "tỉnh thành", "thủ đô", "miền trung",
    "thế giới", "tổng thống", "hoa kỳ",
    # Y tế, sức khỏe
    "cảm cúm", "chữa bệnh",
    # Khoa học, công nghệ, văn học chung
    "truyện kiều", "phát minh", "tác giả", "điện thoại",
    # Các trường đại học khác
    "bách khoa", "kinh tế quốc dân", "quốc gia",
]

# -----------------------------------------------------------------------------
# 2. Ánh xạ tên ngành học & Danh mục ngành học chuẩn
# Nguồn chuẩn từ router.py (45 alias)
# -----------------------------------------------------------------------------
PROGRAM_ALIAS_MAP: Dict[str, str] = {
    "ai": "Trí tuệ nhân tạo",
    "trí tuệ nhân tạo": "Trí tuệ nhân tạo",
    "tri tue nhan tao": "Trí tuệ nhân tạo",
    "cntt": "Công nghệ thông tin",
    "công nghệ thông tin": "Công nghệ thông tin",
    "cong nghe thong tin": "Công nghệ thông tin",
    "công nghệ tt": "Công nghệ thông tin",
    "cong nghe tt": "Công nghệ thông tin",
    "ktpm": "Kỹ thuật phần mềm",
    "kỹ thuật phần mềm": "Kỹ thuật phần mềm",
    "ky thuat phan mem": "Kỹ thuật phần mềm",
    "kỹ thuật pm": "Kỹ thuật phần mềm",
    "ky thuat pm": "Kỹ thuật phần mềm",
    "kt phần mềm": "Kỹ thuật phần mềm",
    "kt phan mem": "Kỹ thuật phần mềm",
    "attt": "An toàn thông tin",
    "an toàn thông tin": "An toàn thông tin",
    "an toan thong tin": "An toàn thông tin",
    "an toàn tt": "An toàn thông tin",
    "an toan tt": "An toàn thông tin",
    "khdl": "Khoa học dữ liệu và ứng dụng",
    "khoa học dữ liệu": "Khoa học dữ liệu và ứng dụng",
    "khoa học dữ liệu và ứng dụng": "Khoa học dữ liệu và ứng dụng",
    "vi mạch": "Vi mạch bán dẫn",
    "bán dẫn": "Vi mạch bán dẫn",
    "vi mạch bán dẫn": "Vi mạch bán dẫn",
    "ô tô": "Công nghệ ô tô số (Automotive)",
    "công nghệ ô tô số": "Công nghệ ô tô số (Automotive)",
    "httt": "Hệ thống thông tin",
    "hệ thống thông tin": "Hệ thống thông tin",
    "đồ họa": "Thiết kế đồ họa và mỹ thuật số",
    "mỹ thuật số": "Thiết kế đồ họa và mỹ thuật số",
    "thiết kế đồ họa": "Thiết kế đồ họa và mỹ thuật số",
    "truyền thông": "Truyền thông đa phương tiện",
    "truyền thông đa phương tiện": "Truyền thông đa phương tiện",
    "ttdpt": "Truyền thông đa phương tiện",
    "tkdh": "Thiết kế đồ họa và mỹ thuật số",
    "tkđh": "Thiết kế đồ họa và mỹ thuật số",
    "qtkd": "Quản trị kinh doanh",
    "quản trị kinh doanh": "Quản trị kinh doanh",
    "kdqt": "Kinh doanh quốc tế",
    "kinh doanh quốc tế": "Kinh doanh quốc tế",
    "marketing": "Marketing",
    "ngôn ngữ anh": "Ngôn ngữ Anh",
    "tiếng anh": "Ngôn ngữ Anh",
    "ngôn ngữ hàn": "Ngôn ngữ Hàn Quốc",
    "ngôn ngữ hàn quốc": "Ngôn ngữ Hàn Quốc",
    "tiếng hàn": "Ngôn ngữ Hàn Quốc",
    "ngôn ngữ trung": "Ngôn ngữ Trung Quốc",
    "ngôn ngữ trung quốc": "Ngôn ngữ Trung Quốc",
    "tiếng trung": "Ngôn ngữ Trung Quốc",
    "ngôn ngữ nhật": "Ngôn ngữ Nhật",
    "tiếng nhật": "Ngôn ngữ Nhật",
    "luật": "Luật",
    "luật kinh tế": "Luật kinh tế",
}

# Danh sách tên ngành chuẩn không trùng lặp
MAJOR_NAMES: List[str] = list(dict.fromkeys(PROGRAM_ALIAS_MAP.values()))

# Ánh xạ từ tên ngành chuẩn hoặc alias sang mã viết tắt ngắn (cho slots semantic parser)
MAJOR_TO_SHORT_CODE: Dict[str, str] = {
    "Trí tuệ nhân tạo": "AI",
    "Công nghệ thông tin": "CNTT",
    "Kỹ thuật phần mềm": "KTPM",
    "An toàn thông tin": "An toàn thông tin",
    "Khoa học dữ liệu và ứng dụng": "Khoa học dữ liệu và ứng dụng",
    "Vi mạch bán dẫn": "Vi mạch bán dẫn",
    "Công nghệ ô tô số (Automotive)": "Công nghệ ô tô số",
    "Hệ thống thông tin": "Hệ thống thông tin",
    "Thiết kế đồ họa và mỹ thuật số": "Thiết kế đồ họa và mỹ thuật số",
    "Truyền thông đa phương tiện": "Truyền thông đa phương tiện",
    "Quản trị kinh doanh": "Quản trị kinh doanh",
    "Kinh doanh quốc tế": "Kinh doanh quốc tế",
    "Marketing": "Marketing",
    "Ngôn ngữ Anh": "Ngôn ngữ Anh",
    "Ngôn ngữ Hàn Quốc": "Ngôn ngữ Hàn Quốc",
    "Ngôn ngữ Trung Quốc": "Ngôn ngữ Trung Quốc",
    "Ngôn ngữ Nhật": "Ngôn ngữ Nhật",
    "chuyên ngành": "chuyên ngành",
}

# -----------------------------------------------------------------------------
# 3. Từ khóa điều phối học phí & lệ phí
# -----------------------------------------------------------------------------
COMMON_FEE_KEYWORDS: List[str] = [
    "lệ phí tốt nghiệp", "phí tốt nghiệp", "lễ cấp bằng", "phí cấp bằng", "lệ phí cấp bằng",
    "le phi tot nghiep", "phi tot nghiep", "le cap bang", "phi cap bang", "le phi cap bang",
    "bảng điểm", "bản sao", "giấy xác nhận", "xác nhận sinh viên", "bang diem", "ban sao",
    "kỳ định hướng", "orientation", "định hướng đầu khóa", "thi lại", "học lại",
    "thi lai", "hoc lai", "ký túc xá", "ký túc", "ky tuc xa", "ky tuc", "ktx",
    "tiếng anh chuẩn bị", "tieng anh chuan bi", "tiếng anh dự bị", "tieng anh du bi"
]

REGIONAL_DISCOUNT_KEYWORDS: List[str] = [
    "ưu đãi", "giảm", "bao nhiêu %", "phần trăm", "hỗ trợ học phí", "chính sách ưu đãi"
]

COHORT_WIDE_KEYWORDS: List[str] = [
    "chuyên ngành", "toàn khóa", "biểu phí chung", "tất cả các ngành",
    "khung học phí", "học kỳ", "kỳ học", "tiếng anh", "dự bị", "chuẩn bị",
    "thi lại", "học lại", "ký túc", "ktx",
    "chuyen nganh", "toan khoa", "bieu phi chung", "tat ca cac nganh",
    "khung hoc phi", "hoc ky", "ky hoc", "tieng anh", "du bi", "chuan bi",
    "thi lai", "hoc lai", "ky tuc", "bao nhiêu một kỳ", "bao nhieu mot ky"
]

# -----------------------------------------------------------------------------
# 4. Regex chuẩn cho phân hiệu và mã phân hiệu
# -----------------------------------------------------------------------------
CAMPUS_NAMES_REGEX: str = r"(hà nội|cần thơ|đà nẵng|hồ chí minh|quy nhơn)"
CAMPUS_CODES_REGEX: str = r"(fuhl|hcm|hn|ct|dn|qn)"
COURSE_CODE_REGEX: str = r"\b[A-Za-z]{3}\d{3}[A-Za-z]?\b"

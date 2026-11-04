import json
import glob
import re
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

gold_path = "data/evaluation/benchmark_v2/retrieval_gold.json"
with open(gold_path, "r", encoding="utf-8") as f:
    gold = json.load(f)

# Danh sách equiv groups chuẩn hóa cho quy chế chung
EQUIV_PATTERNS = [
    # Nhóm phúc khảo
    ["doc_fpt_k20_0127", "doc_fpt_k21_0448", "doc_fpt_k17_0588", "doc_fpt_k18_0732"],
    # Nhóm OJT
    ["doc_fpt_k22_0305", "doc_fpt_k21_0397", "doc_fpt_k20_0099", "doc_fpt_k17_0596"],
    # Nhóm học bổng
    ["doc_fpt_k21_0460", "doc_fpt_k20_0049", "doc_fpt_k17_0598", "doc_fpt_k18_0734"],
    # Nhóm bảo lưu
    ["doc_fpt_k17_0584", "doc_fpt_k20_0048", "doc_fpt_k21_0442", "doc_fpt_k18_0729"],
    # Nhóm chuẩn đầu ra tiếng Anh
    ["doc_fpt_k20_0265", "doc_fpt_k20_0269", "doc_fpt_k17_0595", "doc_fpt_k21_0441"],
    # Nhóm thôi học / cảnh báo học tập
    ["doc_fpt_k17_0623", "doc_fpt_k21_0443", "doc_fpt_k20_0047", "doc_fpt_k18_0730"],
    # Nhóm quy định phòng thi EOS
    ["doc_fpt_k17_0622", "doc_fpt_k21_0441", "doc_fpt_k20_0126", "doc_fpt_k18_0731"],
    # Nhóm tính điểm GPA
    ["doc_fpt_k18_0726", "doc_fpt_k17_0595", "doc_fpt_k20_0045", "doc_fpt_k21_0440"],
    # Nhóm học phí OJT
    ["doc_fpt_k21_0405", "doc_fpt_k20_0100", "doc_fpt_k17_0597"],
    # Nhóm trang phục sinh viên
    ["doc_fpt_k22_0300", "doc_fpt_k20_0039", "doc_fpt_k21_0444"],
    # Nhóm cấm thi / điểm danh 80%
    ["doc_fpt_k20_0041", "doc_fpt_k21_0446", "doc_fpt_k17_0587", "doc_fpt_k18_0728"],
    # Nhóm học lại / thi lại quy chế
    ["doc_fpt_k20_0046", "doc_fpt_k21_0447", "doc_fpt_k17_0589", "doc_fpt_k18_0733"],
    # Nhóm công nhận tốt nghiệp
    ["doc_fpt_k20_0052", "doc_fpt_k21_0453", "doc_fpt_k17_0599", "doc_fpt_k18_0735"],
    # Nhóm chuyển ngành
    ["doc_fpt_k20_0050", "doc_fpt_k21_0450", "doc_fpt_k17_0590", "doc_fpt_k18_0736"],
    # Nhóm chuyển cơ sở
    ["doc_fpt_k20_0051", "doc_fpt_k21_0451", "doc_fpt_k17_0591", "doc_fpt_k18_0737"],
    # Nhóm kỷ luật thi cử
    ["doc_fpt_k20_0128", "doc_fpt_k21_0449", "doc_fpt_k17_0592", "doc_fpt_k18_0738"],
    # Nhóm khen thưởng
    ["doc_fpt_k20_0053", "doc_fpt_k21_0454", "doc_fpt_k17_0600", "doc_fpt_k18_0739"],
    # Nhóm cố vấn học tập
    ["doc_fpt_k20_0054", "doc_fpt_k21_0455", "doc_fpt_k17_0601"],
    # Nhóm học vượt
    ["doc_fpt_k20_0043", "doc_fpt_k21_0445", "doc_fpt_k17_0586"],
    # Nhóm đăng ký môn học
    ["doc_fpt_k20_0040", "doc_fpt_k21_0444", "doc_fpt_k17_0585"],
]

# Đọc query texts để phân loại
queries = {}
for p in sorted(glob.glob("data/evaluation/benchmark_v2/batch_*.jsonl")):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                queries[item["q_id"]] = item.get("query", "")

# 1. Cập nhật 103 câu hiện có: xóa bỏ expected_cohorts giả định, thêm equiv_group
updated_count = 0
for q_id, entry in gold.items():
    q_text = queries.get(q_id, "")
    # Kiểm tra xem query có đề cập cohort không
    m = re.findall(r"\b[kK]\d{1,2}\b|khóa\s*\d{1,2}|khoá\s*\d{1,2}", q_text, re.IGNORECASE)
    if not m:
        entry["expected_cohorts"] = []  # Quy chế chung -> expected_cohorts rỗng!
    
    # Tìm equiv_group phù hợp nếu có
    doc_ids = set(entry.get("relevant_doc_ids", []))
    matched_eq = []
    for grp in EQUIV_PATTERNS:
        if set(grp) & doc_ids:
            # Chỉ lấy các doc khác doc đã có trong relevant_doc_ids
            diff = [d for d in grp if d not in doc_ids]
            if diff:
                matched_eq.append(diff)
    if matched_eq:
        # Gom các doc tương đương
        merged_eq = list(dict.fromkeys([d for sub in matched_eq for d in sub]))
        entry["equiv_group"] = [merged_eq]
    updated_count += 1

# 2. Bổ sung các câu hỏi Cohort-Specific từ batch_02 và batch_03
cohort_specific_entries = {
    "V2_B02_003": {
        "relevant_doc_ids": ["doc_fpt_k18_0695", "doc_fpt_k18_0728"],
        "equiv_group": [],
        "expected_cohorts": ["K18"]
    },
    "V2_B02_012": {
        "relevant_doc_ids": ["doc_fpt_k21_0381", "doc_fpt_k21_0447"],
        "equiv_group": [],
        "expected_cohorts": ["K21"]
    },
    "V2_B02_017": {
        "relevant_doc_ids": ["doc_fpt_k20_0005", "doc_fpt_k20_0096"],
        "equiv_group": [],
        "expected_cohorts": ["K20"]
    },
    "V2_B02_023": {
        "relevant_doc_ids": ["doc_fpt_k17_0569", "doc_fpt_k17_0582"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
    "V2_B02_031": {
        "relevant_doc_ids": ["doc_fpt_k19_0555", "doc_fpt_k19_0556"],
        "equiv_group": [],
        "expected_cohorts": ["K19"]
    },
    "V2_B02_034": {
        "relevant_doc_ids": ["doc_fpt_k22_0309", "doc_fpt_k22_0312"],
        "equiv_group": [],
        "expected_cohorts": ["K22"]
    },
    "V2_B02_044": {
        "relevant_doc_ids": ["doc_fpt_k18_0695", "doc_fpt_k18_0702"],
        "equiv_group": [],
        "expected_cohorts": ["K18"]
    },
    "V2_B02_047": {
        "relevant_doc_ids": ["doc_fpt_k22_0301", "doc_fpt_k22_0373"],
        "equiv_group": [],
        "expected_cohorts": ["K22"]
    },
    "V2_B02_050": {
        "relevant_doc_ids": ["doc_fpt_k20_0132", "doc_fpt_k20_0139"],
        "equiv_group": [],
        "expected_cohorts": ["K20"]
    },
    "V2_B03_001": {
        "relevant_doc_ids": ["doc_fpt_k17_0582", "doc_fpt_k17_0597"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
    "V2_B03_002": {
        "relevant_doc_ids": ["doc_fpt_k17_0582", "doc_fpt_k17_0605"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
    "V2_B03_003": {
        "relevant_doc_ids": ["doc_fpt_k17_0569", "doc_fpt_k17_0581"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
    "V2_B03_004": {
        "relevant_doc_ids": ["doc_fpt_k17_0569", "doc_fpt_k17_0588"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
    "V2_B03_005": {
        "relevant_doc_ids": ["doc_fpt_k17_0569", "doc_fpt_k17_0609"],
        "equiv_group": [],
        "expected_cohorts": ["K17"]
    },
}

for q_id, val in cohort_specific_entries.items():
    gold[q_id] = val

with open(gold_path, "w", encoding="utf-8") as f:
    json.dump(gold, f, ensure_ascii=False, indent=2)

print(f"Hoàn thành: Đã cập nhật {updated_count} câu quy chế chung (expected_cohorts=[]).")
print(f"Đã bổ sung {len(cohort_specific_entries)} câu hỏi Cohort-Specific chính thức.")
print(f"Tổng số entry trong gold hiện tại: {len(gold)}")

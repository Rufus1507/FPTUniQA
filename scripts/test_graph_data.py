import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open("data/processed/structured_data_courses.json", encoding="utf-8") as f:
    courses = json.load(f)["courses"]

print("=== Môn học liên quan thực tập / dự án / tốt nghiệp ===")
for c in courses:
    name = (c.get("vietnamese_name") or "") + " " + (c.get("course_name") or "")
    if any(w in name.lower() for w in ["tốt nghiệp", "ojt", "thực tập", "dự án", "capstone"]):
        print(f"{c['course_code']} ({c.get('vietnamese_name')} | {c.get('course_name')}): Sem {c.get('semester')}, Credits {c.get('credits')}, Prereqs: {c.get('prerequisites')}")

print("\n=== Thống kê mạng lưới tiên quyết ===")
all_prereqs = set()
for c in courses:
    for p in c.get("prerequisites", []):
        all_prereqs.add(p)
print(f"Tổng số môn học: {len(courses)}")
print(f"Số môn làm tiên quyết cho môn khác: {len(all_prereqs)}")
print("Môn có nhiều môn sau nhất:")
counts = {}
for c in courses:
    for p in c.get("prerequisites", []):
        counts[p] = counts.get(p, 0) + 1
for code, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  - {code}: mở đường cho {cnt} môn học")

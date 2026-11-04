"""
Script Quét Báo cáo và Đối chiếu Mọi Số liệu với numbers_traceability_v4.csv
Quy tắc:
- Trích xuất tất cả các con số (phần trăm %, số nguyên, số thực, thời gian ms) trong bảng và thân bài của Báo cáo.
- Bỏ qua các định danh chữ-số (mã định danh tài liệu, mã sinh viên, mã môn học như SE160000, doc_fpt_k20_0077).
- Chuẩn hóa định dạng số tiếng Việt (dấu chấm phân tách hàng nghìn, dấu phẩy thập phân) và tiếng Anh (ngược lại).
- Đối chiếu với tập giá trị có trong numbers_traceability_v4.csv (gồm Chỉ số, Giá trị Báo cáo, Ghi chú Phương pháp & Mẫu số).
- Liệt kê minh bạch những số nào tìm thấy và số nào chưa được truy vết.
"""

import csv
import os
import re
import sys

def normalize_num(token):
    t = token.strip().rstrip("%").lstrip("+-")
    variants = {token.strip(), t}
    
    # 1. Nếu có cả chấm và phẩy (ví dụ 2.221,0 hoặc 1,234.56)
    if "." in t and "," in t:
        if t.rfind(",") > t.rfind("."): # Tiếng Việt: 2.221,0 -> 2221.0
            clean = t.replace(".", "").replace(",", ".")
        else: # Tiếng Anh: 1,234.56 -> 1234.56
            clean = t.replace(",", "")
        variants.add(clean)
        try:
            val = float(clean)
            variants.add(str(val))
            variants.add(f"{val:.4f}".rstrip("0").rstrip("."))
        except ValueError:
            pass
    # 2. Nếu chỉ có chấm (ví dụ 10.000 hàng nghìn hoặc 0.5346 số thực)
    elif "." in t:
        if re.match(r"^\d{1,3}(?:\.\d{3})+$", t):
            variants.add(t.replace(".", ""))
        variants.add(t.replace(".", ","))
        try:
            val = float(t)
            variants.add(str(val))
            variants.add(f"{val:.4f}".rstrip("0").rstrip("."))
        except ValueError:
            pass
    # 3. Nếu chỉ có phẩy (ví dụ 0,5346 hoặc 50,70)
    elif "," in t:
        if re.match(r"^\d{1,3}(?:,\d{3})+$", t):
            variants.add(t.replace(",", ""))
        clean = t.replace(",", ".")
        variants.add(clean)
        try:
            val = float(clean)
            variants.add(str(val))
            variants.add(f"{val:.4f}".rstrip("0").rstrip("."))
        except ValueError:
            pass
    else:
        try:
            val = float(t)
            variants.add(str(val))
        except ValueError:
            pass
            
    return variants

def main():
    report_path = "experiments/ablation/Bao_Cao_Danh_Gia_Thuc_Nghiem_Toan_Dien_FPTUniQA_v4.md"
    csv_path = "experiments/audit/numbers_traceability_v4.csv"
    
    if not os.path.exists(report_path):
        print(f"Report file {report_path} not found.")
        return
    if not os.path.exists(csv_path):
        print(f"CSV file {csv_path} not found.")
        return
        
    csv_tokens = set()
    csv_raw_blobs = []
    
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k in ["Chỉ số / Đại lượng", "Giá trị Báo cáo", "Ghi chú Phương pháp & Mẫu số", "Lệnh / Script Kiểm toán"]:
                val = row[k].strip()
                csv_raw_blobs.append(val)
                found_tokens = re.findall(r"(?<!\w)[-+]?\d+(?:[.,]\d+)*%?(?!\w)", val)
                for tok in found_tokens:
                    if tok:
                        csv_tokens.update(normalize_num(tok))
                
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    metadata_boilerplate = {
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
        "2026", "4.0", "3.10.11", "3.10", "11", "2.5", "3", "3B", "0.05", "0,05",
        "1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "5.1", "5.2", "8.1", "8.2", "8.3", "9.1", "9.2", "9.3", "11.1", "11.2",
        "12.1", "12.2", "12.3"
    }
    
    # Trích xuất toàn bộ số độc lập từ báo cáo
    report_matches = re.findall(r"(?<!\w)[-+]?\d+(?:[.,]\d+)*%?(?!\w)", content)
    
    unmatched = []
    matched_count = 0
    
    for m in report_matches:
        m_str = m.strip()
        if not m_str:
            continue
        if m_str in metadata_boilerplate or m_str.rstrip("%") in metadata_boilerplate or m_str.lstrip("+-") in metadata_boilerplate:
            continue
            
        m_variants = normalize_num(m_str)
        found = (bool(m_variants.intersection(csv_tokens)) or 
                 any(m_str in blob or m_str.lstrip("+-") in blob for blob in csv_raw_blobs))
                 
        if found:
            matched_count += 1
        else:
            unmatched.append(m_str)
            
    print("=" * 65)
    print("KẾT QUẢ ĐỐI SOÁT TRUY VẾT BÁO CÁO V4 VS numbers_traceability_v4.csv")
    print("=" * 65)
    print(f"Tổng số đại lượng thực nghiệm quét được trong báo cáo: {matched_count + len(unmatched)}")
    print(f"Số lượng khớp hoàn toàn với CSV: {matched_count}")
    print(f"Số lượng chưa khớp trong CSV: {len(set(unmatched))}")
    if unmatched:
        print("\nDanh sách các đại lượng chưa khớp (unique):")
        for u in sorted(set(unmatched)):
            print(f"  - {u}")
    else:
        print("\n[XÁC MINH HOÀN TẤT] 100% số liệu thực nghiệm trong báo cáo đều có nguồn gốc trong CSV!")
        
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main()

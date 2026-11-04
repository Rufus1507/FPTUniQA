import os
import json
import hashlib
from datetime import datetime

def get_file_info(filepath):
    stat = os.stat(filepath)
    size = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
    # compute sha256 for key files
    sha256 = ""
    if size < 50 * 1024 * 1024: # < 50MB
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()
    return size, mtime, sha256

def count_lines_and_records(filepath):
    if not (filepath.endswith(".jsonl") or filepath.endswith(".json") or filepath.endswith(".csv")):
        return None
    try:
        if filepath.endswith(".jsonl"):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            return len(lines)
        elif filepath.endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data.keys())
    except Exception as e:
        return f"Error: {e}"
    return None

def main():
    root_dir = "experiments"
    inventory = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "audit" in dirpath.split(os.sep):
            continue
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, ".").replace("\\", "/")
            size, mtime, sha256 = get_file_info(fpath)
            record_count = count_lines_and_records(fpath)
            inventory.append({
                "path": rel_path,
                "size_bytes": size,
                "mtime": mtime,
                "sha256": sha256[:16] + "..." if sha256 else "",
                "records": record_count
            })
            
    # Sort by path
    inventory.sort(key=lambda x: x["path"])
    
    out_md = "experiments/audit/inventory.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# BẢNG KIỂM KÊ TÀI NGUYÊN THỰC NGHIỆM (EXPERIMENT INVENTORY)\n\n")
        f.write(f"- **Thời điểm kiểm kê:** `{datetime.now().isoformat()}`\n")
        f.write(f"- **Tổng số tệp phát hiện trong experiments/:** `{len(inventory)}`\n\n")
        f.write("| Đường dẫn Tệp | Kích thước (bytes) | Số bản ghi / dòng | SHA-256 (rút gọn) | Thời gian cập nhật |\n")
        f.write("| :--- | :---: | :---: | :---: | :--- |\n")
        for item in inventory:
            rec_str = str(item['records']) if item['records'] is not None else "—"
            f.write(f"| `{item['path']}` | {item['size_bytes']:,} | {rec_str} | `{item['sha256']}` | `{item['mtime']}` |\n")
            
    print(f"Inventory saved to {out_md} with {len(inventory)} items.")

if __name__ == "__main__":
    main()

"""Script kiểm tra chi tiết tốc độ, tài nguyên và cấu hình phần cứng của LLM (Ollama & PyTorch)."""

import time
import requests
import subprocess
import torch

import sys
import io

# Đảm bảo stdout ghi UTF-8 trên Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def check_hardware():
    print("=" * 65)
    print("1. KIEM TRA PHAN CUNG & MOI TRUONG CUDA")
    print("=" * 65)
    
    # 1. Kiểm tra Card đồ họa NVIDIA
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"],
            encoding="utf-8"
        ).strip()
        gpu_name, driver, mem_total, mem_used, gpu_util = smi_out.split(", ")
        print(f"[OK] GPU: {gpu_name}")
        print(f"   - Driver Version: {driver}")
        print(f"   - VRAM: {mem_used} / {mem_total}")
        print(f"   - GPU Utilization: {gpu_util}")
    except Exception as e:
        print(f"[FAIL] Khong the doc nvidia-smi: {e}")

    # 2. Kiểm tra PyTorch trong Python venv
    print(f"\n[INFO] PyTorch trong Python Environment:")
    print(f"   - PyTorch Version: {torch.__version__}")
    print(f"   - PyTorch CUDA Support: {'BAT (GPU)' if torch.cuda.is_available() else 'TAT (Dang dung ban CPU: torch+cpu)'}")
    if not torch.cuda.is_available():
        print("   [CHU Y]: Module Embedding va Reranker chay trong Python dang su dung CPU vi PyTorch hien tai la ban CPU.")

def test_ollama_llm():
    print("\n" + "=" * 65)
    print("2. TEST TOC DO VA VI TRI CHAY CUA LLM (OLLAMA)")
    print("=" * 65)
    
    url = "http://localhost:11434/api/generate"
    prompt = "Hay viet mot doan van ngan khoang 80 tu gioi thieu ve nganh Ky thuat phan mem tai Dai hoc FPT."
    payload = {
        "model": "qwen2.5:3b-instruct",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    print(f"Dang gui prompt test toi Ollama ({payload['model']})...")
    start = time.time()
    try:
        res = requests.post(url, json=payload, timeout=30)
        elapsed = time.time() - start
        if res.status_code == 200:
            data = res.json()
            eval_count = data.get("eval_count", 0)
            eval_dur_sec = data.get("eval_duration", 1) / 1e9
            tokens_per_sec = eval_count / eval_dur_sec if eval_dur_sec > 0 else 0
            prompt_eval_dur = data.get("prompt_eval_duration", 0) / 1e9
            
            print(f"[OK] LLM phan hoi thanh cong trong: {elapsed:.2f}s")
            print(f"   - So token sinh ra: {eval_count} tokens")
            print(f"   - Toc do sinh text: {tokens_per_sec:.2f} tokens/giay")
            print(f"   - Thoi gian nap prompt: {prompt_eval_dur:.3f}s")
            print(f"\n[Noi dung phan hoi]:\n{data.get('response', '').strip()}")
        else:
            print(f"[FAIL] Ollama tra ve loi: HTTP {res.status_code}")
    except Exception as e:
        print(f"[FAIL] Khong the ket noi toi Ollama: {e}")

    # 3. Kiểm tra Ollama Process
    try:
        ps_out = subprocess.check_output(["ollama", "ps"], encoding="utf-8")
        print("\nTrang thai mo hinh trong Ollama (ollama ps):")
        print(ps_out)
    except Exception as e:
        print(f"Loi kiem tra ollama ps: {e}")

if __name__ == "__main__":
    check_hardware()
    test_ollama_llm()

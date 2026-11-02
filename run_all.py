"""Script khởi chạy toàn bộ dự án FPTUniQA (All-in-one Launcher).
Tự động khởi động cả Backend API (FastAPI) và Frontend Giao diện (Streamlit).
Cách dùng:
    python run_all.py          # Chạy cả Web UI & Backend API
    python run_all.py --cli    # Chạy giao diện Terminal Chat tương tác
"""

import os
import sys
import time
import subprocess
import signal
import webbrowser
import urllib.request
import argparse

# Thiết lập đường dẫn môi trường
sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("."))
os.environ["PYTHONPATH"] = f"src{os.pathsep}.{os.pathsep}" + os.environ.get("PYTHONPATH", "")

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def check_backend_health(url="http://127.0.0.1:8000/healthz", timeout=15):
    """Đợi Backend API khởi động thành công."""
    start_time = time.time()
    print("⏳ Đang đợi Backend API sẵn sàng...", end="", flush=True)
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    print(" [OK]")
                    return True
        except Exception:
            print(".", end="", flush=True)
            time.sleep(0.8)
    print(" [Timeout - Vẫn tiếp tục mở Frontend]")
    return False


def run_full_web():
    """Khởi chạy đồng thời Backend FastAPI và Frontend Streamlit."""
    print("=" * 70)
    print("🚀 FPTUniQA - KHỞI CHẠY TOÀN BỘ HỆ THỐNG (FULL-STACK LAUNCHER)")
    print("=" * 70)
    print("📌 [1/2] Đang khởi động Backend API tại http://localhost:8000 ...")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        env=os.environ.copy(),
    )

    # Đợi backend khởi động
    check_backend_health()

    print("📌 [2/2] Đang khởi động Frontend Streamlit tại http://localhost:8501 ...")
    frontend_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/app.py",
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
    ]

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        env=os.environ.copy(),
    )

    print("\n" + "=" * 70)
    print("✅ TOÀN BỘ HỆ THỐNG ĐÃ SẴN SÀNG:")
    print("   🌐 Frontend Giao diện Chat: http://localhost:8501")
    print("   🔌 Backend REST API:        http://localhost:8000")
    print("   📚 API Swagger Docs:        http://localhost:8000/docs")
    print("   💻 Nhấn Ctrl+C trong cửa sổ này để tắt toàn bộ hệ thống.")
    print("=" * 70 + "\n")

    # Mở trình duyệt sau 2 giây
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open("http://localhost:8501")
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        # Giữ script chạy cho đến khi người dùng bấm Ctrl+C
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("⚠️ Backend API đã dừng đột ngột.")
                break
            if frontend_proc.poll() is not None:
                print("⚠️ Frontend Streamlit đã dừng đột ngột.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng toàn bộ dịch vụ FPTUniQA...")
    finally:
        for p in [frontend_proc, backend_proc]:
            if p and p.poll() is None:
                try:
                    p.terminate()
                    p.wait(timeout=3)
                except Exception:
                    p.kill()
        print("✅ Đã tắt hoàn tất các dịch vụ. Tạm biệt!")


def run_cli_chat():
    """Khởi chạy chế độ Terminal Chat tương tác."""
    from scripts.interactive_chat import main as chat_main
    chat_main()


def main():
    parser = argparse.ArgumentParser(description="Khởi chạy toàn bộ hệ thống FPTUniQA")
    parser.add_argument("--cli", action="store_true", help="Chạy chế độ Chat tương tác trên Terminal thay vì Web UI")
    args = parser.parse_args()

    if args.cli:
        run_cli_chat()
    else:
        run_full_web()


if __name__ == "__main__":
    main()

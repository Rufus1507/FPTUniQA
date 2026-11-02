@echo off
chcp 65001 > nul
echo ======================================================================
echo 🎓 FPTUniQA - KHỞI CHẠY TOÀN BỘ HỆ THỐNG
echo ======================================================================
set PYTHONPATH=src;.
python run_all.py %*
pause

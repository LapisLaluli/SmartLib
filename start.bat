@echo off
echo ============================================
echo     SmartLib AI - Khoi dong he thong
echo ============================================

cd /d D:\SmartLib\backend

echo [1/2] Kiem tra va cai dat thu vien Python...
pip install -r requirements.txt -q

echo [2/2] Khoi dong Backend Server (port 8001)...
echo.
echo  OK: Backend: http://localhost:8001
echo  OK: Mo frontend: D:\SmartLib\frontend\index.html
echo.
echo Nhan Ctrl+C de dung server.
echo.

python main.py
pause

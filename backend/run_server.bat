@echo off
title Aurora Cafe POS & Roastery Server
cd /d "%~dp0"

echo ========================================================
echo   AURORA CAFE & ROASTERY - POINT OF SALE
echo ========================================================
echo   Aplikasi POS : http://localhost:8000
echo   API Docs     : http://localhost:8000/docs
echo ========================================================
echo.
echo Menjalankan server kasir dan membuka browser otomatis...
echo Tekan CTRL+C jika ingin menghentikan server.
echo.

:: Otomatis membuka aplikasi di browser setelah jeda 2 detik
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Cek keberadaan uv di sistem, gunakan fallback venv jika uv tidak ada
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

pause

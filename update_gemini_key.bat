@echo off
setlocal

echo Cap nhat Gemini API key
set /p "NEW_KEY=Nhap Gemini API key: "
if not defined NEW_KEY (
    echo API key khong duoc de trong.
    pause
    exit /b 1
)

setx GEMINI_API_KEY "%NEW_KEY%" >nul
if errorlevel 1 (
    echo Khong the luu Gemini API key.
    pause
    exit /b 1
)

echo Da luu Gemini API key. Hay khoi dong lai backend.
pause

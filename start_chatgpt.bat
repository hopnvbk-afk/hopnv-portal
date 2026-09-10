@echo off
setlocal
cd /d "%~dp0"

if not defined OPENAI_API_KEY (
    echo Chua tim thay OPENAI_API_KEY tren may nay.
    set /p "OPENAI_API_KEY=Nhap OpenAI API key (chi nhap lan dau): "
    if not defined OPENAI_API_KEY (
        echo API key khong duoc de trong.
        pause
        exit /b 1
    )
    setx OPENAI_API_KEY "%OPENAI_API_KEY%" >nul
    echo Da luu API key vao bien moi truong nguoi dung.
)

echo Dang khoi dong backend ChatGPT tai http://127.0.0.1:8787
python "%~dp0openai_backend.py"
if errorlevel 1 (
    echo Khong the khoi dong Python backend. Hay kiem tra Python da duoc cai dat.
    pause
)

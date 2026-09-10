@echo off
setlocal

echo Cap nhat OpenAI API key
set /p "NEW_KEY=Nhap API key moi: "
if not defined NEW_KEY (
    echo API key khong duoc de trong.
    pause
    exit /b 1
)

setx OPENAI_API_KEY "%NEW_KEY%" >nul
if errorlevel 1 (
    echo Khong the luu API key.
    pause
    exit /b 1
)

echo Da cap nhat API key cho cac phien lam viec moi.
echo Hay dong backend dang chay, sau do chay lai start_chatgpt.bat.
pause

# HOPNV Portal

Portal web gồm giao diện HOPNV, tin tức cập nhật từ Báo Mới và trợ lý AI.

## Chạy online

- Giao diện tĩnh: GitHub Pages.
- Backend AI: Render sử dụng `render.yaml`.
- Khai báo `OPENAI_API_KEY` hoặc `GEMINI_API_KEY` trong Environment Variables của Render.
- Không đưa API key vào repository.

## Chạy local

- Mở `HOPNV.html` để dùng giao diện.
- Chạy `start_chatgpt.bat` nếu muốn dùng backend AI trên máy local.
- Mở `start_launcher.vbs` để chạy launcher nền, không hiện cửa sổ console.
- Các nút chương trình vẫn gọi `launcher.py` tại `127.0.0.1:8765`, vì các chương trình trong `programs.json` chạy trên máy local.

Trình duyệt không được phép tự thực thi lệnh Windows từ một website. Vì vậy nút
Launcher trên portal chỉ kiểm tra trạng thái; lần đầu người dùng cần mở
`start_launcher.vbs` thủ công. Sau đó portal sẽ hiển thị `Sẵn sàng`.

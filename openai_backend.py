import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8787"))
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")


class OpenAIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/chat":
            self.send_json(404, {"error": "Không tìm thấy endpoint."})
            return
        try:
            body = self.read_json()
            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                self.send_json(400, {"error": "Tin nhắn không hợp lệ."})
                return

            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                try:
                    payload = json.dumps({"model": MODEL, "messages": messages}).encode("utf-8")
                    request = Request(
                        OPENAI_URL,
                        data=payload,
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        method="POST",
                    )
                    with urlopen(request, timeout=60) as response:
                        result = json.loads(response.read().decode("utf-8"))
                    answer = result["choices"][0]["message"]["content"].strip()
                    if answer:
                        self.send_json(200, {"answer": answer, "provider": "openai"})
                        return
                except (HTTPError, URLError, KeyError, IndexError, TypeError):
                    pass

            gemini_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_key:
                self.send_json(503, {"error": "OpenAI không khả dụng và chưa cấu hình GEMINI_API_KEY."})
                return

            prompt = self.latest_user_message(messages)
            gemini_payload = json.dumps(
                {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
            ).encode("utf-8")
            gemini_request = Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}",
                data=gemini_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(gemini_request, timeout=60) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                details = error.read().decode("utf-8", errors="replace")
                try:
                    error_body = json.loads(details)
                    message = error_body.get("error", {}).get("message")
                except json.JSONDecodeError:
                    message = None
                self.send_json(502, {"error": message or "Gemini từ chối yêu cầu."})
                return
            except (URLError, json.JSONDecodeError) as error:
                self.send_json(502, {"error": f"Không thể kết nối Gemini: {error}"})
                return
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            if not answer:
                self.send_json(502, {"error": "Gemini không trả về nội dung."})
                return
            self.send_json(200, {"answer": answer, "provider": "gemini"})
        except (json.JSONDecodeError, ValueError):
            self.send_json(400, {"error": "Dữ liệu gửi lên không hợp lệ."})
        except (URLError, KeyError, IndexError, TypeError):
            self.send_json(502, {"error": "Không thể nhận phản hồi từ Gemini."})

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        self.send_json(404, {"error": "Không tìm thấy endpoint."})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    @staticmethod
    def latest_user_message(messages):
        for message in reversed(messages):
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return ""

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def log_message(self, format, *args):
        print(format % args)


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), OpenAIHandler).serve_forever()

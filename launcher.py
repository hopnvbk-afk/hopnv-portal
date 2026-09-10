from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlparse
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("programs.json")
HOST = "127.0.0.1"
PORT = 8765
processes = {}
process_lock = threading.Lock()


def load_programs():
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


class LauncherHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path not in ("/run", "/stop"):
            self.send_json(404, {"message": "Không tìm thấy endpoint."})
            return

        program_id = parse_qs(parsed_path.query).get("program", [""])[0]
        if not program_id:
            self.send_json(400, {"message": "Thiếu mã chương trình."})
            return

        try:
            program = load_programs()[program_id]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.send_json(500, {"message": "Không đọc được cấu hình chương trình."})
            return

        global processes
        with process_lock:
            process = processes.get(program_id)
            if parsed_path.path == "/stop":
                if process is None or process.poll() is not None:
                    self.send_json(200, {"message": "Chương trình không đang chạy."})
                    processes.pop(program_id, None)
                    return
                process.terminate()
                processes.pop(program_id, None)
                self.send_json(200, {"message": "Đã dừng chương trình."})
                return

            raw_path = str(program.get("path", "")).strip()
            if not raw_path:
                self.send_json(400, {"message": f"Chưa cấu hình đường dẫn cho {program_id}."})
                return
            script_path = Path(raw_path).expanduser()
            if not script_path.is_file():
                self.send_json(404, {"message": f"Không tìm thấy file: {script_path}"})
                return
            if process is not None and process.poll() is None:
                self.send_json(409, {"message": "Chương trình đang chạy."})
                return

            command = [sys.executable, str(script_path)] if script_path.suffix.lower() == ".py" else [str(script_path)]
            processes[program_id] = subprocess.Popen(command, cwd=str(script_path.parent))
        self.send_json(200, {"message": "Đã khởi chạy chương trình."})

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
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        print(format % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), LauncherHandler)
    print(f"Launcher đang chạy tại http://{HOST}:{PORT}")
    server.serve_forever()

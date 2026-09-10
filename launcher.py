from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import threading
import time
import ctypes
from urllib.parse import parse_qs, urlparse
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("programs.json")
HOST = "127.0.0.1"
PORT = 8765
processes = {}
process_lock = threading.Lock()


def bring_process_window_to_front(process):
    if sys.platform != "win32":
        return

    user32 = ctypes.windll.user32
    deadline = time.monotonic() + 10

    while time.monotonic() < deadline and process.poll() is None:
        windows = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_window(window_handle, _):
            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(window_handle, ctypes.byref(process_id))
            if process_id.value == process.pid and user32.IsWindowVisible(window_handle):
                windows.append(window_handle)
                return False
            return True

        user32.EnumWindows(enum_window, 0)
        if windows:
            window_handle = windows[0]
            user32.ShowWindow(window_handle, 9)
            user32.SetForegroundWindow(window_handle)
            return
        time.sleep(0.2)


def load_programs():
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


class LauncherHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if urlparse(self.path).path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        self.send_json(404, {"message": "Không tìm thấy endpoint."})

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
            process = subprocess.Popen(command, cwd=str(script_path.parent))
            processes[program_id] = process
            threading.Thread(
                target=bring_process_window_to_front,
                args=(process,),
                daemon=True,
            ).start()
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

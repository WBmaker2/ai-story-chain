#!/usr/bin/env python3
import json
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "4173"))
ROOT = Path(__file__).resolve().parent
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def load_env_file() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, v = stripped.split("=", 1)
        key = k.strip()
        val = v.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


class StoryTrainHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/api/generate-image":
            self.respond_json({"error": "Not Found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            body = json.loads(raw_body.decode("utf-8"))
            sentence = str(body.get("sentence", "")).strip()
            if not sentence:
                self.respond_json({"error": "sentence is required"}, status=400)
                return

            image_data_url = self.generate_with_pollinations(sentence)
            self.respond_json({"imageDataUrl": image_data_url})
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid JSON"}, status=400)
        except RuntimeError as exc:
            self.respond_json({"error": str(exc)}, status=500)
        except Exception as exc:
            self.respond_json({"error": f"unexpected error: {exc}"}, status=500)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.respond_json({"ok": True})
            return

        if self.path.startswith("/api/"):
            self.respond_json({"error": "Not Found"}, status=404)
            return

        target = "index.html" if self.path in ("/", "") else self.path.lstrip("/")
        file_path = (ROOT / target).resolve()

        if ROOT not in file_path.parents and file_path != ROOT:
            self.send_error(403)
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "application/octet-stream"

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        return

    def respond_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def generate_with_pollinations(self, sentence: str) -> str:
        prompt_prefix = os.environ.get(
            "PROMPT_PREFIX",
            "cute fairy tale illustration for elementary school children, bright pastel colors, scene: "
        ).strip()
        width = int(os.environ.get("POLLINATIONS_WIDTH", "512"))
        height = int(os.environ.get("POLLINATIONS_HEIGHT", "512"))

        full_prompt = urllib.parse.quote(f"{prompt_prefix}{sentence}")
        image_url = (
            f"{POLLINATIONS_BASE}/{full_prompt}"
            f"?width={width}&height={height}&nologo=true&model=flux"
        )
        return image_url


def main() -> None:
    load_env_file()
    server = ThreadingHTTPServer((HOST, PORT), StoryTrainHandler)
    print(f"Story Train server running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

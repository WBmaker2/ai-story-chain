#!/usr/bin/env python3
import json
import mimetypes
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "4173"))
ROOT = Path(__file__).resolve().parent
KEYCHAIN_SERVICE = "story-train-openrouter"


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

            image_data_url = self.generate_with_openrouter(sentence)
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

    def generate_with_openrouter(self, sentence: str) -> str:
        api_key = get_openrouter_api_key()
        model = os.environ.get("OPENROUTER_IMAGE_MODEL", "google/gemini-2.0-flash-exp:free").strip()
        app_base_url = os.environ.get("APP_BASE_URL", f"http://localhost:{PORT}").strip()

        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY가 설정되지 않았습니다.")

        payload = {
            "model": model,
            "prompt": f"초등학생 동화 삽화 스타일. 밝고 귀여운 파스텔 톤. 장면: {sentence}",
            "size": "1024x1024"
        }

        req = request.Request(
            "https://openrouter.ai/api/v1/images/generations",
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": app_base_url,
                "X-Title": "Story Train"
            },
            data=json.dumps(payload).encode("utf-8")
        )

        try:
            with request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail[:220]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenRouter 연결 실패: {exc}") from exc

        item = (data.get("data") or [{}])[0]
        b64 = item.get("b64_json")
        url = item.get("url")

        if b64:
            return f"data:image/png;base64,{b64}"

        if url:
            return url

        raise RuntimeError("이미지 응답을 찾지 못했습니다. OPENROUTER_IMAGE_MODEL 값을 확인해 주세요.")


def get_openrouter_api_key() -> str:
    env_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env_key:
        return env_key

    try:
        username = os.environ.get("USER", "")
        cmd = ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"]
        if username:
            cmd.extend(["-a", username])
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main() -> None:
    load_env_file()
    server = ThreadingHTTPServer((HOST, PORT), StoryTrainHandler)
    print(f"Story Train server running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

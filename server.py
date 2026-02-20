#!/usr/bin/env python3
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "4173"))
ROOT = Path(__file__).resolve().parent
PIXAZO_ENDPOINT = os.environ.get("PIXAZO_ENDPOINT", "https://api.pixazo.ai/v1/images/generations").strip()


class UpstreamAPIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


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

            image_data_url = self.generate_with_pixazo(sentence)
            self.respond_json({"imageDataUrl": image_data_url})
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid JSON"}, status=400)
        except UpstreamAPIError as exc:
            self.respond_json({"error": exc.message}, status=exc.status_code)
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

    def generate_with_pixazo(self, sentence: str) -> str:
        width = int(os.environ.get("PIXAZO_WIDTH", "512"))
        height = int(os.environ.get("PIXAZO_HEIGHT", "512"))
        prompt_prefix = os.environ.get(
            "PIXAZO_PROMPT_PREFIX",
            "초등학생을 위한 귀여운 동화풍 삽화, 밝은 파스텔 색감, 장면: "
        ).strip()

        payload = {
            "prompt": f"{prompt_prefix}{sentence}",
            "width": width,
            "height": height
        }

        headers = {
            "Content-Type": "application/json"
        }
        api_key = os.environ.get("PIXAZO_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = request.Request(
            PIXAZO_ENDPOINT,
            method="POST",
            headers=headers,
            data=json.dumps(payload).encode("utf-8")
        )

        try:
            with request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            msg = parse_upstream_error(detail)
            raise UpstreamAPIError(exc.code, f"Pixazo {exc.code}: {msg}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Pixazo 연결 실패: {exc}") from exc

        image_data_url = extract_image_url_or_data(data)
        if image_data_url:
            return image_data_url

        raise RuntimeError("Pixazo 응답에서 이미지 데이터를 찾지 못했습니다.")


def extract_image_url_or_data(obj, depth: int = 0) -> str:
    if depth > 6:
        return ""

    if isinstance(obj, str):
        val = obj.strip()
        if val.startswith("http://") or val.startswith("https://") or val.startswith("data:image/"):
            return val
        return ""

    if isinstance(obj, list):
        for item in obj:
            found = extract_image_url_or_data(item, depth + 1)
            if found:
                return found
        return ""

    if not isinstance(obj, dict):
        return ""

    for key in ("imageDataUrl", "image_url", "imageUrl", "url"):
        value = obj.get(key)
        found = extract_image_url_or_data(value, depth + 1)
        if found:
            return found

    for key in ("b64_json", "base64", "image_base64", "imageBase64"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return f"data:image/png;base64,{value.strip()}"

    for key in ("data", "images", "output", "result", "results"):
        value = obj.get(key)
        found = extract_image_url_or_data(value, depth + 1)
        if found:
            return found

    return ""


def parse_upstream_error(detail: str) -> str:
    try:
        parsed = json.loads(detail)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("error"), dict):
                msg = str(parsed["error"].get("message", "")).strip()
                if msg:
                    return msg
            if parsed.get("error"):
                return str(parsed["error"]).strip()
            if parsed.get("message"):
                return str(parsed["message"]).strip()
    except Exception:
        pass

    compact = " ".join(detail.strip().split())
    if compact.startswith("<!DOCTYPE html"):
        return "엔드포인트 또는 요청 형식이 올바르지 않습니다."
    return compact[:220] if compact else "Unknown upstream error"


def main() -> None:
    load_env_file()
    server = ThreadingHTTPServer((HOST, PORT), StoryTrainHandler)
    print(f"Story Train server running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

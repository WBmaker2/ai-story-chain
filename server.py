#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "4173"))
ROOT = Path(__file__).resolve().parent
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
DEFAULT_MAX_REQUEST_BYTES = 8192
DEFAULT_MAX_SENTENCE_CHARS = 500
PUBLIC_FILES = {"index.html"}
PUBLIC_ASSET_DIRS = {"assets", "static"}
PUBLIC_ASSET_EXTENSIONS = {
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".mjs",
    ".png",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
}


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


def get_int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def is_public_static_target(target: str) -> bool:
    if target in PUBLIC_FILES:
        return True

    target_path = Path(target)
    parts = target_path.parts
    return (
        bool(parts)
        and parts[0] in PUBLIC_ASSET_DIRS
        and target_path.suffix.lower() in PUBLIC_ASSET_EXTENSIONS
    )


def build_image_prompt(prompt_prefix: str, sentence: str) -> str:
    prefix = prompt_prefix.strip()
    if not prefix:
        return sentence
    return f"{prefix} {sentence}"


class StoryTrainHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path != "/api/generate-image":
            self.respond_json({"error": "Not Found"}, status=404)
            return

        try:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.respond_json({"error": "invalid Content-Length"}, status=400)
                return

            max_request_bytes = get_int_env("MAX_REQUEST_BYTES", DEFAULT_MAX_REQUEST_BYTES)
            if length > max_request_bytes:
                self.respond_json({"error": "request body too large"}, status=413)
                return

            raw_body = self.rfile.read(length)
            body = json.loads(raw_body.decode("utf-8"))
            sentence = str(body.get("sentence", "")).strip()
            if not sentence:
                self.respond_json({"error": "sentence is required"}, status=400)
                return

            max_sentence_chars = get_int_env("MAX_SENTENCE_CHARS", DEFAULT_MAX_SENTENCE_CHARS)
            if len(sentence) > max_sentence_chars:
                self.respond_json(
                    {"error": f"sentence is too long (max {max_sentence_chars} characters)"},
                    status=400,
                )
                return

            image_data_url = self.generate_image_with_fallback(sentence)
            self.respond_json({"imageDataUrl": image_data_url})
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid JSON"}, status=400)
        except RuntimeError as exc:
            self.respond_json({"error": str(exc)}, status=500)
        except Exception as exc:
            self.respond_json({"error": f"unexpected error: {exc}"}, status=500)

    def do_GET(self) -> None:
        parsed_path = urllib.parse.urlparse(self.path).path
        if parsed_path == "/healthz":
            self.respond_json({"ok": True})
            return

        if parsed_path.startswith("/api/"):
            self.respond_json({"error": "Not Found"}, status=404)
            return

        target = "index.html" if parsed_path in ("/", "") else parsed_path.lstrip("/")
        if not is_public_static_target(target):
            self.send_error(404)
            return

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

        full_prompt = urllib.parse.quote(build_image_prompt(prompt_prefix, sentence))
        image_url = (
            f"{POLLINATIONS_BASE}/{full_prompt}"
            f"?width={width}&height={height}&nologo=true"
        )

        # 서버에서 이미지를 직접 다운로드해 base64로 변환
        # (Render 등 외부 서버에서 실행 시 브라우저 차단 우회)
        req = request.Request(
            image_url,
            headers={"User-Agent": "story-train/1.2"},
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                image_bytes = resp.read()
                b64 = base64.b64encode(image_bytes).decode("ascii")
                return f"data:{content_type};base64,{b64}"
        except error.HTTPError as exc:
            raise RuntimeError(f"Pollinations 오류 ({exc.code}): {exc.reason}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Pollinations 연결 실패: {exc}") from exc

    def generate_with_huggingface(self, sentence: str) -> str:
        """Hugging Face Inference API를 사용한 이미지 생성 (fallback 옵션)"""
        hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise RuntimeError("HUGGINGFACE_TOKEN 환경변수가 설정되지 않았습니다")

        prompt_prefix = os.environ.get(
            "PROMPT_PREFIX",
            "cute fairy tale illustration for elementary school children, bright pastel colors, scene: "
        ).strip()

        hf_model = os.environ.get(
            "HUGGINGFACE_MODEL",
            "runwayml/stable-diffusion-v1-5"
        )

        api_url = f"https://api-inference.huggingface.co/models/{hf_model}"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }

        try:
            req = request.Request(
                api_url,
                data=json.dumps({"inputs": build_image_prompt(prompt_prefix, sentence)}).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with request.urlopen(req, timeout=90) as resp:
                image_bytes = resp.read()
                b64 = base64.b64encode(image_bytes).decode("ascii")
                return f"data:image/jpeg;base64,{b64}"
        except error.HTTPError as exc:
            raise RuntimeError(f"Hugging Face 오류 ({exc.code}): {exc.reason}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Hugging Face 연결 실패: {exc}") from exc

    def generate_image_with_fallback(self, sentence: str) -> str:
        """
        Pollinations.ai → Hugging Face 순서로 시도하는 fallback 시스템
        교육용으로 안정적인 이미지 생성 제공
        """
        # 1. Pollinations.ai 시도 (무료, API Key 불필요)
        try:
            print(f"[1/2] Pollinations.ai 시도: {sentence[:30]}...")
            return self.generate_with_pollinations(sentence)
        except RuntimeError as e:
            print(f"  ⚠️ Pollinations 실패: {e}")

        # 2. Hugging Face 시도 (무료, Access Token 필요)
        if os.environ.get("HUGGINGFACE_TOKEN"):
            try:
                print(f"[2/2] Hugging Face 시도...")
                return self.generate_with_huggingface(sentence)
            except RuntimeError as e:
                print(f"  ⚠️ Hugging Face 실패: {e}")

        # 모두 실패하면 에러 전달
        raise RuntimeError("모든 이미지 생성 서비스가 실패했습니다. 나중에 다시 시도해주세요.")


def main() -> None:
    load_env_file()
    server = ThreadingHTTPServer((HOST, PORT), StoryTrainHandler)
    print(f"Story Train server running: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

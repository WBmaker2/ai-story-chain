#!/usr/bin/env python3
"""
이미지 생성 API 테스트 스크립트
"""
import base64
import json
import urllib.parse
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import error, request

HOST = "127.0.0.1"
PORT = 4173
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


class TestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/generate-image":
            # 요청 읽기
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            sentence = body.get("sentence", "")

            print(f"\n{'='*60}")
            print(f"📝 문장: {sentence}")
            print(f"{'='*60}")

            # Pollinations 시도
            try:
                prompt_prefix = "cute fairy tale illustration for elementary school children, bright pastel colors, scene: "
                full_prompt = urllib.parse.quote(f"{prompt_prefix}{sentence}")
                image_url = f"{POLLINATIONS_BASE}/{full_prompt}?width=256&height=256&nologo=true"

                print(f"🔗 Pollinations URL 생성...")
                print(f"   {image_url[:80]}...")

                req = request.Request(image_url, headers={"User-Agent": "story-train/1.3-test"})
                with request.urlopen(req, timeout=30) as resp:
                    content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
                    image_bytes = resp.read()

                    print(f"✅ Pollinations 성공!")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Size: {len(image_bytes):,} bytes")

                    b64 = base64.b64encode(image_bytes).decode("ascii")
                    response = {"imageDataUrl": f"data:{content_type};base64,{b64}"}

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    print(f"✅ 응답 전송 완료\n")
                    return

            except error.HTTPError as exc:
                print(f"❌ Pollinations HTTP 오류: {exc.code} - {exc.reason}")
            except error.URLError as exc:
                print(f"❌ Pollinations 연결 오류: {exc}")

            # 실패 응답
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "이미지 생성 실패"}).encode())

    def log_message(self, fmt, *args):
        return  # 로그 끄기


def main():
    print(f"""
╔════════════════════════════════════════════════════════════╗
║  🚂 상상 톡톡 이미지 생성 API 테스트 서버                  ║
╚════════════════════════════════════════════════════════════╝

시작: http://{HOST}:{PORT}
종료: Ctrl+C

테스트 예시:
curl -X POST http://{HOST}:{PORT}/api/generate-image \\
  -H "Content-Type: application/json" \\
  -d '{{"sentence":"기차가 무지개 터널을 지나갔어요"}}'
""")

    server = ThreadingHTTPServer((HOST, PORT), TestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ 서버 종료")
        server.shutdown()


if __name__ == "__main__":
    main()

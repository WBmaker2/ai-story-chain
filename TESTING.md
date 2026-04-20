# 테스트 가이드

## 1. 로컬 설정

```bash
cd /Users/kimhongnyeon/Dev/codex/ai-story-chain
cp .env.example .env
```

Pollinations.ai만 사용할 때는 API 키가 필요 없습니다.
Hugging Face fallback을 테스트하려면 `.env`에 `HUGGINGFACE_TOKEN`을 추가합니다.

## 2. 서버 실행

```bash
cd /Users/kimhongnyeon/Dev/codex/ai-story-chain
python3 server.py
```

브라우저에서 열기:

- `http://127.0.0.1:4173`

헬스체크:

- `http://127.0.0.1:4173/healthz`

## 3. 자동 테스트

```bash
cd /Users/kimhongnyeon/Dev/codex/ai-story-chain
PYTHONPYCACHEPREFIX=/tmp/ai-story-chain-pycache python3 -m unittest test_server -v
```

테스트 범위:

- 루트 페이지가 정상 서빙되는지 확인
- `.env`, Markdown 문서 등 내부 파일이 서빙되지 않는지 확인
- 큰 요청 본문이 `413`으로 거부되는지 확인
- 너무 긴 문장이 이미지 생성 전에 거부되는지 확인
- `PROMPT_PREFIX`와 문장 사이 공백이 유지되는지 확인

## 4. 기능 테스트

1. 문장을 입력하고 `기차 칸 추가하기`를 클릭합니다.
2. 상단 기차 칸과 하단 타임라인에 문장이 추가되는지 확인합니다.
3. 우측 시각화 영역에 이미지가 표시되는지 확인합니다.
4. Pollinations.ai가 실패하고 `HUGGINGFACE_TOKEN`이 설정되어 있으면 Hugging Face fallback이 동작하는지 서버 로그로 확인합니다.

## 5. 문제 해결

- 상태 문구가 `이미지 생성 실패`이면 서버 실행 터미널의 에러 로그를 확인합니다.
- Pollinations.ai 호출이 실패하면 잠시 후 다시 시도하거나 네트워크 연결을 확인합니다.
- Hugging Face 응답이 `401`이면 `HUGGINGFACE_TOKEN`을 확인합니다.
- Hugging Face 응답이 `503`이면 모델 로딩 중일 수 있으니 30-60초 후 다시 시도합니다.
- 요청이 `413`이면 `MAX_REQUEST_BYTES`를 늘리거나 입력 크기를 줄입니다.
- 요청이 `400`이고 문장이 너무 길다는 메시지가 나오면 `MAX_SENTENCE_CHARS`를 조정하거나 문장을 줄입니다.

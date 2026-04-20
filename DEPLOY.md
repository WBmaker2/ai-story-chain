# 배포 가이드

이 프로젝트는 Python 표준 라이브러리만 사용하는 단일 서버 앱입니다.
서버는 `index.html`을 서빙하고, `POST /api/generate-image`에서 이미지를 생성합니다.

## 이미지 생성 흐름

1. 기본: Pollinations.ai
   - API 키가 필요 없습니다.
   - `PROMPT_PREFIX`, `POLLINATIONS_WIDTH`, `POLLINATIONS_HEIGHT`로 조정합니다.
2. Fallback: Hugging Face Inference API
   - `HUGGINGFACE_TOKEN`이 설정되어 있을 때만 사용합니다.
   - Pollinations.ai 호출이 실패하면 Hugging Face로 재시도합니다.

## 환경변수

필수 환경변수는 없습니다.

선택 환경변수:

- `PROMPT_PREFIX`: 이미지 생성 프롬프트 앞부분
- `POLLINATIONS_WIDTH`: 이미지 너비, 기본값 `512`
- `POLLINATIONS_HEIGHT`: 이미지 높이, 기본값 `512`
- `HUGGINGFACE_TOKEN`: Hugging Face fallback용 Access Token
- `HUGGINGFACE_MODEL`: Hugging Face 모델, 기본값 `runwayml/stable-diffusion-v1-5`
- `MAX_REQUEST_BYTES`: API 요청 본문 최대 크기, 기본값 `8192`
- `MAX_SENTENCE_CHARS`: 문장 최대 길이, 기본값 `500`
- `APP_BASE_URL`: 배포 URL 기록용 선택값

## Render 배포

1. GitHub 저장소를 Render에 연결합니다.
2. `New +` -> `Blueprint`를 선택합니다.
3. 저장소의 `render.yaml`을 사용해 배포합니다.
4. 필요하면 Render Variables에 선택 환경변수를 추가합니다.
5. Hugging Face fallback을 사용하려면 `HUGGINGFACE_TOKEN`을 Secret으로 추가합니다.

`render.yaml`은 기본적으로 다음 값을 설정합니다.

- `PROMPT_PREFIX`
- `POLLINATIONS_WIDTH=512`
- `POLLINATIONS_HEIGHT=512`

## Railway 배포

1. `New Project` -> `Deploy from GitHub repo`를 선택합니다.
2. Start command를 `python3 server.py`로 설정합니다.
3. 필요한 Variables를 추가합니다.
   - `PROMPT_PREFIX`
   - `POLLINATIONS_WIDTH=512`
   - `POLLINATIONS_HEIGHT=512`
   - `HUGGINGFACE_TOKEN=<hf-token>` 선택

## 로컬 확인

```bash
cd /Users/kimhongnyeon/Dev/codex/ai-story-chain
python3 server.py
```

- 접속: `http://127.0.0.1:4173`
- 헬스체크: `http://127.0.0.1:4173/healthz`

## 정적 호스팅

GitHub Pages처럼 Python 서버가 없는 정적 호스팅에서는 `index.html`이 Pollinations.ai URL을 직접 사용합니다.
이 경우 서버 측 Hugging Face fallback과 요청 제한은 동작하지 않습니다.

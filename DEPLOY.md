# 배포 가이드 (Pixazo Stable Diffusion v3.5)

## 공통 준비

필수 환경변수:
- `PIXAZO_ENDPOINT`: `https://gateway-replicate-flux-schnell.appypie.workers.dev/r-sd-3-5-large`
- `PIXAZO_API_KEY`: Pixazo 대시보드의 구독 키 (`Ocp-Apim-Subscription-Key`)
- `APP_BASE_URL`: 배포 URL (예: `https://your-app.onrender.com`)

선택 환경변수:
- `PIXAZO_ASPECT_RATIO` (기본 `1:1`)
- `PIXAZO_CFG` (기본 `4.5`)
- `PIXAZO_STEPS` (기본 `40`)
- `PIXAZO_OUTPUT_FORMAT` (기본 `webp`)
- `PIXAZO_OUTPUT_QUALITY` (기본 `90`)
- `PIXAZO_PROMPT_STRENGTH` (기본 `0.85`)
- `PIXAZO_PROMPT_PREFIX`

## Render 배포

1. GitHub에 이 폴더를 push
2. Render에서 `New +` -> `Blueprint` 선택
3. 저장소 연결 후 `render.yaml`로 배포
4. `APP_BASE_URL`를 실제 배포 URL로 입력
5. `PIXAZO_API_KEY`를 반드시 추가

## Railway 배포

1. `New Project` -> `Deploy from GitHub repo`
2. Start command: `python3 server.py`
3. Variables에 아래 입력:
   - `PIXAZO_ENDPOINT=https://gateway-replicate-flux-schnell.appypie.workers.dev/r-sd-3-5-large`
   - `PIXAZO_API_KEY=<pixazo-subscription-key>`
   - `APP_BASE_URL=https://<railway-domain>`

## 로컬 확인

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
python3 server.py
```

- 접속: `http://127.0.0.1:4173`
- 헬스체크: `http://127.0.0.1:4173/healthz`

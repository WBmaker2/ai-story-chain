# 배포 가이드 (Pixazo Stable Diffusion)

## 공통 준비

필수 환경변수:
- `PIXAZO_ENDPOINT`: `https://api.pixazo.ai/v1/images/generations`
- `APP_BASE_URL`: 배포 URL (예: `https://your-app.onrender.com`)

선택 환경변수:
- `PIXAZO_API_KEY`: Pixazo에서 키가 필요한 계정/플랜일 때만
- `PIXAZO_WIDTH`, `PIXAZO_HEIGHT` (기본 512)
- `PIXAZO_PROMPT_PREFIX`

## Render 배포

1. GitHub에 이 폴더를 push
2. Render에서 `New +` -> `Blueprint` 선택
3. 저장소 연결 후 `render.yaml`로 배포
4. `APP_BASE_URL`를 실제 배포 URL로 입력
5. 필요 시 `PIXAZO_API_KEY` 추가

## Railway 배포

1. `New Project` -> `Deploy from GitHub repo`
2. Start command: `python3 server.py`
3. Variables에 아래 입력:
   - `PIXAZO_ENDPOINT=https://api.pixazo.ai/v1/images/generations`
   - `APP_BASE_URL=https://<railway-domain>`
   - 필요 시 `PIXAZO_API_KEY`

## 로컬 확인

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
python3 server.py
```

- 접속: `http://127.0.0.1:4173`
- 헬스체크: `http://127.0.0.1:4173/healthz`

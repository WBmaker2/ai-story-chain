# 배포 가이드

## 공통 준비

필수 환경변수:
- `OPENROUTER_API_KEY`: OpenRouter API Key
- `OPENROUTER_IMAGE_MODEL`: `sourceful/riverflow-v2-pro`
- `APP_BASE_URL`: 배포 URL (예: `https://your-app.onrender.com`)

## Render 배포

1. GitHub에 이 폴더를 push
2. Render에서 `New +` -> `Blueprint` 선택
3. 저장소 연결 후 `render.yaml`로 배포
4. 배포 서비스의 환경변수에 `OPENROUTER_API_KEY` 입력
5. `APP_BASE_URL`를 실제 배포 URL로 입력

## Railway 배포

1. `New Project` -> `Deploy from GitHub repo`
2. Start command: `python3 server.py`
3. Variables에 아래 입력:
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_IMAGE_MODEL=sourceful/riverflow-v2-pro`
   - `APP_BASE_URL=https://<railway-domain>`

## 로컬 확인

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
python3 server.py
```

- 접속: `http://127.0.0.1:4173`
- 헬스체크: `http://127.0.0.1:4173/healthz`

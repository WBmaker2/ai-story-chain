# 테스트 가이드 (서버 키 숨김 모드)

## 1) 교사용 API 키 설정 (브라우저에 노출되지 않음)

1. 가장 쉬운 방법(숨김 입력):

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
./set_openrouter_key.sh
```

2. 또는 수동으로 아래 파일을 복사:

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
cp .env.example .env
```

3. `.env` 파일에서 `OPENROUTER_API_KEY` 값을 실제 키로 바꿉니다.
4. 필요하면 `OPENROUTER_IMAGE_MODEL`도 사용 가능한 이미지 모델로 바꿉니다.

## 2) 실행

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
python3 server.py
```

브라우저에서 열기:
- http://127.0.0.1:4173

## 3) 기능 테스트

1. 문장을 입력하고 `기차 칸 추가하기` 클릭
2. 상단 기차 칸/하단 타임라인에 문장이 추가되는지 확인
3. 우측 시각화 영역에 이미지가 표시되는지 확인

## 4) 문제 해결

- 상태 문구가 `이미지 생성 실패`이면:
  - 서버 실행 터미널 에러 로그 확인
  - `.env`의 `OPENROUTER_API_KEY` 값 확인
  - `OPENROUTER_IMAGE_MODEL`을 실제 이미지 생성 가능 모델로 교체
- API 키는 서버 환경변수로만 사용되며, 프론트엔드로 전달되지 않습니다.

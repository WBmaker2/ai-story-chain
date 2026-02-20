# 테스트 가이드 (Pixazo)

## 1) 로컬 설정

```bash
cd /Users/kimhongnyeon/Documents/Codex/ai-story-chain
cp .env.example .env
```

- `.env`에 `PIXAZO_API_KEY`(구독 키)를 반드시 추가

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
  - 응답 코드가 `402`면 업스트림 크레딧/플랜 제한
  - 응답 코드가 `404`면 `PIXAZO_ENDPOINT`와 요청 파라미터 형식 확인
  - 응답 코드가 `401`이면 `PIXAZO_API_KEY`(구독 키) 확인

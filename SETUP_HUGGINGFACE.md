# Hugging Face Inference API 설정 가이드

## 🎯 목표

교육용 이미지 생성을 위해 **Hugging Face Inference API**를 무료로 설정하고 테스트합니다.

---

## 📋 1단계: Hugging Face Token 발급

### 1-1. 계정 생성
1. https://huggingface.co 접속
2. **Sign Up** 클릭 (무료)
3. 이메일 또는 Google/GitHub 계정으로 가입

### 1-2. Access Token 발급
1. 로그인 후 우측 상단 프로필 클릭
2. **Settings** → **Access Tokens** 탭
3. **New token** 버튼 클릭
4. 정보 입력:
   - **Name**: `story-train` (또는 원하는 이름)
   - **Type**: `Read` 선택
5. **Generate token** 클릭
6. 생성된 토큰 복사 (형식: `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

> ⚠️ **중요**: Token은 한 번만 표시되므로 반드시 복사해서 안전하게 보관하세요.

---

## 📝 2단계: .env 파일 설정

### 2-1. .env 파일 편집

프로젝트 루트의 `.env` 파일을 열어 다음을 추가:

```bash
# Hugging Face Inference API
HUGGINGFACE_TOKEN=hf_여기에_실제_토큰_입력
HUGGINGFACE_MODEL=runwayml/stable-diffusion-v1-5

# 다른 모델 사용 시 (선택)
# HUGGINGFACE_MODEL=stabilityai/stable-diffusion-2-1
# HUGGINGFACE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
```

### 2-2. 사용 가능한 모델

| 모델 | 특징 | 크기 |
|------|------|------|
| `runwayml/stable-diffusion-v1-5` | 기본, 빠름 | 작음 |
| `stabilityai/stable-diffusion-2-1` | 고해상도 지원 | 중간 |
| `stabilityai/stable-diffusion-xl-base-1.0` | 최고 품질 | 큼 |

---

## 🧪 3단계: 테스트

### 3-1. 서버 시작

```bash
cd /Users/kimhongnyeon/Dev/codex/ai-story-chain
python3 server.py
```

서버가 다음과 같이 시작되어야 합니다:
```
Story Train server running: http://0.0.0.0:4173
```

### 3-2. API 테스트 (새 터미널)

```bash
curl -X POST http://127.0.0.1:4173/api/generate-image \
  -H "Content-Type: application/json" \
  -d '{"sentence":"기차가 무지개 터널을 지나갔어요"}' \
  -o response.json

# 결과 확인
cat response.json | head -c 200
```

성공 시:
```json
{
  "imageDataUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA..."
}
```

### 3-3. 브라우저 테스트

1. http://127.0.0.1:4173 접속
2. 문장 입력: "기차가 무지개 터널을 지나갔어요"
3. **기차 칸 추가하기** 클릭
4. 이미지가 생성되는지 확인

---

## 🔍 4단계: 서버 로그 확인

서버 로그에서 fallback 동작 확인:

```
[1/2] Pollinations.ai 시도: 기차가 무지개 터널을 지나갔어요...
  ⚠️ Pollinations 실패: HTTP Error 403
[2/2] Hugging Face 시도...
✅ 성공: image/jpeg, 45,678 bytes
```

---

## 🚨 문제 해결

### 문제 1: "HUGGINGFACE_TOKEN 환경변수가 설정되지 않았습니다"
- **해결**: .env 파일에 Token이 올바르게 입력되었는지 확인

### 문제 2: "Hugging Face 오류 (401)"
- **원인**: Token이 만료되었거나 잘못됨
- **해결**: Token 재발급 후 .env 업데이트

### 문제 3: "Hugging Face 오류 (503): Model loading"
- **원인**: 모델이 콜드 스타트 중 (첫 요청 시)
- **해결**: 30~60초 후 다시 시도

### 문제 4: 이미지 생성이 너무 느림
- **해결**: 더 가벼운 모델 사용
  ```bash
  HUGGINGFACE_MODEL=runwayml/stable-diffusion-v1-5
  ```

---

## 📊 요약

| 항목 | 상태 |
|------|------|
| Hugging Face 계정 | 무료 생성 가능 |
| Access Token | 무료 발급 (Read 권한) |
| API 호출 | 무료 (Serverless) |
| 제한 | 공정 사용 정책 |
| 추천 모델 | runwayml/stable-diffusion-v1-5 |

---

## 🔗 유용한 링크

- [Hugging Face 모델 탐색](https://huggingface.co/models?pipeline_tag=text-to-image)
- [Inference API 문서](https://huggingface.co/docs/api-inference/index)
- [요금 안내](https://huggingface.co/pricing) - 무료 tier 확인

---

**설정 완료 후 `/pdca analyze ai-story-chain`로 Gap Analysis를 실행해 주세요!**

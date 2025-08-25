## 🤖 AI 지인 추천 서비스 - 기술 스택 및 구현 방식

### 🎯 AI 핵심 기술 스택

1. **대화형 AI (LLM)**
- Google Gemini 1.5 Flash API
    - 사용자 요청 텍스트 자동 분류 (6개 카테고리)
    - 자연어 처리를 통한 의도 파악
    - 실시간 카테고리 추론 (repair, cleaning, pest_control, tech_service, life_helper, senior_support)
1. **머신러닝 추천 시스템**
- Random Forest Classifier
    - scikit-learn 기반 앙상블 학습 모델
    - 연결 성공률 예측 (이진 분류)
    - 실시간 AI 점수 계산 (0.0~1.0)
1. **데이터 분석 & 전처리**
- Pandas: 대용량 사용자 데이터 처리
- One-Hot Encoding: 범주형 데이터 변환
- Feature Engineering: 관계 거리, 나이대, 성별, 카테고리 특성 추출

---

### 🔧 AI 시스템 아키텍처

**하이브리드 AI 접근법**

사용자 요청 → Gemini API (1차) → 키워드 매칭 (2차) → ML 모델 → 최종 추천

**2단계 점수 계산 시스템**

1. ML 기반 점수: Random Forest로 연결 성공 확률 예측
2. 프로필 매칭 점수: 텍스트 유사도 + 키워드 매칭

---

### 📊 AI 모델 학습 데이터 구조

**학습 특성 (Features)**

features = [
'relationship_degree',    # 관계 거리 (1촌, 2촌 등)
'category',              # 요청 카테고리
'requester_age',         # 요청자 연령대
'candidate_gender'       # 후보자 성별
]

**예측 목표 (Target)**

- is_successful: 연결 성공 여부 (0/1)

---

### 🚀 AI 핵심 알고리즘

1. 카테고리 추론 (Gemini AI)

### Gemini API로 자연어 → 카테고리 분류

category = gemini_model.generate_content(
system_prompt + user_request
).text.strip()

1. 프로필 매칭 스코어링

### 키워드 기반 유사도 + 매너온도 보정

match_score = direct_keyword_match * 0.5 +
category_keyword_match * 0.4 +
manner_temperature_bonus

1. ML 기반 성공률 예측

### Random Forest로 연결 성공 확률 계산

ml_score = model.predict_proba(encoded_features)[0, 1]
final_score = ml_score * profile_weight

---

### 💡 AI 혁신 포인트

1. **이중 안전망 시스템**
- Gemini API 실패 시 키워드 기반 분류로 자동 백업
- 서비스 안정성 보장
1. **동적 임계값 조정**
- 최고 점수 대비 70% 이상만 추천
- 품질 기반 필터링으로 정확도 향상
1. **실시간 학습 데이터 수집**
- 사용자 피드백 → 재학습 데이터 자동 생성
- 지속적인 모델 성능 개선

---

### 🏆 기술적 차별화 요소

1. 멀티모달 AI 융합: LLM + ML + 규칙 기반 시스템
2. 실시간 추천: API 호출 시점에 동적 점수 계산
3. 확장 가능한 아키텍처: 새로운 카테고리 추가 용이
4. 데이터 드리븐: 실제 연결 성공 데이터로 모델 훈련

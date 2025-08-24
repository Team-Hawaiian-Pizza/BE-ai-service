# create_dummy_data.py
import pandas as pd
import random

# --- 설정 ---
NUM_SAMPLES = 5000  # 생성할 데이터 샘플 수
CATEGORIES = ['repair', 'cleaning', 'pest_control', 'tech_service', 'life_helper', 'senior_support']
AGE_BANDS = ['20s', '30s', '40s', '50s+']
GENDERS = ['male', 'female']
CITIES = ['미추홀구']

# --- 데이터 생성 ---
data = []
for _ in range(NUM_SAMPLES):
    # 1. 입력 데이터 (Features) 랜덤 생성
    relationship_degree = random.choice([1, 2, 3])
    category = random.choice(CATEGORIES)
    requester_age = random.choice(AGE_BANDS)
    candidate_gender = random.choice(GENDERS)
    requester_city = random.choice(CITIES)
    candidate_city = random.choice(CITIES)

    # 2. 정답 데이터 (Label) 생성 - 간단한 규칙 기반
    # 기본 성공 확률은 10%로 설정
    success_probability = 0.10

    # 규칙 1: 1촌 관계일수록 성공 확률 증가
    if relationship_degree == 1:
        success_probability += 0.40  # 40%p 증가
    elif relationship_degree == 2:
        success_probability += 0.20  # 20%p 증가

    # 규칙 2: 긴급한 카테고리일수록 성공 확률 약간 증가
    if category in ['repair', 'pest_control']:
        success_probability += 0.10

    # 규칙 3: 같은 지역일 경우 성공 확률 증가
    if requester_city == candidate_city:
        success_probability += 0.15

    # 최종적으로 성공 여부(0 또는 1) 결정
    is_successful = 1 if random.random() < success_probability else 0

    data.append({
        'relationship_degree': relationship_degree,
        'category': category,
        'requester_age': requester_age,
        'candidate_gender': candidate_gender,
        'requester_city': requester_city,
        'candidate_city': candidate_city,
        'is_successful': is_successful
    })

# --- CSV 파일로 저장 ---
df = pd.DataFrame(data)
df.to_csv('recommendation_logs.csv', index=False)

print(f"'{NUM_SAMPLES}'개의 더미 데이터가 'recommendation_logs.csv' 파일로 생성되었습니다.")
print("생성된 데이터의 성공/실패 비율:")
print(df['is_successful'].value_counts(normalize=True))
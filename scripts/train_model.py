# train_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# 1. 데이터 로드
# 이 CSV 파일은 1단계에서 생성한 데이터라고 가정합니다.
data = pd.read_csv('./data/recommendation_logs.csv')

# 2. 데이터 전처리
# 모델이 학습할 수 있도록 텍스트 데이터를 숫자로 변환합니다 (One-Hot Encoding).
features = pd.get_dummies(data[['relationship_degree', 'category', 'requester_age', 'candidate_gender']])
labels = data['is_successful'] # 'is_successful'은 0 또는 1의 값을 가짐

# 3. 학습/테스트 데이터 분리
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# 4. 모델 생성 및 학습
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. 모델 평가
predictions = model.predict(X_test)
print(f"모델 정확도: {accuracy_score(y_test, predictions):.2f}")

# 6. 학습된 모델 파일로 저장
joblib.dump(model, 'recommendation_model.joblib')
print("모델이 'recommendation_model.joblib' 파일로 저장되었습니다.")
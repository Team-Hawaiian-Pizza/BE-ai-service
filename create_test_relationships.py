#!/usr/bin/env python
"""
테스트용 관계 데이터를 생성하는 스크립트
Core service에서 가져온 사용자들 간의 관계를 설정합니다.
"""

import os
import django
import sys

# Django 설정
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_service.settings')
django.setup()

from ai.models import Relationships

def create_test_relationships():
    """테스트용 관계 데이터 생성"""
    
    # 기존 데이터 삭제 (테스트용)
    Relationships.objects.all().delete()
    print("기존 관계 데이터를 모두 삭제했습니다.")
    
    # Core service 사용자 ID: 1(성시경), 2(김민준), 3(이서연), 4(박지후), 5(최예준)
    
    # 1차 관계 (직접 친구) 설정
    relationships_1st = [
        (1, 2, 'active'),  # 성시경 - 김민준
        (1, 3, 'active'),  # 성시경 - 이서연  
        (2, 4, 'active'),  # 김민준 - 박지후
        (3, 5, 'active'),  # 이서연 - 최예준
        (4, 5, 'active'),  # 박지후 - 최예준
    ]
    
    # 2차 관계가 생성되도록 관계 설정
    # 성시경(1) -> 김민준(2) -> 박지후(4) : 성시경과 박지후는 2촌
    # 성시경(1) -> 이서연(3) -> 최예준(5) : 성시경과 최예준은 2촌
    
    for user_from, user_to, status in relationships_1st:
        relationship = Relationships.objects.create(
            user_from_id=user_from,
            user_to_id=user_to,
            status=status
        )
        print(f"관계 생성: 사용자 {user_from} ↔ 사용자 {user_to} ({status})")
    
    print(f"\n총 {len(relationships_1st)}개의 관계를 생성했습니다.")
    
    # 관계 확인
    total_relationships = Relationships.objects.count()
    print(f"데이터베이스에 저장된 총 관계 수: {total_relationships}")
    
    # 각 사용자별 1차 친구 수 확인
    from django.db import models
    for user_id in range(1, 6):
        friends_count = Relationships.objects.filter(
            models.Q(user_from_id=user_id) | models.Q(user_to_id=user_id),
            status='active'
        ).count()
        print(f"사용자 {user_id}의 친구 수: {friends_count}명")

if __name__ == "__main__":
    create_test_relationships()
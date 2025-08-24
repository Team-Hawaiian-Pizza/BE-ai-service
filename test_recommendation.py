#!/usr/bin/env python
"""
AI 추천 시스템을 직접 테스트하는 스크립트
"""

import os
import django
import sys

# Django 설정
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AI_service.settings')
django.setup()

from ai.services import AIRecommendationService

def test_recommendation():
    """AI 추천 시스템 테스트"""
    
    service = AIRecommendationService()
    
    # 테스트 케이스들
    test_cases = [
        {
            "user_id": 1,
            "request_text": "화장실 변기가 막혔는데 수리해줄 수 있는 분 찾아요",
            "description": "성시경(1)이 수리 서비스 요청"
        },
        {
            "user_id": 2, 
            "request_text": "바퀴벌레가 너무 많이 나와서 방역 전문가가 필요합니다",
            "description": "김민준(2)이 방역 서비스 요청"
        },
        {
            "user_id": 3,
            "request_text": "이사 청소 전문적으로 해주실 분 필요해요", 
            "description": "이서연(3)이 청소 서비스 요청"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== 테스트 케이스 {i}: {test_case['description']} ===")
        print(f"요청 텍스트: {test_case['request_text']}")
        
        try:
            # AI 추천 실행
            result = service.create_recommendation_request(
                user_id=test_case['user_id'],
                request_text=test_case['request_text'],
                max_recommendations=3
            )
            
            print(f"[SUCCESS] Category: {result['inferred_category']}")
            print(f"Request ID: {result['request_id']}")
            print(f"Recommendations count: {len(result['recommendations'])}")
            
            if result['recommendations']:
                print("Recommendations:")
                for j, rec in enumerate(result['recommendations'], 1):
                    print(f"  {j}. User: {rec.get('recommended_user', {}).get('name', 'Unknown')}")
                    print(f"     ID: {rec.get('recommended_user', {}).get('id', 'N/A')}")
                    print(f"     Location: {rec.get('recommended_user', {}).get('city_name', 'Unknown')}")
                    print(f"     Introducer: {rec.get('introducer_user', {}).get('name', 'Unknown')}")
                    print(f"     AI Score: {rec.get('ai_score', 0)}")
                    print(f"     Degree: {rec.get('relationship_degree', 0)}")
                    print("     ---")
            else:
                print("[ERROR] No recommendations found.")
                
        except Exception as e:
            print(f"[ERROR] Exception: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_recommendation()
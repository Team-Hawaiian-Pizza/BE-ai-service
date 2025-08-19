import time
import requests
import json
from statistics import mean, median

def test_ai_recommendation_speed():
    """AI 추천 서비스 속도 테스트"""
    
    # 테스트할 다양한 요청들
    test_requests = [
        {
            "user_id": 1,
            "request_text": "스타트업 창업을 위한 투자자를 소개받고 싶어요",
            "max_recommendations": 3
        },
        {
            "user_id": 2,
            "request_text": "AI 머신러닝 연구에 관심있는 대학원생과 연결하고 싶습니다",
            "max_recommendations": 5
        },
        {
            "user_id": 3,
            "request_text": "프론트엔드 개발자로 이직을 위한 멘토를 찾고 있어요",
            "max_recommendations": 3
        },
        {
            "user_id": 4,
            "request_text": "같이 등산할 수 있는 취미 친구를 만나고 싶어요",
            "max_recommendations": 2
        },
        {
            "user_id": 5,
            "request_text": "블록체인 기술에 대해 토론할 수 있는 전문가와 연결하고 싶습니다",
            "max_recommendations": 4
        }
    ]
    
    base_url = "http://localhost:8000/api/ai"
    headers = {"Content-Type": "application/json"}
    
    print("AI 추천 서비스 속도 테스트 시작...")
    print("=" * 60)
    
    response_times = []
    successful_requests = 0
    
    for i, test_data in enumerate(test_requests, 1):
        print(f"\n테스트 {i}: {test_data['request_text'][:30]}...")
        
        start_time = time.time()
        
        try:
            # API 요청 실행
            response = requests.post(
                f"{base_url}/recommend/",
                json=test_data,
                headers=headers,
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 201:
                successful_requests += 1
                response_times.append(response_time)
                
                # 응답 데이터 파싱
                data = response.json()
                category = data.get('inferred_category', 'unknown')
                recommendation_count = len(data.get('recommendations', []))
                
                print(f"   성공 - {response_time:.2f}초")
                print(f"   카테고리: {category}")
                print(f"   추천 수: {recommendation_count}개")
                
            else:
                print(f"   실패 - HTTP {response.status_code}")
                print(f"   응답: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print(f"   타임아웃 (30초 초과)")
        except requests.exceptions.ConnectionError:
            print(f"   연결 실패 - 서버가 실행 중인지 확인하세요")
        except Exception as e:
            print(f"   오류: {str(e)}")
    
    # 통계 계산 및 출력
    print("\n" + "=" * 60)
    print("속도 테스트 결과")
    print("=" * 60)
    
    if response_times:
        print(f"성공한 요청: {successful_requests}/{len(test_requests)}")
        print(f"평균 응답 시간: {mean(response_times):.2f}초")
        print(f"중간값 응답 시간: {median(response_times):.2f}초")
        print(f"가장 빠른 응답: {min(response_times):.2f}초")
        print(f"가장 느린 응답: {max(response_times):.2f}초")
        
        # 성능 평가
        avg_time = mean(response_times)
        if avg_time < 2:
            performance = "매우 빠름"
        elif avg_time < 5:
            performance = "빠름"
        elif avg_time < 10:
            performance = "양호"
        elif avg_time < 20:
            performance = "느림"
        else:
            performance = "매우 느림"
            
        print(f"성능 등급: {performance}")
        
        # 세부 응답 시간 분포
        print(f"\n세부 응답 시간:")
        for i, rt in enumerate(response_times, 1):
            print(f"   테스트 {i}: {rt:.2f}초")
            
    else:
        print("성공한 요청이 없습니다. 서버 상태를 확인하세요.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_ai_recommendation_speed()
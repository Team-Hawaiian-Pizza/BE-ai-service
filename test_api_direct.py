#!/usr/bin/env python
"""
AI 추천 API 직접 테스트 (Django 없이)
Core Service 연동 테스트만 수행
"""

import sys
import os
import requests
import json

# Django 환경변수 mock 설정
os.environ['GOOGLE_API_KEY'] = 'test-key'

# 간단한 Mock 클래스들
class MockConnectionRequest:
    def __init__(self, **kwargs):
        self.id = 1
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def create(cls, **kwargs):
        return cls(**kwargs)

class MockRecommendationLog:
    def __init__(self, **kwargs):
        self.id = 1
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod 
    def create(cls, **kwargs):
        return cls(**kwargs)

# Mock된 AI 추천 서비스 클래스
class TestAIRecommendationService:
    def __init__(self):
        pass
    
    def infer_category(self, request_text: str) -> str:
        # 간단한 카테고리 추론 로직
        if any(word in request_text for word in ['전기', '수리', '고장']):
            return 'repair'
        return 'life_helper'

    def _fetch_user_profiles_from_core_service(self, user_ids):
        """Core 서비스에서 사용자 프로필 가져오기"""
        core_service_url = "http://13.124.106.69:8000/users/all"
        
        try:
            response = requests.get(core_service_url, timeout=10)
            response.raise_for_status()
            api_data = response.json()
            
            all_users = api_data.get('results', [])
            user_ids_set = set(user_ids)
            filtered_users = [
                user for user in all_users 
                if user.get('id') in user_ids_set
            ]
            
            print(f"[INFO] Core 서비스에서 {len(filtered_users)}명 사용자 정보 가져옴")
            return filtered_users
            
        except Exception as e:
            print(f"[ERROR] Core 서비스 호출 실패: {e}")
            return []

    def _fetch_network_graph_from_core_service(self, center_user_id, depth=2):
        """Core 서비스에서 네트워크 그래프 데이터 가져오기"""
        core_graph_url = "http://13.124.106.69:8000/network/graph"
        
        try:
            params = {
                'depth': depth,
                'format': 'json',
                'center': center_user_id
            }
            
            response = requests.get(core_graph_url, params=params, timeout=10)
            response.raise_for_status()
            graph_data = response.json()
            
            print(f"[INFO] Core 서비스에서 네트워크 그래프 데이터 가져옴 - 중심: {graph_data.get('center')}, 노드: {len(graph_data.get('nodes', []))}, 엣지: {len(graph_data.get('edges', []))}")
            return graph_data
            
        except Exception as e:
            print(f"[ERROR] Core 서비스 네트워크 그래프 호출 실패: {e}")
            return {}

    def find_potential_connections(self, requester_id, category, location=None, max_recommendations=5):
        """2촌 추천 찾기"""
        
        print(f"[DEBUG] 추천 시작 - 요청자: {requester_id}, 카테고리: {category}")
        
        # Core 서비스에서 네트워크 그래프 데이터 가져오기
        graph_data = self._fetch_network_graph_from_core_service(requester_id, depth=2)
        
        if not graph_data or 'edges' not in graph_data:
            print(f"[DEBUG] 네트워크 그래프 데이터를 가져올 수 없어서 추천 종료")
            return []
        
        edges = graph_data['edges']
        center_user = graph_data.get('center', requester_id)
        
        print(f"[DEBUG] 네트워크 그래프 - 중심: {center_user}, 엣지 수: {len(edges)}")
        
        # 1차 관계 (직접 연결된 친구들) 찾기
        first_degree_friends = set()
        for edge in edges:
            source = edge['source']
            target = edge['target']
            
            if source == requester_id:
                first_degree_friends.add(target)
            elif target == requester_id:
                first_degree_friends.add(source)
        
        print(f"[DEBUG] 1촌 친구들: {first_degree_friends}")
        
        if not first_degree_friends:
            print(f"[DEBUG] 1촌 친구가 없어서 추천 종료")
            return []

        # 2차 관계 (친구의 친구들) 후보 찾기
        candidates = {}
        connected_users = {requester_id} | first_degree_friends
        
        for introducer_id in first_degree_friends:
            for edge in edges:
                source = edge['source']
                target = edge['target']
                
                candidate_id = None
                if source == introducer_id and target not in connected_users:
                    candidate_id = target
                elif target == introducer_id and source not in connected_users:
                    candidate_id = source
                
                if candidate_id and candidate_id not in candidates:
                    candidates[candidate_id] = introducer_id
        
        print(f"[DEBUG] 2촌 후보들: {candidates}")
        
        if not candidates:
            print(f"[DEBUG] 2촌 후보가 없어서 추천 종료")
            return []

        # Core 서비스에서 후보들의 프로필 정보 일괄 조회
        candidate_profiles = self._fetch_user_profiles_from_core_service(list(candidates.keys()))
        print(f"[DEBUG] Core 서비스에서 가져온 프로필 수: {len(candidate_profiles)}")

        # 최종 추천 목록 생성
        recommendations = []
        for profile in candidate_profiles:
            candidate_id = profile['id']
            introducer_id = candidates[candidate_id]

            # 간단한 AI 점수 계산 (0.7~0.9)
            import random
            ai_score = round(random.uniform(0.7, 0.9), 3)
            
            recommendations.append({
                'recommended_user_id': candidate_id,
                'introducer_user_id': introducer_id,
                'relationship_degree': 2,
                'ai_score': ai_score
            })
        
        # AI 점수 기준으로 정렬하고 상위 N개 반환
        recommendations.sort(key=lambda x: x['ai_score'], reverse=True)
        final_recommendations = recommendations[:max_recommendations]
        print(f"[DEBUG] 최종 추천 결과: {len(final_recommendations)}개")
        return final_recommendations

    def create_recommendation_request(self, user_id, request_text, max_recommendations=5):
        """추천 요청 생성 및 처리 (Mock)"""
        
        print(f"[API] 추천 요청 - 사용자: {user_id}, 텍스트: '{request_text}'")
        
        # 카테고리 추론
        category = self.infer_category(request_text)
        print(f"[API] 추론된 카테고리: {category}")
        
        # Mock 연결 요청 생성
        connection_request = MockConnectionRequest(
            requester_user_id=user_id,
            request_text=request_text,
            inferred_category=category,
            status='pending'
        )
        
        # 추천 생성
        potential_connections = self.find_potential_connections(
            user_id, category, location=None, max_recommendations=max_recommendations
        )
        
        # 모든 관련 사용자 ID 수집
        all_user_ids = set()
        for conn in potential_connections:
            all_user_ids.add(conn['recommended_user_id'])
            all_user_ids.add(conn['introducer_user_id'])
        
        # Core 서비스에서 사용자 프로필 가져오기
        user_profiles = self._fetch_user_profiles_from_core_service(list(all_user_ids))
        user_profile_dict = {profile['id']: profile for profile in user_profiles}
        
        enhanced_recommendations = []
        for conn in potential_connections:
            # Mock 로그 생성
            log = MockRecommendationLog(
                request=connection_request,
                recommended_user=conn['recommended_user_id'],
                introducer_user=conn['introducer_user_id'],
                relationship_degree=conn['relationship_degree'],
                ai_score=conn['ai_score']
            )
            
            # 향상된 추천 데이터 생성
            enhanced_rec = {
                'id': log.id,
                'recommended_user': user_profile_dict.get(conn['recommended_user_id'], {}),
                'introducer_user': user_profile_dict.get(conn['introducer_user_id'], {}),
                'relationship_degree': conn['relationship_degree'],
                'ai_score': conn['ai_score']
            }
            enhanced_recommendations.append(enhanced_rec)
        
        return {
            'request_id': connection_request.id,
            'recommendations': enhanced_recommendations,
            'inferred_category': category
        }

if __name__ == "__main__":
    print("=== AI 추천 API 직접 테스트 ===")
    
    service = TestAIRecommendationService()
    
    # 테스트 요청
    result = service.create_recommendation_request(
        user_id=1,
        request_text="전기 수리가 필요해요",
        max_recommendations=5
    )
    
    print(f"\n=== 최종 API 응답 ===")
    print(f"요청 ID: {result['request_id']}")
    print(f"추론된 카테고리: {result['inferred_category']}")
    print(f"추천 결과: {len(result['recommendations'])}개")
    
    for i, rec in enumerate(result['recommendations'], 1):
        recommended_user = rec['recommended_user']
        introducer_user = rec['introducer_user']
        print(f"{i}. 추천: {recommended_user.get('name', 'Unknown')} (ID: {recommended_user.get('id')})")
        print(f"   소개자: {introducer_user.get('name', 'Unknown')} (ID: {introducer_user.get('id')})")
        print(f"   AI점수: {rec['ai_score']}")
        print()
#!/usr/bin/env python
"""
AI 추천 서비스 테스트 스크립트
Core Service API 연동 테스트
"""

import os
import requests
from typing import Dict, Any, List

class TestAIRecommendationService:
    def _fetch_network_graph_from_core_service(self, center_user_id: int, depth: int = 2) -> Dict[str, Any]:
        """Core 서비스에서 네트워크 그래프 데이터를 가져오는 메서드"""
        core_graph_url = f"http://13.124.106.69:8000/network/graph"
        
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
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Core 서비스 네트워크 그래프 호출 실패: {e}")
            return {}
            
        except Exception as e:
            print(f"[ERROR] 네트워크 그래프 조회 중 예상치 못한 오류: {e}")
            return {}

    def test_find_potential_connections(self, requester_id: int):
        """2촌 추천 로직 테스트"""
        
        print(f"[DEBUG] 추천 시작 - 요청자: {requester_id}")
        
        # 1. Core 서비스에서 네트워크 그래프 데이터 가져오기
        graph_data = self._fetch_network_graph_from_core_service(requester_id, depth=2)
        
        if not graph_data or 'edges' not in graph_data:
            print(f"[DEBUG] 네트워크 그래프 데이터를 가져올 수 없어서 추천 종료")
            return []
        
        edges = graph_data['edges']
        center_user = graph_data.get('center', requester_id)
        
        print(f"[DEBUG] 네트워크 그래프 - 중심: {center_user}, 엣지 수: {len(edges)}")
        
        # 2. 1차 관계 (직접 연결된 친구들) 찾기
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

        # 3. 2차 관계 (친구의 친구들) 후보 찾기
        candidates = {}  # {후보자_id: 소개해준_친구_id}
        connected_users = {requester_id} | first_degree_friends  # 이미 연결된 사용자들
        
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
        
        print(f"[DEBUG] 최종 추천 후보: {len(candidates)}명")
        return candidates

if __name__ == "__main__":
    service = TestAIRecommendationService()
    
    # 사용자 ID 1번으로 테스트
    print("=== 사용자 1번 (성시경) 추천 테스트 ===")
    result = service.test_find_potential_connections(1)
    
    if result:
        print(f"추천 성공: {len(result)}명의 2촌 후보 발견")
        for candidate_id, introducer_id in result.items():
            print(f"  - 후보: {candidate_id}, 소개자: {introducer_id}")
    else:
        print("추천 실패: 후보를 찾을 수 없습니다.")
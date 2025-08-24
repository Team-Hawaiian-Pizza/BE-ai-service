import random
import os
import requests
from typing import List, Dict, Any
from django.db.models import Q
from .models import Relationships, ConnectionRequest, RecommendationLog
import google.generativeai as genai 

class AIRecommendationService:
    """AI 기반 연결 추천 서비스 (Gemini 1.5 Pro API 연동)"""
    
    def __init__(self):
        """서비스 초기화 시 Gemini API 키를 설정합니다."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
        genai.configure(api_key=api_key) # Gemini 설정 방식으로 변경
        
    def _call_gemini_api(self, request_text: str) -> str:
        """Gemini API를 호출하여 카테고리를 추론하는 내부 메서드"""
        # Gemini에게 역할을 부여하고, 원하는 작업과 출력 형식을 명확히 지시
        system_prompt = """
        당신은 '건너건너'라는 생활 서비스 연결 플랫폼의 요청 분석 AI입니다.
        사용자의 요청 텍스트를 분석하여 아래 6가지 생활 서비스 카테고리 중 가장 적합한 것 하나만 골라 소문자로 답해주세요.
        다른 설명은 절대 추가하지 마세요.
        
        카테고리:
        - repair: 수리·유지보수 (전기, 배관, 가전제품, 샷시, 열쇠 등)
        - cleaning: 청소·폐기 (입주청소, 쓰레기처리, 대청소 등)
        - pest_control: 해충·방역 (바퀴벌레, 쥐, 모기, 소독 등)
        - tech_service: 기술 서비스 (포스기, 와이파이, CCTV, 컴퓨터 등)
        - life_helper: 생활 도우미 (짐나르기, 반려동물 산책, 심부름 등)
        - senior_support: 고령자·외국인 지원 (번역, 관공서 동행, 병원 안내 등)
        """
        
        try:
            # 사용할 모델을 지정합니다. (무료 버전용)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 프롬프트와 함께 요청을 보냅니다.
            response = model.generate_content(f"{system_prompt}\n\n사용자 요청: {request_text}")
            
            # Gemini의 답변에서 텍스트만 추출하고 공백을 제거합니다.
            category = response.text.strip().lower()
            
            # 유효한 카테고리인지 확인하는 안전장치
            valid_categories = ['repair', 'cleaning', 'pest_control', 'tech_service', 'life_helper', 'senior_support']
            if category in valid_categories:
                return category
            return 'life_helper' # 유효하지 않은 답변일 경우 기본값 반환

        except Exception as e:
            print(f"Gemini API 호출 중 오류 발생: {e}")
            return 'life_helper' # API 오류 시 기본값 반환    
        
    CATEGORIES = {
        'repair': ['수리', '전기', '배관', '수도', '가전제품', '샷시', '유리', '문', '열쇠', '잠금장치', '벽', '타일', '싱크대', '고장', '수선'],
        'cleaning': ['청소', '입주청소', '이사청소', '가게청소', '대청소', '쓰레기', '분리수거', '폐기물', '가구수거', '정리정돈'],
        'pest_control': ['방역', '바퀴벌레', '쥐', '개미', '모기', '벌', '해충', '소독', '퇴치', '박멸'],
        'tech_service': ['포스기', '프린터', '와이파이', 'CCTV', '앱', '컴퓨터', '기술지원', '설치', '점검', '수리'],
        'life_helper': ['짐나르기', '반려동물', '산책', '벌레잡기', '심부름', '물건구매', '배송', '전달', '도움'],
        'senior_support': ['번역', '통역', '어르신', '집수리', '관공서', '동행', '병원', '약국', '안내', '외국인지원']
    }
    
    def infer_category(self, request_text: str) -> str:
        """요청 텍스트에서 카테고리 추론"""
        return self._call_gemini_api(request_text)
    
    def calculate_ai_score(self, requester_id: int, candidate_profile: Dict[str, Any], introducer_id: int, 
                          relationship_degree: int, category: str) -> float:
        """AI 점수 계산 (실제로는 ML 모델을 사용해야 함)"""
        base_score = 0.5
        
        # 관계 거리가 가까울수록 높은 점수
        degree_score = max(0, (4 - relationship_degree) * 0.2)
        
        # 카테고리별 가중치 (생활 서비스 중요도)
        category_weight = {
            'repair': 0.9,          # 수리는 긴급성이 높음
            'cleaning': 0.7,        # 청소 서비스
            'pest_control': 0.8,    # 방역은 중요도 높음
            'tech_service': 0.8,    # 기술 서비스
            'life_helper': 0.6,     # 일반 생활 도우미
            'senior_support': 0.9   # 고령자 지원은 우선도 높음
        }.get(category, 0.6)
        
        # 랜덤 요소 (실제로는 더 정교한 특성 기반 점수)
        random_factor = random.uniform(0.1, 0.4)
        
        final_score = min(1.0, base_score + degree_score + (category_weight * 0.3) + random_factor)
        return round(final_score, 3)
    
    def _fetch_user_profiles_from_core_service(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Core 서비스의 /all API를 호출하여 모든 사용자 정보를 가져온 뒤,
        필요한 사용자들의 정보만 필터링하여 반환합니다.
        """
        core_service_url = "http://13.124.106.69:8000/users/all" 
        
        try:
            # Core Service API 호출
            headers = {
                'User-Agent': 'Django-AI-Service/1.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(core_service_url, timeout=10, headers=headers)
            response.raise_for_status() 
            api_data = response.json()
            
            # API 응답에서 results 키의 사용자 리스트를 가져옵니다.
            all_users = api_data.get('results', [])
            
            # 필요한 user_id만 필터링
            user_ids_set = set(user_ids)
            filtered_users = [
                user for user in all_users 
                if user.get('id') in user_ids_set
            ]
            
            print(f"[INFO] Core 서비스에서 {len(filtered_users)}명 사용자 정보 가져옴")
            return filtered_users

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Core 서비스 호출 실패: {e}")
            return []
            
        except Exception as e:
            print(f"[ERROR] 예상치 못한 오류: {e}")
            return []
    
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

    def find_potential_connections(self, requester_id: int, category: str, 
                                   location: str = None, max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """잠재적 연결 대상(2촌)을 찾고, 필터링 및 점수 계산 후 최종 추천 목록 반환"""
        
        print(f"[DEBUG] 추천 시작 - 요청자: {requester_id}, 카테고리: {category}")
        
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
        
        all_candidate_ids = list(candidates.keys())
        print(f"[DEBUG] 2촌 후보들: {candidates}")
        
        if not all_candidate_ids:
            print(f"[DEBUG] 2촌 후보가 없어서 추천 종료")
            return [] # 2촌 후보가 없으면 종료

        # 3. Core 서비스에서 후보들의 프로필 정보를 일괄 조회
        candidate_profiles = self._fetch_user_profiles_from_core_service(all_candidate_ids)
        print(f"[DEBUG] Core 서비스에서 가져온 프로필 수: {len(candidate_profiles)}")

        # 4. (선택사항) 동네 기반으로 후보 필터링
        if location:
            candidate_profiles = [
                profile for profile in candidate_profiles
                if profile.get('city_name') and location in profile.get('city_name')
            ]
        
        # 5. 최종 추천 목록 생성 및 점수 계산
        recommendations = []
        for profile in candidate_profiles:
            candidate_id = profile['id']
            introducer_id = candidates[candidate_id]

            ai_score = self.calculate_ai_score(
                requester_id=requester_id, 
                candidate_profile=profile, 
                introducer_id=introducer_id,
                relationship_degree=2, # 2촌 관계이므로 2로 고정
                category=category
            )
            recommendations.append({
                'recommended_user_id': candidate_id,
                'introducer_user_id': introducer_id,
                'relationship_degree': 2,
                'ai_score': ai_score
            })
            
        # 6. AI 점수 기준으로 정렬하고 상위 N개 반환
        recommendations.sort(key=lambda x: x['ai_score'], reverse=True)
        final_recommendations = recommendations[:max_recommendations]
        print(f"[DEBUG] 최종 추천 결과: {len(final_recommendations)}개")
        return final_recommendations
    
    def create_recommendation_request(self, user_id: int, request_text: str, 
                                   max_recommendations: int = 5) -> Dict[str, Any]:
        """추천 요청 생성 및 처리"""
        
        # 카테고리 추론
        category = self.infer_category(request_text)
        
        # 연결 요청 생성
        connection_request = ConnectionRequest.objects.create(
            requester_user_id=user_id,
            request_text=request_text,
            inferred_category=category,
            status='pending'
        )
        
        # 추천 생성 (location 파라미터 추가)
        potential_connections = self.find_potential_connections(
            user_id, category, location=None, max_recommendations=max_recommendations
        )
        
        recommendation_logs = []
        enhanced_recommendations = []
        
        # 모든 관련 사용자 ID 수집 (추천자 + 소개자)
        all_user_ids = set()
        for conn in potential_connections:
            all_user_ids.add(conn['recommended_user_id'])
            all_user_ids.add(conn['introducer_user_id'])
        
        # Core 서비스에서 사용자 프로필 가져오기
        user_profiles = self._fetch_user_profiles_from_core_service(list(all_user_ids))
        user_profile_dict = {profile['id']: profile for profile in user_profiles}
        
        for conn in potential_connections:
            # 데이터베이스에 로그 저장
            log = RecommendationLog.objects.create(
                request=connection_request,
                recommended_user=conn['recommended_user_id'],
                introducer_user=conn['introducer_user_id'],
                relationship_degree=conn['relationship_degree'],
                ai_score=conn['ai_score']
            )
            recommendation_logs.append(log)
            
            # 프론트엔드용 향상된 추천 데이터 생성
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
            'recommendations': enhanced_recommendations,  # 향상된 데이터 사용
            'inferred_category': category
        }
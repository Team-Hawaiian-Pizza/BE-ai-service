import random
import os
import requests
from typing import List, Dict, Any
from django.db.models import Q
from .models import Relationships, ConnectionRequest, RecommendationLog
import google.generativeai as genai 
import logging
logger = logging.getLogger(__name__)

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
            logger.error(f"Gemini API 호출 중 오류 발생: {e}")
            return 'life_helper' # API 오류 시 기본값 반환
    
    def infer_category(self, request_text: str) -> str:
        """요청 텍스트에서 카테고리 추론"""
        # 1차: Gemini API 시도
        gemini_result = self._call_gemini_api(request_text)
        if gemini_result != 'life_helper':  # 기본값이 아니면 성공
            return gemini_result
            
        # 2차: 로컬 키워드 기반 추론 (API 실패 시 대안)
        return self._infer_category_locally(request_text)
    
    def _infer_category_locally(self, request_text: str) -> str:
        """로컬 키워드 기반 카테고리 추론 (Gemini API 대안)"""
        text = request_text.lower()
        
        # 키워드 기반 카테고리 매칭
        category_keywords = {
            'pest_control': ['바퀴벌레', 'cockroach', '쥐', 'rat', '방역', 'pest', '해충', '소독', '개미', 'ant'],
            'repair': ['수리', 'repair', 'fix', '고장', '전기', 'electrical', '배관', 'plumbing', '가전'],
            'cleaning': ['청소', 'clean', '정리', 'organize', '이사', 'moving', '입주청소', '대청소'],
            'tech_service': ['cctv', '와이파이', 'wifi', '컴퓨터', 'computer', '포스기', '설치', 'install'],
            'senior_support': ['번역', 'translate', '통역', '병원', 'hospital', '관공서', '동행', '어르신'],
            'life_helper': ['심부름', '배송', 'delivery', '짐나르기', '반려동물', 'pet', '도움']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
                
        return 'life_helper'  # 기본값
    
    def _calculate_profile_match_score(self, request_text: str, category: str, candidate_profile: Dict[str, Any]) -> float:
        """요청 내용과 후보자 프로필의 매칭 점수 계산"""
        intro = candidate_profile.get('intro', '').lower()
        name = candidate_profile.get('name', '').lower()
        
        if not intro:
            return 0.0
        
        # 카테고리별 핵심 키워드 정의 (1차 매칭)
        primary_keywords = {
            'repair': ['수리', '전기', '배관', '수도', '가전', '고장', '수선', '보수', '정비', '교체'],
            'cleaning': ['청소', '정리', '대청소', '입주청소', '이사청소', '비우기', '정돈'],
            'pest_control': ['방역', '바퀴벌레', '쥐', '개미', '모기', '벌', '해충', '소독', '퇴치', '박멸'],
            'tech_service': ['포스기', '프린터', '와이파이', 'cctv', '앱', '컴퓨터', '기술', '설치', '점검'],
            'life_helper': ['짐나르기', '반려동물', '산책', '심부름', '물건구매', '배송', '전달', '도움', '서비스'],
            'senior_support': ['번역', '통역', '어르신', '관공서', '동행', '병원', '약국', '안내', '지원']
        }
        
        # 2차 연관 키워드 정의 (관련 있지만 우선순위 낮음)
        secondary_keywords = {
            'repair': ['도구', '전문가', '기사', '숙련', '경험'],
            'cleaning': ['깔끔', '완벽', '꼼꼼', '청결', '위생'],
            'pest_control': ['전문', '안전', '효과적', '깨끗'],
            'tech_service': ['전문가', '신속', '숙련', '해결'],
            'life_helper': ['친절', '빠른', '안전', '신뢰'],
            'senior_support': ['정중', '친절', '배려', '세심']
        }
        
        # 요청 텍스트에서 중요한 키워드 추출
        request_keywords = set(request_text.lower().split())
        
        match_score = 0.0
        
        # 1차 키워드 매칭 (높은 가중치)
        primary_matches = 0
        for keyword in primary_keywords.get(category, []):
            if keyword in intro:
                primary_matches += 1
                # 요청 텍스트와 직접 매칭되면 추가 점수
                if any(req_word in keyword or keyword in req_word for req_word in request_keywords):
                    match_score += 0.3
                else:
                    match_score += 0.2
        
        # 2차 키워드 매칭 (중간 가중치)  
        secondary_matches = 0
        for keyword in secondary_keywords.get(category, []):
            if keyword in intro:
                secondary_matches += 1
                match_score += 0.1
        
        # 다른 카테고리 키워드 매칭 (낮은 가중치 - 2순위)
        for other_category, keywords in primary_keywords.items():
            if other_category != category:
                for keyword in keywords:
                    if keyword in intro:
                        match_score += 0.05  # 관련 분야로 2순위
        
        # 매너온도 보정 (높은 매너온도 = 신뢰도 높음)
        manner_temp = candidate_profile.get('manner_temperature', 50)
        if manner_temp >= 70:
            match_score += 0.1
        elif manner_temp >= 60:
            match_score += 0.05
        elif manner_temp <= 40:
            match_score -= 0.1
        
        return min(1.0, match_score)
    
    def calculate_ai_score(self, requester_id: int, candidate_profile: Dict[str, Any], introducer_id: int, 
                          relationship_degree: int, category: str, request_text: str = "") -> float:
        """개선된 AI 점수 계산 - 프로필 매칭 기반"""
        base_score = 0.4  # 기본 점수를 높여서 기본 추천도 가능하게
        
        # 1. 관계 거리 점수 (가까울수록 높음)
        degree_score = max(0, (4 - relationship_degree) * 0.15)
        
        # 2. 프로필 매칭 점수 (가장 중요한 요소)
        profile_match_score = self._calculate_profile_match_score(request_text, category, candidate_profile)
        
        # 3. 카테고리별 기본 가중치 
        category_weight = {
            'repair': 0.2,          # 수리
            'cleaning': 0.15,       # 청소 
            'pest_control': 0.2,    # 방역
            'tech_service': 0.2,    # 기술 서비스
            'life_helper': 0.1,     # 생활 도우미
            'senior_support': 0.2   # 고령자 지원
        }.get(category, 0.1)
        
        # 4. 지역 매칭 보너스
        location_bonus = 0.0
        candidate_city = candidate_profile.get('city_name', '')
        if candidate_city:
            location_bonus = 0.05  # 같은 지역이면 약간의 보너스
        
        # 최종 점수 계산 (프로필 매칭이 가장 큰 비중)
        final_score = (
            base_score + 
            degree_score + 
            (profile_match_score * 0.6) +  # 60% 가중치
            (category_weight * 0.2) + 
            location_bonus
        )
        
        return round(min(1.0, max(0.0, final_score)), 3)
    
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
            
            return filtered_users

        except requests.exceptions.RequestException as e:
            logger.error(f"Core 서비스 호출 실패: {e}")
            return []
            
        except Exception as e:
            logger.error(f"사용자 프로필 조회 중 오류: {e}")
            return []
    
    def _fetch_network_graph_from_core_service(self, center_user_id: int, depth: int = 2) -> Dict[str, Any]:
        """Core 서비스에서 네트워크 그래프 데이터를 가져오는 메서드"""
        core_graph_url = f"http://13.124.106.69:8000/network/graph"
        
        try:
            params = {
                'depth': depth,
                'center': center_user_id
            }
            
            response = requests.get(core_graph_url, params=params, timeout=10)
            response.raise_for_status()
            graph_data = response.json()
            return graph_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"네트워크 그래프 조회 실패: {e}")
            return {}
            
        except Exception as e:
            logger.error(f"네트워크 그래프 조회 중 오류: {e}")
            return {}

    def find_potential_connections(self, requester_id: int, category: str, request_text: str = "",
                                   location: str = None, max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """잠재적 연결 대상(2촌)을 찾고, 필터링 및 점수 계산 후 최종 추천 목록 반환"""
        
        # 1. Core 서비스에서 네트워크 그래프 데이터 가져오기
        graph_data = self._fetch_network_graph_from_core_service(requester_id, depth=2)
        
        if not graph_data or 'edges' not in graph_data:
            return []
        
        edges = graph_data['edges']
        center_user = graph_data.get('center', requester_id)
        
        # 2. 1차 관계 (직접 연결된 친구들) 찾기
        first_degree_friends = set()
        for edge in edges:
            source = edge['source']
            target = edge['target']
            
            if source == requester_id:
                first_degree_friends.add(target)
            elif target == requester_id:
                first_degree_friends.add(source)
        
        if not first_degree_friends:
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
        
        if not all_candidate_ids:
            return [] # 2촌 후보가 없으면 종료

        # 3. Core 서비스에서 후보들의 프로필 정보를 일괄 조회
        candidate_profiles = self._fetch_user_profiles_from_core_service(all_candidate_ids)

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
                category=category,
                request_text=request_text
            )
            recommendations.append({
                'recommended_user_id': candidate_id,
                'introducer_user_id': introducer_id,
                'relationship_degree': 2,
                'ai_score': ai_score
            })
            
        # 6. AI 점수 기준으로 정렬하고 상위 N개 반환
        recommendations.sort(key=lambda x: x['ai_score'], reverse=True)
        return recommendations[:max_recommendations]
    
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
        
        # 추천 생성 (request_text와 location 파라미터 추가)
        potential_connections = self.find_potential_connections(
            user_id, category, request_text=request_text, location=None, max_recommendations=max_recommendations
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
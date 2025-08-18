import random
import os
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
        당신은 '건너건너'라는 인맥 연결 서비스의 요청 분석 AI입니다.
        사용자의 요청 텍스트를 분석하여 아래 6가지 카테고리 중 가장 적합한 것 하나만 골라 소문자로 답해주세요.
        다른 설명은 절대 추가하지 마세요.
        카테고리: business, networking, career, academic, hobby, personal
        """
        
        try:
            # 사용할 모델을 지정합니다. (무료 버전용)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 프롬프트와 함께 요청을 보냅니다.
            response = model.generate_content(f"{system_prompt}\n\n사용자 요청: {request_text}")
            
            # Gemini의 답변에서 텍스트만 추출하고 공백을 제거합니다.
            category = response.text.strip().lower()
            
            # 유효한 카테고리인지 확인하는 안전장치
            valid_categories = ['business', 'networking', 'career', 'academic', 'hobby', 'personal']
            if category in valid_categories:
                return category
            return 'networking' # 유효하지 않은 답변일 경우 기본값 반환

        except Exception as e:
            print(f"Gemini API 호출 중 오류 발생: {e}")
            return 'networking' # API 오류 시 기본값 반환    
        
    CATEGORIES = {
        'business': ['사업', '비즈니스', '창업', '투자', '협업', '파트너'],
        'networking': ['네트워킹', '인맥', '소개', '만남', '연결'],
        'career': ['취업', '이직', '커리어', '직업', '진로', '멘토'],
        'academic': ['학술', '연구', '논문', '학회', '교육', '대학'],
        'hobby': ['취미', '관심사', '동호회', '클럽', '활동'],
        'personal': ['개인적', '친구', '지인', '사적', '개인']
    }
    
    def infer_category(self, request_text: str) -> str:
        """요청 텍스트에서 카테고리 추론"""
        return self._call_gemini_api(request_text)
    
    def calculate_ai_score(self, requester_id: int, candidate_id: int, introducer_id: int, 
                          relationship_degree: int, category: str) -> float:
        """AI 점수 계산 (실제로는 ML 모델을 사용해야 함)"""
        base_score = 0.5
        
        # 관계 거리가 가까울수록 높은 점수
        degree_score = max(0, (4 - relationship_degree) * 0.2)
        
        # 카테고리별 가중치
        category_weight = {
            'business': 0.9,
            'career': 0.8,
            'academic': 0.7,
            'networking': 0.8,
            'hobby': 0.6,
            'personal': 0.5
        }.get(category, 0.6)
        
        # 랜덤 요소 (실제로는 더 정교한 특성 기반 점수)
        random_factor = random.uniform(0.1, 0.4)
        
        final_score = min(1.0, base_score + degree_score + (category_weight * 0.3) + random_factor)
        return round(final_score, 3)
    
    def find_potential_connections(self, requester_id: int, category: str, 
                                 max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """잠재적 연결 대상 찾기"""
        
        # 2차, 3차 관계의 사용자들을 찾기
        # 실제로는 더 복잡한 그래프 탐색 알고리즘 필요
        
        # 1차 관계 (직접 연결된 사용자들)
        first_degree = Relationships.objects.filter(
            Q(user_from_id=requester_id) | Q(user_to_id=requester_id),
            status='active'
        ).values_list('user_from_id', 'user_to_id')
        
        connected_users = set()
        for from_id, to_id in first_degree:
            if from_id != requester_id:
                connected_users.add(from_id)
            if to_id != requester_id:
                connected_users.add(to_id)
        
        recommendations = []
        
        # 2차 관계 찾기
        for introducer_id in list(connected_users)[:10]:  # 성능을 위해 제한
            second_degree = Relationships.objects.filter(
                Q(user_from_id=introducer_id) | Q(user_to_id=introducer_id),
                status='active'
            ).exclude(
                Q(user_from_id=requester_id) | Q(user_to_id=requester_id)
            ).values_list('user_from_id', 'user_to_id')
            
            for from_id, to_id in second_degree:
                candidate_id = from_id if from_id != introducer_id else to_id
                
                if candidate_id not in connected_users and candidate_id != requester_id:
                    ai_score = self.calculate_ai_score(
                        requester_id, candidate_id, introducer_id, 2, category
                    )
                    
                    recommendations.append({
                        'recommended_user': candidate_id,
                        'introducer_user': introducer_id,
                        'relationship_degree': 2,
                        'ai_score': ai_score
                    })
        
        # AI 점수 기준으로 정렬하고 상위 N개 반환
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
        
        # 추천 생성
        potential_connections = self.find_potential_connections(
            user_id, category, max_recommendations
        )
        
        recommendation_logs = []
        for conn in potential_connections:
            log = RecommendationLog.objects.create(
                request=connection_request,
                recommended_user=conn['recommended_user_id'],
                introducer_user=conn['introducer_user_id'],
                relationship_degree=conn['relationship_degree'],
                ai_score=conn['ai_score']
            )
            recommendation_logs.append(log)
        
        return {
            'request_id': connection_request.id,
            'recommendations': recommendation_logs,
            'inferred_category': category
        }
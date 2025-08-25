from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render
from .models import ConnectionRequest, RecommendationLog, ConnectionFeedback
from .serializers import (
    ConnectionRequestSerializer, 
    RecommendationLogSerializer,
    ConnectionFeedbackSerializer,
    RecommendationRequestSerializer,
    RecommendationResponseSerializer
)
from .services import AIRecommendationService

class RecommendConnectionView(APIView):
    """AI 기반 연결 추천 API"""
    
    def post(self, request):
        # DEBUG용
        print(f"[DEBUG] API 요청이 RecommendConnectionView에 들어왔습니다. 요청 데이터: {request.data}")
        
        serializer = RecommendationRequestSerializer(data=request.data)
        if serializer.is_valid():
            ai_service = AIRecommendationService()
            
            try:
                result = ai_service.create_recommendation_request(
                    user_id=serializer.validated_data['user_id'],
                    request_text=serializer.validated_data['request_text'],
                    max_recommendations=serializer.validated_data['max_recommendations']
                )
                
                response_serializer = RecommendationResponseSerializer(result)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {'error': f'추천 생성 중 오류가 발생했습니다: {str(e)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConnectionRequestView(APIView):
    """연결 요청 관리 API"""
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            requests = ConnectionRequest.objects.filter(requester_user_id=user_id)
        else:
            requests = ConnectionRequest.objects.all()
        
        serializer = ConnectionRequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    def patch(self, request, pk=None):
        request_id = pk or request.data.get('request_id')
        if not request_id:
            return Response(
                {'error': '요청 ID가 필요합니다'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        connection_request = get_object_or_404(ConnectionRequest, id=request_id)
        
        # 상태 업데이트만 허용
        if 'status' in request.data:
            connection_request.status = request.data['status']
            connection_request.save()
        
        serializer = ConnectionRequestSerializer(connection_request)
        return Response(serializer.data)

class ConnectionFeedbackView(APIView):
    """연결 피드백 API"""
    
    def post(self, request):
        serializer = ConnectionFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            feedback = serializer.save()
            
            # 피드백 점수가 높으면 보상 발송 로직
            if feedback.satisfaction_score >= 4:
                # 여기에 보상 발송 로직 추가
                feedback.reward_sent = True
                feedback.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        request_id = request.query_params.get('request_id')
        if request_id:
            feedback = get_object_or_404(ConnectionFeedback, request_id=request_id)
            serializer = ConnectionFeedbackSerializer(feedback)
            return Response(serializer.data)
        
        feedbacks = ConnectionFeedback.objects.all()
        serializer = ConnectionFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)

def modern_interface(request):
    """AI 인맥 추천 서비스 메인 페이지"""
    return render(request, 'modern_interface.html')

def home(request):
    """메인 서비스 페이지"""
    return render(request, 'modern_interface.html')

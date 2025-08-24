from rest_framework import serializers
from .models import ConnectionRequest, RecommendationLog, ConnectionFeedback, Relationships

class ConnectionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionRequest
        fields = ['id', 'requester_user_id', 'request_text', 'inferred_category', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'inferred_category']

class RecommendationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationLog
        fields = ['id', 'request', 'recommended_user', 'introducer_user', 'relationship_degree', 'ai_score', 'is_selected', 'created_at']
        read_only_fields = ['id', 'created_at']

class ConnectionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectionFeedback
        fields = ['id', 'request', 'final_user', 'satisfaction_score', 'reward_sent', 'created_at']
        read_only_fields = ['id', 'created_at', 'reward_sent']

class RecommendationRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    request_text = serializers.CharField(max_length=1000)
    max_recommendations = serializers.IntegerField(default=5, min_value=1, max_value=10)

class UserProfileSerializer(serializers.Serializer):
    """Core 서비스의 사용자 프로필"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    province_name = serializers.CharField()
    city_name = serializers.CharField()
    gender = serializers.CharField()
    age_band = serializers.CharField()
    intro = serializers.CharField()
    manner_temperature = serializers.IntegerField()

class EnhancedRecommendationSerializer(serializers.Serializer):
    """추천 결과 + 사용자 프로필 정보"""
    id = serializers.IntegerField()
    recommended_user = UserProfileSerializer()
    introducer_user = UserProfileSerializer()
    relationship_degree = serializers.IntegerField()
    ai_score = serializers.FloatField()

class RecommendationResponseSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    recommendations = EnhancedRecommendationSerializer(many=True)
    inferred_category = serializers.CharField()
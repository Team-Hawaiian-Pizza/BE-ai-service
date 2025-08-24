from django.db import models

class Relationships(models.Model):
    # Django는 id(PK)를 자동으로 만들어주므로 생략 가능
    user_from_id = models.BigIntegerField()
    user_to_id = models.BigIntegerField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
class ConnectionRequest(models.Model):
    requester_user_id = models.BigIntegerField()
    request_text = models.TextField()
    inferred_category = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
class RecommendationLog(models.Model):
    request = models.ForeignKey(ConnectionRequest, on_delete=models.CASCADE)
    recommended_user = models.BigIntegerField()
    introducer_user = models.BigIntegerField()
    relationship_degree = models.IntegerField()
    ai_score = models.FloatField()
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
class ConnectionFeedback(models.Model):
    request = models.OneToOneField(ConnectionRequest, on_delete=models.CASCADE)
    final_user = models.BigIntegerField()
    satisfaction_score = models.IntegerField()
    reward_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
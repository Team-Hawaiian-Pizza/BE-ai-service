from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('recommend/', views.RecommendConnectionView.as_view(), name='recommend_connection'),
    path('feedback/', views.ConnectionFeedbackView.as_view(), name='connection_feedback'),
    path('requests/', views.ConnectionRequestView.as_view(), name='connection_requests'),
]
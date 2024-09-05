from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

from .views import ChatbotViewSet
# Create a router and register the ChatbotViewSet
api_router = DefaultRouter()
api_router.register(r'chatbot', ChatbotViewSet, basename='chatbot')

urlpatterns = [
    path('register/', views.CreateUserView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='get_token'),
    path('token/refresh', TokenRefreshView.as_view(), name='refresh_token'),
    
    path('user/', views.UserDetailView.as_view(), name='user_detail'),
    
    path('', include(api_router.urls)),
]
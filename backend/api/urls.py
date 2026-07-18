from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Public
    path('health/', views.health_check, name='health-check'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Protected — Auth
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),

    # Protected — Scanner
    path('scan/', views.scan_plant, name='scan-plant'),
    path('scan/history/', views.scan_history, name='scan-history'),
    path('scan/<int:scan_id>/', views.scan_detail, name='scan-detail'),

    # Protected — Crop
    path('crop/recommend/', views.recommend_crop, name='crop-recommend'),
    path('crop/history/', views.crop_history, name='crop-history'),

    # Protected — Fertilizer
    path('fertilizer/recommend/', views.recommend_fertilizer, name='fertilizer-recommend'),
    path('fertilizer/history/', views.fertilizer_history, name='fertilizer-history'),
]
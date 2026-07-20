from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    path('scan/', views.scan_plant, name='scan-plant'),
    path('scan/history/', views.scan_history, name='scan-history'),
    path('scan/<int:scan_id>/', views.scan_detail, name='scan-detail'),
    path('crop/recommend/', views.recommend_crop, name='crop-recommend'),
    path('crop/history/', views.crop_history, name='crop-history'),
    path('fertilizer/recommend/', views.recommend_fertilizer, name='fertilizer-recommend'),
    path('fertilizer/history/', views.fertilizer_history, name='fertilizer-history'),
    path('irrigation/recommend/', views.recommend_irrigation, name='irrigation-recommend'),
    path('irrigation/history/', views.irrigation_history, name='irrigation-history'),
    path('weather/', views.weather, name='weather'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/suggestions/', views.chatbot_suggestions, name='chatbot-suggestions'),
    path('market/', views.market_prices, name='market-prices'),
    path('market/commodities/', views.market_commodities, name='market-commodities'),
    path('reports/scan/<int:scan_id>/', views.download_scan_report, name='scan-report'),
    path('reports/summary/', views.download_summary_report, name='summary-report'),
    path('admin/stats/', views.admin_stats, name='admin-stats'),
]
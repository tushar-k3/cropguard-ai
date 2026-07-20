from django.contrib import admin
from .models import (
    UserProfile, ScanResult, CropRecommendation,
    FertilizerRecommendation, IrrigationRecommendation, MarketPrice
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'phone', 'location', 'preferred_language', 'created_at']
    list_filter   = ['preferred_language']
    search_fields = ['user__username', 'user__email', 'location']
    ordering      = ['-created_at']


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display  = ['user', 'plant_name', 'is_healthy', 'source', 'confidence', 'created_at']
    list_filter   = ['is_healthy', 'source', 'unsupported_crop']
    search_fields = ['user__username', 'plant_name']
    ordering      = ['-created_at']
    readonly_fields = ['result_data', 'created_at']


@admin.register(CropRecommendation)
class CropRecommendationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'recommended_crop', 'confidence', 'created_at']
    list_filter   = ['recommended_crop']
    search_fields = ['user__username', 'recommended_crop']
    ordering      = ['-created_at']


@admin.register(FertilizerRecommendation)
class FertilizerRecommendationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'crop', 'recommended_fertilizer', 'confidence', 'created_at']
    list_filter   = ['recommended_fertilizer']
    search_fields = ['user__username', 'crop']
    ordering      = ['-created_at']


@admin.register(IrrigationRecommendation)
class IrrigationRecommendationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'crop', 'soil_type', 'water_requirement', 'created_at']
    list_filter   = ['soil_type']
    search_fields = ['user__username', 'crop']
    ordering      = ['-created_at']


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display  = ['commodity', 'market', 'state', 'modal_price', 'price_date', 'fetched_at']
    list_filter   = ['state', 'price_date']
    search_fields = ['commodity', 'market', 'state']
    ordering      = ['-price_date']
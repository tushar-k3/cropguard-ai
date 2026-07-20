from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    phone = models.CharField(max_length=15, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    farm_size = models.CharField(max_length=50, blank=True, default='')
    preferred_language = models.CharField(
        max_length=5,
        choices=[('en', 'English'), ('hi', 'Hindi'), ('mr', 'Marathi')],
        default='en'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — Profile"

    class Meta:
        db_table = 'user_profiles'


class ScanResult(models.Model):
    SOURCE_CHOICES = [
        ('kindwise', 'Kindwise API'),
        ('local_model', 'Local MobileNetV2 Model'),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='scans'
    )
    image = models.ImageField(upload_to='scans/%Y/%m/', blank=True, null=True)
    plant_name = models.CharField(max_length=200, blank=True, default='')
    is_healthy = models.BooleanField(default=True)
    is_plant = models.BooleanField(default=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='kindwise')
    confidence = models.FloatField(default=0.0)
    result_data = models.JSONField(default=dict)
    unsupported_crop = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.plant_name} ({self.source})"

    class Meta:
        db_table = 'scan_results'
        ordering = ['-created_at']


class CropRecommendation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='crop_recommendations'
    )
    nitrogen = models.FloatField()
    phosphorus = models.FloatField()
    potassium = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()
    recommended_crop = models.CharField(max_length=100)
    confidence = models.FloatField(default=0.0)
    result_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.recommended_crop}"

    class Meta:
        db_table = 'crop_recommendations'
        ordering = ['-created_at']


class FertilizerRecommendation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='fertilizer_recommendations'
    )
    crop = models.CharField(max_length=100)
    nitrogen = models.FloatField()
    phosphorus = models.FloatField()
    potassium = models.FloatField()
    recommended_fertilizer = models.CharField(max_length=100)
    confidence = models.FloatField(default=0.0)
    result_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.recommended_fertilizer} for {self.crop}"

    class Meta:
        db_table = 'fertilizer_recommendations'
        ordering = ['-created_at']


class IrrigationRecommendation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='irrigation_recommendations'
    )
    crop = models.CharField(max_length=100)
    soil_type = models.CharField(max_length=50)
    temperature = models.FloatField()
    humidity = models.FloatField()
    rainfall = models.FloatField()
    water_requirement = models.CharField(max_length=200)
    confidence = models.FloatField(default=0.0)
    result_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.crop} irrigation"

    class Meta:
        db_table = 'irrigation_recommendations'
        ordering = ['-created_at']


class MarketPrice(models.Model):
    """
    Cache table for market prices from data.gov.in.
    Always written to on successful API calls.
    Read from when API is unavailable.
    """
    commodity = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True, default='')
    market = models.CharField(max_length=200)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, default='')
    min_price = models.FloatField(default=0.0)
    max_price = models.FloatField(default=0.0)
    modal_price = models.FloatField(default=0.0)
    price_date = models.DateField()
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.commodity} — {self.market} — ₹{self.modal_price}"

    class Meta:
        db_table = 'market_prices'
        ordering = ['-price_date', '-fetched_at']
        indexes = [
            models.Index(fields=['commodity']),
            models.Index(fields=['state']),
            models.Index(fields=['price_date']),
        ]
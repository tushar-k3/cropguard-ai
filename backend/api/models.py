from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
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
    """
    Stores each plant scan with its full result.
    JSONField is PostgreSQL-compatible via Django ORM.
    SQLite supports JSONField from Django 3.1+.
    """

    SOURCE_CHOICES = [
        ('kindwise', 'Kindwise API'),
        ('local_model', 'Local MobileNetV2 Model'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    image = models.ImageField(upload_to='scans/%Y/%m/', blank=True, null=True)
    plant_name = models.CharField(max_length=200, blank=True, default='')
    is_healthy = models.BooleanField(default=True)
    is_plant = models.BooleanField(default=True)
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='kindwise'
    )

    # Confidence score as percentage (0-100)
    confidence = models.FloatField(default=0.0)

    # Full result stored as JSON — avoids needing separate Disease tables for MVP
    # Diseases list, treatment suggestions, warnings all go here
    result_data = models.JSONField(default=dict)

    # True if the plant is outside the PlantVillage fallback dataset
    unsupported_crop = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.plant_name} ({self.source})"

    class Meta:
        db_table = 'scan_results'
        ordering = ['-created_at']
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django's built-in User model with farming-specific fields.
    Uses a OneToOneField so every User has exactly one UserProfile.
    We never touch Django's User model directly — ORM only, no raw SQL.
    """
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
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.
    Creates both a User and a UserProfile in one transaction.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField(required=False, allow_blank=True, default='')
    preferred_language = serializers.ChoiceField(
        choices=['en', 'hi', 'mr'],
        default='en',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password2',
            'phone', 'location', 'preferred_language'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        return attrs

    def create(self, validated_data):
        # Extract profile fields before creating the User
        phone = validated_data.pop('phone', '')
        location = validated_data.pop('location', '')
        preferred_language = validated_data.pop('preferred_language', 'en')
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )

        UserProfile.objects.create(
            user=user,
            phone=phone,
            location=location,
            preferred_language=preferred_language,
        )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT login serializer to include
    basic user info in the token response, so the frontend
    doesn't need a separate /me/ call immediately after login.
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user info to the login response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        # Add profile info if it exists
        try:
            profile = self.user.profile
            data['user']['phone'] = profile.phone
            data['user']['location'] = profile.location
            data['user']['preferred_language'] = profile.preferred_language
        except UserProfile.DoesNotExist:
            data['user']['preferred_language'] = 'en'

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Used for the /profile/ endpoint — read and update profile data.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'location', 'farm_size', 'preferred_language',
            'created_at',
        ]
        read_only_fields = ['username', 'email', 'created_at']

    def update(self, instance, validated_data):
        # Handle nested user fields
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
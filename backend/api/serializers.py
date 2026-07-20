from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    UserProfile,
    ScanResult,
    CropRecommendation,
    FertilizerRecommendation,
    IrrigationRecommendation,
    MarketPrice,
)


# ============================================================
# USER REGISTRATION
# ============================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )
    location = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
    )
    preferred_language = serializers.ChoiceField(
        choices=['en', 'hi', 'mr'],
        default='en',
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password2',
            'phone',
            'location',
            'preferred_language',
        ]

        extra_kwargs = {
            'email': {
                'required': True,
            },
            'first_name': {
                'required': True,
            },
            'last_name': {
                'required': False,
                'allow_blank': True,
            },
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                'email': 'A user with this email already exists.'
            })

        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        location = validated_data.pop('location', '')
        preferred_language = validated_data.pop(
            'preferred_language',
            'en'
        )

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


# ============================================================
# CUSTOM JWT LOGIN
# ============================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # User information returned with JWT tokens
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,

            # Required by frontend AdminPage
            'is_staff': self.user.is_staff,
        }

        try:
            profile = self.user.profile

            data['user']['phone'] = profile.phone
            data['user']['location'] = profile.location
            data['user']['preferred_language'] = (
                profile.preferred_language
            )

        except UserProfile.DoesNotExist:
            data['user']['phone'] = ''
            data['user']['location'] = ''
            data['user']['preferred_language'] = 'en'

        return data


# ============================================================
# USER PROFILE
# ============================================================

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )

    email = serializers.CharField(
        source='user.email',
        read_only=True,
    )

    first_name = serializers.CharField(
        source='user.first_name',
    )

    last_name = serializers.CharField(
        source='user.last_name',
    )

    class Meta:
        model = UserProfile

        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'location',
            'farm_size',
            'preferred_language',
            'created_at',
        ]

        read_only_fields = [
            'username',
            'email',
            'created_at',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']

        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']

        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


# ============================================================
# PLANT SCAN RESULT
# ============================================================

class ScanResultSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ScanResult

        fields = [
            'id',
            'plant_name',
            'is_healthy',
            'is_plant',
            'source',
            'confidence',
            'result_data',
            'unsupported_crop',
            'image_url',
            'created_at',
        ]

        read_only_fields = fields

    def get_image_url(self, obj):
        request = self.context.get('request')

        if obj.image and request:
            return request.build_absolute_uri(
                obj.image.url
            )

        return None


# ============================================================
# CROP RECOMMENDATION
# ============================================================

class CropRecommendationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CropRecommendation

        fields = [
            'id',
            'nitrogen',
            'phosphorus',
            'potassium',
            'temperature',
            'humidity',
            'ph',
            'rainfall',
            'recommended_crop',
            'confidence',
            'result_data',
            'created_at',
        ]

        read_only_fields = fields


class CropInputSerializer(serializers.Serializer):
    N = serializers.FloatField(
        min_value=0,
        max_value=300,
    )

    P = serializers.FloatField(
        min_value=0,
        max_value=300,
    )

    K = serializers.FloatField(
        min_value=0,
        max_value=300,
    )

    temperature = serializers.FloatField(
        min_value=0,
        max_value=50,
    )

    humidity = serializers.FloatField(
        min_value=0,
        max_value=100,
    )

    ph = serializers.FloatField(
        min_value=0,
        max_value=14,
    )

    rainfall = serializers.FloatField(
        min_value=0,
        max_value=500,
    )


# ============================================================
# FERTILIZER RECOMMENDATION
# ============================================================

class FertilizerRecommendationSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = FertilizerRecommendation

        fields = [
            'id',
            'crop',
            'nitrogen',
            'phosphorus',
            'potassium',
            'recommended_fertilizer',
            'confidence',
            'result_data',
            'created_at',
        ]

        read_only_fields = fields


class FertilizerInputSerializer(serializers.Serializer):
    crop = serializers.CharField(
        max_length=100,
    )

    N = serializers.FloatField(
        min_value=0,
        max_value=300,
    )

    P = serializers.FloatField(
        min_value=0,
        max_value=300,
    )

    K = serializers.FloatField(
        min_value=0,
        max_value=300,
    )


# ============================================================
# IRRIGATION RECOMMENDATION
# ============================================================

class IrrigationRecommendationSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = IrrigationRecommendation

        fields = [
            'id',
            'crop',
            'soil_type',
            'temperature',
            'humidity',
            'rainfall',
            'water_requirement',
            'confidence',
            'result_data',
            'created_at',
        ]

        read_only_fields = fields


class IrrigationInputSerializer(serializers.Serializer):

    crop = serializers.CharField(
        max_length=100,
    )

    soil_type = serializers.ChoiceField(
        choices=[
            'sandy',
            'loamy',
            'clay',
            'silt',
            'black',
            'red',
            'alluvial',
        ]
    )

    temperature = serializers.FloatField(
        min_value=0,
        max_value=50,
    )

    humidity = serializers.FloatField(
        min_value=0,
        max_value=100,
    )

    rainfall = serializers.FloatField(
        min_value=0,
        max_value=500,
    )


# ============================================================
# MARKET PRICE
# ============================================================

class MarketPriceSerializer(serializers.ModelSerializer):

    class Meta:
        model = MarketPrice

        fields = [
            'id',
            'commodity',
            'variety',
            'market',
            'state',
            'district',
            'min_price',
            'max_price',
            'modal_price',
            'price_date',
            'fetched_at',
        ]

        read_only_fields = fields
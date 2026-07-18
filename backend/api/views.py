import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.conf import settings

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ScanResultSerializer,
    CropRecommendationSerializer,
    CropInputSerializer,
    FertilizerRecommendationSerializer,
    FertilizerInputSerializer,
)
from .models import ScanResult, CropRecommendation, FertilizerRecommendation
from .ml.kindwise import call_kindwise
from .ml.fallback import run_fallback
from .ml.crop_model import predict_crop
from .ml.fertilizer_model import predict_fertilizer

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    db_engine = settings.DATABASES['default']['ENGINE']
    if 'sqlite' in db_engine:
        db_label = 'SQLite (development)'
    elif 'postgresql' in db_engine:
        db_label = 'PostgreSQL (production)'
    else:
        db_label = db_engine
    return Response({
        'status': 'ok',
        'message': 'CropGuard AI API is running',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'database': db_label,
        'debug_mode': settings.DEBUG,
    })


# ─────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'Account created successfully.',
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'preferred_language': user.profile.preferred_language,
        }
    }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        user_profile = request.user.profile
    except Exception:
        return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        return Response(UserProfileSerializer(user_profile).data)
    serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# Plant Scanner
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def scan_plant(request):
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if image_file.content_type not in allowed_types:
        return Response(
            {'error': 'Invalid file type. Please upload JPEG, PNG, or WebP.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if image_file.size > 10 * 1024 * 1024:
        return Response(
            {'error': 'Image too large. Maximum 10MB.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    kindwise_result = call_kindwise(image_file)
    if kindwise_result['success']:
        result = kindwise_result
    else:
        logger.warning(f"Kindwise failed: {kindwise_result.get('error')}. Using fallback.")
        fallback_result = run_fallback(image_file)
        if fallback_result['success']:
            result = fallback_result
        else:
            return Response({
                'error': 'Both the AI service and offline model are unavailable.',
                'kindwise_error': kindwise_result.get('error'),
                'fallback_error': fallback_result.get('error'),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        scan = ScanResult.objects.create(
            user=request.user,
            image=image_file,
            plant_name=result.get('plant_name', ''),
            is_healthy=result.get('is_healthy', True),
            is_plant=result.get('is_plant', True),
            source=result.get('source', 'kindwise'),
            confidence=result.get('plant_probability', 0.0),
            result_data=result,
            unsupported_crop=result.get('unsupported_crop', False),
        )
        result['scan_id'] = scan.id
    except Exception as e:
        logger.error(f"Failed to save scan: {e}")
        result['scan_id'] = None

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_history(request):
    scans = ScanResult.objects.filter(user=request.user)[:20]
    serializer = ScanResultSerializer(scans, many=True, context={'request': request})
    return Response({'count': scans.count(), 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_detail(request, scan_id):
    try:
        scan = ScanResult.objects.get(id=scan_id, user=request.user)
    except ScanResult.DoesNotExist:
        return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(ScanResultSerializer(scan, context={'request': request}).data)


# ─────────────────────────────────────────────
# Crop Recommendation
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_crop(request):
    serializer = CropInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    d = serializer.validated_data
    result = predict_crop(
        N=d['N'], P=d['P'], K=d['K'],
        temperature=d['temperature'],
        humidity=d['humidity'],
        ph=d['ph'],
        rainfall=d['rainfall'],
    )
    if not result['success']:
        return Response(
            {'error': result.get('error', 'Prediction failed.')},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    try:
        CropRecommendation.objects.create(
            user=request.user,
            nitrogen=d['N'], phosphorus=d['P'], potassium=d['K'],
            temperature=d['temperature'], humidity=d['humidity'],
            ph=d['ph'], rainfall=d['rainfall'],
            recommended_crop=result['crop'],
            confidence=result['confidence'],
            result_data=result,
        )
    except Exception as e:
        logger.error(f"Failed to save crop recommendation: {e}")
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_history(request):
    recs = CropRecommendation.objects.filter(user=request.user)[:20]
    return Response({
        'count': recs.count(),
        'results': CropRecommendationSerializer(recs, many=True).data,
    })


# ─────────────────────────────────────────────
# Fertilizer Recommendation
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_fertilizer(request):
    """
    Accepts crop name and soil NPK values.
    Returns best fertilizer with application guidance.
    """
    serializer = FertilizerInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    d = serializer.validated_data
    result = predict_fertilizer(
        N=d['N'], P=d['P'], K=d['K'],
        crop=d['crop'],
    )

    if not result['success']:
        return Response(
            {'error': result.get('error', 'Prediction failed.')},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    try:
        FertilizerRecommendation.objects.create(
            user=request.user,
            crop=d['crop'],
            nitrogen=d['N'],
            phosphorus=d['P'],
            potassium=d['K'],
            recommended_fertilizer=result['fertilizer'],
            confidence=result['confidence'],
            result_data=result,
        )
    except Exception as e:
        logger.error(f"Failed to save fertilizer recommendation: {e}")

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fertilizer_history(request):
    """Returns the user's last 20 fertilizer recommendations."""
    recs = FertilizerRecommendation.objects.filter(user=request.user)[:20]
    return Response({
        'count': recs.count(),
        'results': FertilizerRecommendationSerializer(recs, many=True).data,
    })
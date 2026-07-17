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
)
from .models import ScanResult
from .ml.kindwise import call_kindwise
from .ml.fallback import run_fallback

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
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        user_profile = request.user.profile
    except Exception:
        return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    if request.method == 'PATCH':
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
    """
    Accepts an uploaded image and returns plant identification
    and disease detection results.

    Detection flow:
    1. Try Kindwise API (primary)
    2. If Kindwise fails/limit exceeded → use MobileNetV2 fallback
    3. Save result to database
    4. Return result with source clearly labeled
    """
    image_file = request.FILES.get('image')

    if not image_file:
        return Response(
            {'error': 'No image provided. Please upload an image.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if image_file.content_type not in allowed_types:
        return Response(
            {'error': 'Invalid file type. Please upload a JPEG, PNG, or WebP image.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file size — 10MB max
    if image_file.size > 10 * 1024 * 1024:
        return Response(
            {'error': 'Image is too large. Maximum size is 10MB.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = None
    used_fallback = False

    # ── Step 1: Try Kindwise ──
    logger.info(f"Scan request from user {request.user.username}")
    kindwise_result = call_kindwise(image_file)

    if kindwise_result['success']:
        result = kindwise_result
        logger.info("Kindwise scan successful.")
    else:
        # ── Step 2: Fall back to local model ──
        logger.warning(
            f"Kindwise failed ({kindwise_result.get('error')}). "
            "Switching to MobileNetV2 fallback."
        )
        used_fallback = True
        fallback_result = run_fallback(image_file)

        if fallback_result['success']:
            result = fallback_result
            logger.info("Fallback model scan successful.")
        else:
            # Both failed
            return Response({
                'error': (
                    'Both the AI service and offline model are unavailable. '
                    'Please check your internet connection and try again.'
                ),
                'kindwise_error': kindwise_result.get('error'),
                'fallback_error': fallback_result.get('error'),
                'fallback_model_available': fallback_result.get('model_available', False),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # ── Step 3: Save to database ──
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
        logger.error(f"Failed to save scan result: {e}")
        # Don't fail the request — return result even if save fails
        result['scan_id'] = None

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_history(request):
    """
    Returns the authenticated user's scan history, newest first.
    Limited to 20 most recent scans for performance.
    """
    scans = ScanResult.objects.filter(user=request.user)[:20]
    serializer = ScanResultSerializer(scans, many=True, context={'request': request})
    return Response({
        'count': scans.count(),
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_detail(request, scan_id):
    """
    Returns a single scan result by ID.
    Users can only access their own scans.
    """
    try:
        scan = ScanResult.objects.get(id=scan_id, user=request.user)
    except ScanResult.DoesNotExist:
        return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ScanResultSerializer(scan, context={'request': request})
    return Response(serializer.data)
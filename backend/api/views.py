from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
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
)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Public endpoint — no authentication required.
    Confirms backend is running and reports the active database.
    """
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
# Registration
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Creates a new user account and returns JWT tokens immediately
    so the user is logged in right after registration.
    """
    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    # Issue tokens immediately so the user is logged in after registration
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


# ─────────────────────────────────────────────
# Login — Custom JWT view with user info
# ─────────────────────────────────────────────
class LoginView(TokenObtainPairView):
    """
    Returns access + refresh tokens plus user info in one response.
    Inherits all SimpleJWT validation logic.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


# ─────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Blacklisting is not enabled (kept simple for MVP).
    The frontend is responsible for deleting the token from localStorage.
    This endpoint exists so future blacklisting can be added here
    without changing the frontend API call.
    """
    return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Profile — Read and Update
# ─────────────────────────────────────────────
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET  — Returns the authenticated user's profile.
    PATCH — Partially updates the profile (only sent fields are changed).
    """
    try:
        user_profile = request.user.profile
    except Exception:
        return Response(
            {'error': 'Profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = UserProfileSerializer(
            user_profile,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
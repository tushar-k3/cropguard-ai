import logging

from django.conf import settings
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)

from .models import (
    ScanResult, CropRecommendation,
    FertilizerRecommendation, IrrigationRecommendation,
    MarketPrice,
)

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ScanResultSerializer,
    CropRecommendationSerializer,
    CropInputSerializer,
    FertilizerRecommendationSerializer,
    FertilizerInputSerializer,
    IrrigationRecommendationSerializer,
    IrrigationInputSerializer,
)

from .models import (
    ScanResult,
    CropRecommendation,
    FertilizerRecommendation,
    IrrigationRecommendation,
)

from .ml.kindwise import call_kindwise
from .ml.fallback import run_fallback
from .ml.crop_model import predict_crop
from .ml.fertilizer_model import predict_fertilizer
from .ml.irrigation_model import predict_irrigation

# Weather
from .weather import (
    fetch_weather_for_city,
    fetch_weather_for_coordinates,
)

# Chatbot
from .chatbot import (
    chat_with_groq,
    get_suggested_questions,
)


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
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = serializer.save()
    refresh = RefreshToken.for_user(user)

    return Response(
        {
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
            },
        },
        status=status.HTTP_201_CREATED,
    )


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    return Response({
        'message': 'Logged out successfully.'
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        user_profile = request.user.profile

    except Exception:
        return Response(
            {
                'error': 'Profile not found.'
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(
            UserProfileSerializer(
                user_profile
            ).data
        )

    serializer = UserProfileSerializer(
        user_profile,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )


# ─────────────────────────────────────────────
# Plant Scanner
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([
    MultiPartParser,
    FormParser,
])
def scan_plant(request):
    image_file = request.FILES.get('image')

    if not image_file:
        return Response(
            {
                'error': 'No image provided.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    allowed_types = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
    ]

    if image_file.content_type not in allowed_types:
        return Response(
            {
                'error':
                    'Invalid file type. '
                    'Please upload JPEG, PNG, or WebP.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if image_file.size > 10 * 1024 * 1024:
        return Response(
            {
                'error':
                    'Image too large. '
                    'Maximum 10MB.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    kindwise_result = call_kindwise(
        image_file
    )

    if kindwise_result['success']:
        result = kindwise_result

    else:
        logger.warning(
            f"Kindwise failed: "
            f"{kindwise_result.get('error')}. "
            f"Using fallback."
        )

        fallback_result = run_fallback(
            image_file
        )

        if fallback_result['success']:
            result = fallback_result

        else:
            return Response(
                {
                    'error':
                        'Both the AI service '
                        'and offline model '
                        'are unavailable.',

                    'kindwise_error':
                        kindwise_result.get(
                            'error'
                        ),

                    'fallback_error':
                        fallback_result.get(
                            'error'
                        ),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    try:
        scan = ScanResult.objects.create(
            user=request.user,
            image=image_file,

            plant_name=result.get(
                'plant_name',
                '',
            ),

            is_healthy=result.get(
                'is_healthy',
                True,
            ),

            is_plant=result.get(
                'is_plant',
                True,
            ),

            source=result.get(
                'source',
                'kindwise',
            ),

            confidence=result.get(
                'plant_probability',
                0.0,
            ),

            result_data=result,

            unsupported_crop=result.get(
                'unsupported_crop',
                False,
            ),
        )

        result['scan_id'] = scan.id

    except Exception as e:
        logger.error(
            f"Failed to save scan: {e}"
        )

        result['scan_id'] = None

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_history(request):
    scans = (
        ScanResult.objects
        .filter(user=request.user)[:20]
    )

    serializer = ScanResultSerializer(
        scans,
        many=True,
        context={
            'request': request
        },
    )

    return Response({
        'count': scans.count(),
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_detail(request, scan_id):
    try:
        scan = ScanResult.objects.get(
            id=scan_id,
            user=request.user,
        )

    except ScanResult.DoesNotExist:
        return Response(
            {
                'error': 'Scan not found.'
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        ScanResultSerializer(
            scan,
            context={
                'request': request
            },
        ).data
    )


# ─────────────────────────────────────────────
# Crop Recommendation
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_crop(request):
    serializer = CropInputSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    d = serializer.validated_data

    result = predict_crop(
        N=d['N'],
        P=d['P'],
        K=d['K'],
        temperature=d['temperature'],
        humidity=d['humidity'],
        ph=d['ph'],
        rainfall=d['rainfall'],
    )

    if not result['success']:
        return Response(
            {
                'error': result.get(
                    'error',
                    'Prediction failed.',
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        CropRecommendation.objects.create(
            user=request.user,
            nitrogen=d['N'],
            phosphorus=d['P'],
            potassium=d['K'],
            temperature=d['temperature'],
            humidity=d['humidity'],
            ph=d['ph'],
            rainfall=d['rainfall'],
            recommended_crop=result['crop'],
            confidence=result['confidence'],
            result_data=result,
        )

    except Exception as e:
        logger.error(
            f"Failed to save "
            f"crop recommendation: {e}"
        )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_history(request):
    recs = (
        CropRecommendation.objects
        .filter(user=request.user)[:20]
    )

    return Response({
        'count': recs.count(),

        'results':
            CropRecommendationSerializer(
                recs,
                many=True,
            ).data,
    })


# ─────────────────────────────────────────────
# Fertilizer Recommendation
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_fertilizer(request):
    serializer = FertilizerInputSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    d = serializer.validated_data

    result = predict_fertilizer(
        N=d['N'],
        P=d['P'],
        K=d['K'],
        crop=d['crop'],
    )

    if not result['success']:
        return Response(
            {
                'error': result.get(
                    'error',
                    'Prediction failed.',
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
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
        logger.error(
            f"Failed to save "
            f"fertilizer recommendation: {e}"
        )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fertilizer_history(request):
    recs = (
        FertilizerRecommendation.objects
        .filter(user=request.user)[:20]
    )

    return Response({
        'count': recs.count(),

        'results':
            FertilizerRecommendationSerializer(
                recs,
                many=True,
            ).data,
    })


# ─────────────────────────────────────────────
# Irrigation Recommendation
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_irrigation(request):
    serializer = IrrigationInputSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    d = serializer.validated_data

    result = predict_irrigation(
        crop=d['crop'],
        soil_type=d['soil_type'],
        temperature=d['temperature'],
        humidity=d['humidity'],
        rainfall=d['rainfall'],
    )

    if not result['success']:
        return Response(
            {
                'error': result.get(
                    'error',
                    'Prediction failed.',
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:
        IrrigationRecommendation.objects.create(
            user=request.user,
            crop=d['crop'],
            soil_type=d['soil_type'],
            temperature=d['temperature'],
            humidity=d['humidity'],
            rainfall=d['rainfall'],
            water_requirement=result['label'],
            confidence=result['confidence'],
            result_data=result,
        )

    except Exception as e:
        logger.error(
            f"Failed to save "
            f"irrigation recommendation: {e}"
        )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def irrigation_history(request):
    recs = (
        IrrigationRecommendation.objects
        .filter(user=request.user)[:20]
    )

    return Response({
        'count': recs.count(),

        'results':
            IrrigationRecommendationSerializer(
                recs,
                many=True,
            ).data,
    })


# ─────────────────────────────────────────────
# Weather
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weather(request):
    """
    Get weather using either:

    City:
    GET /api/weather/?city=Nashik

    Current GPS coordinates:
    GET /api/weather/?lat=19.99&lon=73.79
    """

    lat = request.query_params.get(
        'lat'
    )

    lon = request.query_params.get(
        'lon'
    )

    city = request.query_params.get(
        'city',
        '',
    ).strip()

    # Current GPS location
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)

        except ValueError:
            return Response(
                {
                    'error':
                        'Invalid coordinates.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data, error = fetch_weather_for_coordinates(
            lat,
            lon,
        )

        if data is None:
            return Response(
                {
                    'error':
                        error
                        or
                        'Could not fetch weather data.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(data)

    # Search by city
    elif city:
        data, error = fetch_weather_for_city(
            city
        )

        if data is None:
            return Response(
                {
                    'error':
                        error
                        or
                        'Could not fetch weather data.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(data)

    # No location provided
    else:
        return Response(
            {
                'error':
                    'Provide either a city name '
                    '(?city=) or coordinates '
                    '(?lat=&lon=).'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# ─────────────────────────────────────────────
# AI Chatbot
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chatbot(request):
    """
    POST /api/chatbot/

    Example body:

    {
        "messages": [
            {
                "role": "user",
                "content": "What fertilizer should I use for wheat?"
            }
        ],
        "language": "en"
    }

    Languages:
    en = English
    hi = Hindi
    mr = Marathi
    """

    messages = request.data.get(
        'messages',
        []
    )

    language = request.data.get(
        'language',
        'en',
    )

    if not messages:
        return Response(
            {
                'error':
                    'No messages provided.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(messages, list):
        return Response(
            {
                'error':
                    'Messages must be a list.'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if language not in [
        'en',
        'hi',
        'mr',
    ]:
        language = 'en'

    # Keep last 20 messages only
    messages = messages[-20:]

    result = chat_with_groq(
        messages,
        language=language,
    )

    if not result.get('success'):
        return Response(
            {
                'error': result.get(
                    'error',
                    'Chatbot unavailable.',
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response({
        'message':
            result['message'],

        'model':
            result.get(
                'model',
                'unknown',
            ),

        'tokens_used':
            result.get(
                'tokens_used',
                0,
            ),
    })


# ─────────────────────────────────────────────
# Chatbot Suggestions
# ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chatbot_suggestions(request):
    """
    GET /api/chatbot/suggestions/?lang=en
    """

    language = request.query_params.get(
        'lang',
        'en',
    )

    if language not in [
        'en',
        'hi',
        'mr',
    ]:
        language = 'en'

    suggestions = get_suggested_questions(
        language
    )

    return Response({
        'suggestions': suggestions
    })
# ─────────────────────────────────────────────
# Market Prices
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_prices(request):
    """
    GET /api/market/?commodity=Tomato&state=Maharashtra&limit=50
    Returns live prices from data.gov.in or cached prices as fallback.
    """
    from .market import get_market_prices, seed_sample_prices

    commodity = request.query_params.get('commodity', '').strip() or None
    state     = request.query_params.get('state', '').strip() or None
    limit     = int(request.query_params.get('limit', 50))

    # Seed sample data on first run so page is never empty
    seed_sample_prices()

    result = get_market_prices(
        commodity=commodity,
        state=state,
        limit=limit,
    )

    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def market_commodities(request):
    """Returns list of unique commodities in the cache for the search dropdown."""
    from .models import MarketPrice
    from .market import seed_sample_prices

    seed_sample_prices()

    commodities = (
        MarketPrice.objects
        .values_list('commodity', flat=True)
        .distinct()
        .order_by('commodity')
    )
    return Response({'commodities': list(commodities)})
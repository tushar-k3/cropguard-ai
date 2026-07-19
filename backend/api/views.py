# import logging
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes, parser_classes
# from rest_framework.parsers import MultiPartParser, FormParser
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.utils import timezone
# from django.conf import settings

# from .serializers import (
#     RegisterSerializer,
#     CustomTokenObtainPairSerializer,
#     UserProfileSerializer,
#     ScanResultSerializer,
#     CropRecommendationSerializer,
#     CropInputSerializer,
#     FertilizerRecommendationSerializer,
#     FertilizerInputSerializer,
#     IrrigationRecommendationSerializer,
#     IrrigationInputSerializer,
# )
# from .models import (
#     ScanResult, CropRecommendation,
#     FertilizerRecommendation, IrrigationRecommendation
# )
# from .ml.kindwise import call_kindwise
# from .ml.fallback import run_fallback
# from .ml.crop_model import predict_crop
# from .ml.fertilizer_model import predict_fertilizer
# from .ml.irrigation_model import predict_irrigation
# from .weather import (
#     fetch_weather_for_city,
#     get_weather,
#     get_weather_description,
#     generate_farming_advice,
# )

# logger = logging.getLogger(__name__)


# # ─────────────────────────────────────────────
# # Health Check
# # ─────────────────────────────────────────────
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def health_check(request):
#     db_engine = settings.DATABASES['default']['ENGINE']
#     if 'sqlite' in db_engine:
#         db_label = 'SQLite (development)'
#     elif 'postgresql' in db_engine:
#         db_label = 'PostgreSQL (production)'
#     else:
#         db_label = db_engine
#     return Response({
#         'status': 'ok',
#         'message': 'CropGuard AI API is running',
#         'timestamp': timezone.now().isoformat(),
#         'version': '1.0.0',
#         'database': db_label,
#         'debug_mode': settings.DEBUG,
#     })


# # ─────────────────────────────────────────────
# # Authentication
# # ─────────────────────────────────────────────
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def register(request):
#     serializer = RegisterSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     user = serializer.save()
#     refresh = RefreshToken.for_user(user)
#     return Response({
#         'message': 'Account created successfully.',
#         'access': str(refresh.access_token),
#         'refresh': str(refresh),
#         'user': {
#             'id': user.id,
#             'username': user.username,
#             'email': user.email,
#             'first_name': user.first_name,
#             'last_name': user.last_name,
#             'preferred_language': user.profile.preferred_language,
#         }
#     }, status=status.HTTP_201_CREATED)


# class LoginView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer
#     permission_classes = [AllowAny]


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def logout(request):
#     return Response({'message': 'Logged out successfully.'})


# @api_view(['GET', 'PATCH'])
# @permission_classes([IsAuthenticated])
# def profile(request):
#     try:
#         user_profile = request.user.profile
#     except Exception:
#         return Response(
#             {'error': 'Profile not found.'},
#             status=status.HTTP_404_NOT_FOUND
#         )
#     if request.method == 'GET':
#         return Response(UserProfileSerializer(user_profile).data)
#     serializer = UserProfileSerializer(
#         user_profile, data=request.data, partial=True
#     )
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# # ─────────────────────────────────────────────
# # Plant Scanner
# # ─────────────────────────────────────────────
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])
# def scan_plant(request):
#     image_file = request.FILES.get('image')
#     if not image_file:
#         return Response(
#             {'error': 'No image provided.'},
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
#     if image_file.content_type not in allowed_types:
#         return Response(
#             {'error': 'Invalid file type. Please upload JPEG, PNG, or WebP.'},
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     if image_file.size > 10 * 1024 * 1024:
#         return Response(
#             {'error': 'Image too large. Maximum 10MB.'},
#             status=status.HTTP_400_BAD_REQUEST
#         )
#     kindwise_result = call_kindwise(image_file)
#     if kindwise_result['success']:
#         result = kindwise_result
#     else:
#         logger.warning(
#             f"Kindwise failed: {kindwise_result.get('error')}. Using fallback."
#         )
#         fallback_result = run_fallback(image_file)
#         if fallback_result['success']:
#             result = fallback_result
#         else:
#             return Response({
#                 'error': 'Both the AI service and offline model are unavailable.',
#                 'kindwise_error': kindwise_result.get('error'),
#                 'fallback_error': fallback_result.get('error'),
#             }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
#     try:
#         scan = ScanResult.objects.create(
#             user=request.user,
#             image=image_file,
#             plant_name=result.get('plant_name', ''),
#             is_healthy=result.get('is_healthy', True),
#             is_plant=result.get('is_plant', True),
#             source=result.get('source', 'kindwise'),
#             confidence=result.get('plant_probability', 0.0),
#             result_data=result,
#             unsupported_crop=result.get('unsupported_crop', False),
#         )
#         result['scan_id'] = scan.id
#     except Exception as e:
#         logger.error(f"Failed to save scan: {e}")
#         result['scan_id'] = None
#     return Response(result)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def scan_history(request):
#     scans = ScanResult.objects.filter(user=request.user)[:20]
#     serializer = ScanResultSerializer(
#         scans, many=True, context={'request': request}
#     )
#     return Response({'count': scans.count(), 'results': serializer.data})


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def scan_detail(request, scan_id):
#     try:
#         scan = ScanResult.objects.get(id=scan_id, user=request.user)
#     except ScanResult.DoesNotExist:
#         return Response(
#             {'error': 'Scan not found.'},
#             status=status.HTTP_404_NOT_FOUND
#         )
#     return Response(
#         ScanResultSerializer(scan, context={'request': request}).data
#     )


# # ─────────────────────────────────────────────
# # Crop Recommendation
# # ─────────────────────────────────────────────
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def recommend_crop(request):
#     serializer = CropInputSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     d = serializer.validated_data
#     result = predict_crop(
#         N=d['N'], P=d['P'], K=d['K'],
#         temperature=d['temperature'],
#         humidity=d['humidity'],
#         ph=d['ph'],
#         rainfall=d['rainfall'],
#     )
#     if not result['success']:
#         return Response(
#             {'error': result.get('error', 'Prediction failed.')},
#             status=status.HTTP_503_SERVICE_UNAVAILABLE
#         )
#     try:
#         CropRecommendation.objects.create(
#             user=request.user,
#             nitrogen=d['N'], phosphorus=d['P'], potassium=d['K'],
#             temperature=d['temperature'], humidity=d['humidity'],
#             ph=d['ph'], rainfall=d['rainfall'],
#             recommended_crop=result['crop'],
#             confidence=result['confidence'],
#             result_data=result,
#         )
#     except Exception as e:
#         logger.error(f"Failed to save crop recommendation: {e}")
#     return Response(result)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def crop_history(request):
#     recs = CropRecommendation.objects.filter(user=request.user)[:20]
#     return Response({
#         'count': recs.count(),
#         'results': CropRecommendationSerializer(recs, many=True).data,
#     })


# # ─────────────────────────────────────────────
# # Fertilizer Recommendation
# # ─────────────────────────────────────────────
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def recommend_fertilizer(request):
#     serializer = FertilizerInputSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     d = serializer.validated_data
#     result = predict_fertilizer(
#         N=d['N'], P=d['P'], K=d['K'], crop=d['crop'],
#     )
#     if not result['success']:
#         return Response(
#             {'error': result.get('error', 'Prediction failed.')},
#             status=status.HTTP_503_SERVICE_UNAVAILABLE
#         )
#     try:
#         FertilizerRecommendation.objects.create(
#             user=request.user,
#             crop=d['crop'],
#             nitrogen=d['N'], phosphorus=d['P'], potassium=d['K'],
#             recommended_fertilizer=result['fertilizer'],
#             confidence=result['confidence'],
#             result_data=result,
#         )
#     except Exception as e:
#         logger.error(f"Failed to save fertilizer recommendation: {e}")
#     return Response(result)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def fertilizer_history(request):
#     recs = FertilizerRecommendation.objects.filter(user=request.user)[:20]
#     return Response({
#         'count': recs.count(),
#         'results': FertilizerRecommendationSerializer(recs, many=True).data,
#     })


# # ─────────────────────────────────────────────
# # Irrigation Recommendation
# # ─────────────────────────────────────────────
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def recommend_irrigation(request):
#     serializer = IrrigationInputSerializer(data=request.data)
#     if not serializer.is_valid():
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#     d = serializer.validated_data
#     result = predict_irrigation(
#         crop=d['crop'],
#         soil_type=d['soil_type'],
#         temperature=d['temperature'],
#         humidity=d['humidity'],
#         rainfall=d['rainfall'],
#     )
#     if not result['success']:
#         return Response(
#             {'error': result.get('error', 'Prediction failed.')},
#             status=status.HTTP_503_SERVICE_UNAVAILABLE
#         )
#     try:
#         IrrigationRecommendation.objects.create(
#             user=request.user,
#             crop=d['crop'],
#             soil_type=d['soil_type'],
#             temperature=d['temperature'],
#             humidity=d['humidity'],
#             rainfall=d['rainfall'],
#             water_requirement=result['label'],
#             confidence=result['confidence'],
#             result_data=result,
#         )
#     except Exception as e:
#         logger.error(f"Failed to save irrigation recommendation: {e}")
#     return Response(result)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def irrigation_history(request):
#     recs = IrrigationRecommendation.objects.filter(user=request.user)[:20]
#     return Response({
#         'count': recs.count(),
#         'results': IrrigationRecommendationSerializer(recs, many=True).data,
#     })


# # ─────────────────────────────────────────────
# # Weather
# # ─────────────────────────────────────────────
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def weather(request):
#     """
#     GET /api/weather/?city=Nashik
#     GET /api/weather/?lat=19.99&lon=73.79
#     """
#     lat = request.query_params.get('lat')
#     lon = request.query_params.get('lon')
#     city = request.query_params.get('city', '').strip()

#     if lat and lon:
#         try:
#             lat = float(lat)
#             lon = float(lon)
#         except ValueError:
#             return Response(
#                 {'error': 'Invalid coordinates.'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         weather_data, error = get_weather(lat, lon)
#         if weather_data is None:
#             return Response(
#                 {'error': error or 'Could not fetch weather data.'},
#                 status=status.HTTP_503_SERVICE_UNAVAILABLE
#             )

#         current = weather_data.get('current', {})
#         daily = weather_data.get('daily', {})
#         code = current.get('weather_code', 0)
#         description, icon = get_weather_description(code)

#         forecast = []
#         days = daily.get('time', [])
#         for i, day in enumerate(days):
#             day_code = daily.get('weather_code', [0] * 7)
#             day_desc, day_icon = get_weather_description(
#                 day_code[i] if i < len(day_code) else 0
#             )
#             forecast.append({
#                 'date': day,
#                 'temp_max': daily.get('temperature_2m_max', [])[i] if i < len(daily.get('temperature_2m_max', [])) else None,
#                 'temp_min': daily.get('temperature_2m_min', [])[i] if i < len(daily.get('temperature_2m_min', [])) else None,
#                 'precipitation': daily.get('precipitation_sum', [])[i] if i < len(daily.get('precipitation_sum', [])) else 0,
#                 'wind_max': daily.get('wind_speed_10m_max', [])[i] if i < len(daily.get('wind_speed_10m_max', [])) else 0,
#                 'description': day_desc,
#                 'icon': day_icon,
#             })

#         data = {
#             'city': 'Current Location',
#             'latitude': lat,
#             'longitude': lon,
#             'current': {
#                 'temperature': current.get('temperature_2m'),
#                 'feels_like': current.get('apparent_temperature'),
#                 'humidity': current.get('relative_humidity_2m'),
#                 'rain': current.get('rain', 0),
#                 'precipitation': current.get('precipitation', 0),
#                 'wind_speed': current.get('wind_speed_10m'),
#                 'wind_direction': current.get('wind_direction_10m'),
#                 'cloud_cover': current.get('cloud_cover'),
#                 'pressure': current.get('surface_pressure'),
#                 'description': description,
#                 'icon': icon,
#                 'weather_code': code,
#             },
#             'forecast': forecast,
#             'farming_advice': generate_farming_advice(weather_data),
#         }
#         return Response(data)

#     elif city:
#         data, error = fetch_weather_for_city(city)
#         if data is None:
#             return Response(
#                 {'error': error or 'Could not fetch weather data.'},
#                 status=status.HTTP_503_SERVICE_UNAVAILABLE
#             )
#         return Response(data)

#     else:
#         return Response(
#             {'error': 'Provide either a city name (?city=) or coordinates (?lat=&lon=).'},
#             status=status.HTTP_400_BAD_REQUEST
#         )

import logging

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
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

# Weather functions
from .weather import (
    fetch_weather_for_city,
    fetch_weather_for_coordinates,
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

    serializer = RegisterSerializer(
        data=request.data
    )

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

            'access': str(
                refresh.access_token
            ),

            'refresh': str(
                refresh
            ),

            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'preferred_language':
                    user.profile.preferred_language,
            },
        },

        status=status.HTTP_201_CREATED,
    )


class LoginView(TokenObtainPairView):

    serializer_class = (
        CustomTokenObtainPairSerializer
    )

    permission_classes = [
        AllowAny
    ]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):

    return Response({
        'message':
            'Logged out successfully.'
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):

    try:
        user_profile = (
            request.user.profile
        )

    except Exception:

        return Response(
            {
                'error':
                    'Profile not found.'
            },

            status=
                status.HTTP_404_NOT_FOUND,
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

        return Response(
            serializer.data
        )

    return Response(
        serializer.errors,

        status=
            status.HTTP_400_BAD_REQUEST,
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

    image_file = (
        request.FILES.get('image')
    )

    if not image_file:

        return Response(
            {
                'error':
                    'No image provided.'
            },

            status=
                status.HTTP_400_BAD_REQUEST,
        )

    allowed_types = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
    ]

    if (
        image_file.content_type
        not in allowed_types
    ):

        return Response(
            {
                'error':
                    'Invalid file type. '
                    'Please upload JPEG, PNG, or WebP.'
            },

            status=
                status.HTTP_400_BAD_REQUEST,
        )

    if (
        image_file.size
        > 10 * 1024 * 1024
    ):

        return Response(
            {
                'error':
                    'Image too large. '
                    'Maximum 10MB.'
            },

            status=
                status.HTTP_400_BAD_REQUEST,
        )

    kindwise_result = (
        call_kindwise(
            image_file
        )
    )

    if kindwise_result['success']:

        result = kindwise_result

    else:

        logger.warning(
            f"Kindwise failed: "
            f"{kindwise_result.get('error')}. "
            f"Using fallback."
        )

        fallback_result = (
            run_fallback(
                image_file
            )
        )

        if fallback_result['success']:

            result = (
                fallback_result
            )

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

                status=
                    status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    try:

        scan = (
            ScanResult.objects.create(
                user=request.user,

                image=image_file,

                plant_name=
                    result.get(
                        'plant_name',
                        '',
                    ),

                is_healthy=
                    result.get(
                        'is_healthy',
                        True,
                    ),

                is_plant=
                    result.get(
                        'is_plant',
                        True,
                    ),

                source=
                    result.get(
                        'source',
                        'kindwise',
                    ),

                confidence=
                    result.get(
                        'plant_probability',
                        0.0,
                    ),

                result_data=
                    result,

                unsupported_crop=
                    result.get(
                        'unsupported_crop',
                        False,
                    ),
            )
        )

        result['scan_id'] = (
            scan.id
        )

    except Exception as e:

        logger.error(
            f"Failed to save scan: {e}"
        )

        result['scan_id'] = None

    return Response(
        result
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_history(request):

    scans = (
        ScanResult.objects
        .filter(
            user=request.user
        )[:20]
    )

    serializer = (
        ScanResultSerializer(
            scans,
            many=True,
            context={
                'request': request
            },
        )
    )

    return Response({
        'count':
            scans.count(),

        'results':
            serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_detail(
    request,
    scan_id,
):

    try:

        scan = (
            ScanResult.objects.get(
                id=scan_id,
                user=request.user,
            )
        )

    except ScanResult.DoesNotExist:

        return Response(
            {
                'error':
                    'Scan not found.'
            },

            status=
                status.HTTP_404_NOT_FOUND,
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

            status=
                status.HTTP_400_BAD_REQUEST,
        )

    d = serializer.validated_data

    result = predict_crop(
        N=d['N'],
        P=d['P'],
        K=d['K'],

        temperature=
            d['temperature'],

        humidity=
            d['humidity'],

        ph=
            d['ph'],

        rainfall=
            d['rainfall'],
    )

    if not result['success']:

        return Response(
            {
                'error':
                    result.get(
                        'error',
                        'Prediction failed.',
                    )
            },

            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:

        CropRecommendation.objects.create(

            user=
                request.user,

            nitrogen=
                d['N'],

            phosphorus=
                d['P'],

            potassium=
                d['K'],

            temperature=
                d['temperature'],

            humidity=
                d['humidity'],

            ph=
                d['ph'],

            rainfall=
                d['rainfall'],

            recommended_crop=
                result['crop'],

            confidence=
                result['confidence'],

            result_data=
                result,
        )

    except Exception as e:

        logger.error(
            f"Failed to save "
            f"crop recommendation: {e}"
        )

    return Response(
        result
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crop_history(request):

    recs = (
        CropRecommendation.objects
        .filter(
            user=request.user
        )[:20]
    )

    return Response({
        'count':
            recs.count(),

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

    serializer = (
        FertilizerInputSerializer(
            data=request.data
        )
    )

    if not serializer.is_valid():

        return Response(
            serializer.errors,

            status=
                status.HTTP_400_BAD_REQUEST,
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
                'error':
                    result.get(
                        'error',
                        'Prediction failed.',
                    )
            },

            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:

        FertilizerRecommendation.objects.create(

            user=
                request.user,

            crop=
                d['crop'],

            nitrogen=
                d['N'],

            phosphorus=
                d['P'],

            potassium=
                d['K'],

            recommended_fertilizer=
                result['fertilizer'],

            confidence=
                result['confidence'],

            result_data=
                result,
        )

    except Exception as e:

        logger.error(
            f"Failed to save "
            f"fertilizer recommendation: {e}"
        )

    return Response(
        result
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fertilizer_history(request):

    recs = (
        FertilizerRecommendation.objects
        .filter(
            user=request.user
        )[:20]
    )

    return Response({
        'count':
            recs.count(),

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

    serializer = (
        IrrigationInputSerializer(
            data=request.data
        )
    )

    if not serializer.is_valid():

        return Response(
            serializer.errors,

            status=
                status.HTTP_400_BAD_REQUEST,
        )

    d = serializer.validated_data

    result = predict_irrigation(

        crop=
            d['crop'],

        soil_type=
            d['soil_type'],

        temperature=
            d['temperature'],

        humidity=
            d['humidity'],

        rainfall=
            d['rainfall'],
    )

    if not result['success']:

        return Response(
            {
                'error':
                    result.get(
                        'error',
                        'Prediction failed.',
                    )
            },

            status=
                status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    try:

        IrrigationRecommendation.objects.create(

            user=
                request.user,

            crop=
                d['crop'],

            soil_type=
                d['soil_type'],

            temperature=
                d['temperature'],

            humidity=
                d['humidity'],

            rainfall=
                d['rainfall'],

            water_requirement=
                result['label'],

            confidence=
                result['confidence'],

            result_data=
                result,
        )

    except Exception as e:

        logger.error(
            f"Failed to save "
            f"irrigation recommendation: {e}"
        )

    return Response(
        result
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def irrigation_history(request):

    recs = (
        IrrigationRecommendation.objects
        .filter(
            user=request.user
        )[:20]
    )

    return Response({
        'count':
            recs.count(),

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

    # ─────────────────────────────────────────
    # Current GPS Location
    # ─────────────────────────────────────────

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

                status=
                    status.HTTP_400_BAD_REQUEST,
            )

        data, error = (
            fetch_weather_for_coordinates(
                lat,
                lon,
            )
        )

        if data is None:

            return Response(
                {
                    'error':
                        error
                        or
                        'Could not fetch weather data.'
                },

                status=
                    status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            data
        )

    # ─────────────────────────────────────────
    # Search by City
    # ─────────────────────────────────────────

    elif city:

        data, error = (
            fetch_weather_for_city(
                city
            )
        )

        if data is None:

            return Response(
                {
                    'error':
                        error
                        or
                        'Could not fetch weather data.'
                },

                status=
                    status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            data
        )

    # ─────────────────────────────────────────
    # No Location Provided
    # ─────────────────────────────────────────

    else:

        return Response(
            {
                'error':
                    'Provide either a city name '
                    '(?city=) or coordinates '
                    '(?lat=&lon=).'
            },

            status=
                status.HTTP_400_BAD_REQUEST,
        )
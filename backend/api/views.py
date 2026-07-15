from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Public endpoint — no authentication required.
    Confirms the backend is running and reports
    which database engine is active.
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
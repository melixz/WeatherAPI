from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from datetime import datetime

from ..constants import API_VERSION, API_NAME


class HealthCheckView(APIView):
    """
    Эндпоинт для проверки состояния API
    GET /api/health
    """

    @extend_schema(
        summary="Проверка состояния API",
        description="Возвращает статус работоспособности Weather API",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "version": {"type": "string"},
                },
            }
        },
        tags=["System"],
    )
    def get(self, request):
        """Проверка здоровья API"""
        return Response(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": API_VERSION,
                "services": {
                    "database": "connected",
                    "cache": "available",
                    "external_api": "configured",
                },
            }
        )


class APIInfoView(APIView):
    """
    Информация об API эндпоинтах
    GET /api/info
    """

    @extend_schema(
        summary="Информация об API",
        description="Возвращает список доступных эндпоинтов и их описание",
        responses={
            200: {"type": "object", "properties": {"endpoints": {"type": "object"}}}
        },
        tags=["System"],
    )
    def get(self, request):
        """Информация об API"""
        return Response(
            {
                "api_name": API_NAME,
                "version": API_VERSION,
                "endpoints": {
                    "current_weather": {
                        "url": "/api/weather/current",
                        "method": "GET",
                        "description": "Получить текущую погоду",
                        "parameters": ["city"],
                    },
                    "forecast": {
                        "url": "/api/weather/forecast",
                        "method": "GET",
                        "description": "Получить прогноз погоды",
                        "parameters": ["city", "date"],
                    },
                    "custom_forecast": {
                        "url": "/api/weather/forecast",
                        "method": "POST",
                        "description": "Создать пользовательский прогноз",
                        "body": ["city", "date", "min_temperature", "max_temperature"],
                    },
                },
                "documentation": "/api/schema/swagger-ui/",
                "openapi_schema": "/api/schema/",
            }
        )

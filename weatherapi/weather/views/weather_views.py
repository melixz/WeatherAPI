from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
import logging

from ..serializers import (
    CurrentWeatherQuerySerializer,
    CurrentWeatherResponseSerializer,
    ForecastQuerySerializer,
    ForecastResponseSerializer,
    CustomForecastCreateSerializer,
    ErrorResponseSerializer,
)
from ..services import weather_service
from ..exceptions import WeatherAPIException

logger = logging.getLogger(__name__)


class CurrentWeatherView(APIView):
    """
    API эндпоинт для получения текущей погоды
    GET /api/weather/current?city=London
    """

    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Получить текущую погоду",
        description="Возвращает текущую температуру и локальное время в указанном городе",
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Название города на английском языке (например: Moscow, Amsterdam)",
            )
        ],
        responses={
            200: CurrentWeatherResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
        },
        tags=["Weather"],
    )
    def get(self, request):
        """Получение текущей погоды"""

        # Валидация query параметров
        query_serializer = CurrentWeatherQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                {
                    "error": "Ошибка валидации параметров",
                    "details": query_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = query_serializer.validated_data["city"]

        try:
            weather_data = weather_service.get_current_weather(city)

            response_serializer = CurrentWeatherResponseSerializer(data=weather_data)
            response_serializer.is_valid(raise_exception=True)

            logger.info(f"Successfully returned current weather for {city}")
            return Response(
                response_serializer.validated_data, status=status.HTTP_200_OK
            )

        except WeatherAPIException as e:
            logger.error(f"Weather API error for city {city}: {e}")
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error in current weather for {city}: {e}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ForecastView(APIView):
    """
    API эндпоинт для получения прогноза погоды
    GET /api/weather/forecast?city=Paris&date=10.06.2025
    """

    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Получить прогноз погоды",
        description="Возвращает прогноз температуры на заданную дату: минимальное и максимальное значение",
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Название города на английском языке",
            ),
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Дата в формате dd.MM.yyyy (например: 30.06.2025)",
            ),
        ],
        responses={
            200: ForecastResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
        },
        tags=["Weather"],
    )
    def get(self, request):
        """Получение прогноза погоды"""

        query_serializer = ForecastQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                {
                    "error": "Ошибка валидации параметров",
                    "details": query_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = query_serializer.validated_data["city"]
        date_obj = query_serializer.validated_data["date"]

        date_str = date_obj.strftime("%Y-%m-%d")

        try:
            forecast_data = weather_service.get_forecast(city, date_str)

            response_serializer = ForecastResponseSerializer(data=forecast_data)
            response_serializer.is_valid(raise_exception=True)

            logger.info(f"Successfully returned forecast for {city} on {date_str}")
            return Response(
                response_serializer.validated_data, status=status.HTTP_200_OK
            )

        except WeatherAPIException as e:
            logger.error(f"Weather API error for city {city} on {date_str}: {e}")
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error in forecast for {city} on {date_str}: {e}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CombinedForecastView(APIView):
    """
    Комбинированный API эндпоинт для прогноза погоды
    GET /api/weather/forecast?city=Paris&date=10.06.2025 - получить прогноз
    POST /api/weather/forecast - создать/обновить пользовательский прогноз
    """

    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Получить прогноз погоды",
        description="Возвращает прогноз температуры на заданную дату: минимальное и максимальное значение",
        parameters=[
            OpenApiParameter(
                name="city",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Название города на английском языке",
            ),
            OpenApiParameter(
                name="date",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Дата в формате dd.MM.yyyy (например: 30.06.2025)",
            ),
        ],
        responses={
            200: ForecastResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            503: ErrorResponseSerializer,
        },
        tags=["Weather"],
    )
    def get(self, request):
        """Получение прогноза погоды"""

        query_serializer = ForecastQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                {
                    "error": "Ошибка валидации параметров",
                    "details": query_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        city = query_serializer.validated_data["city"]
        date_obj = query_serializer.validated_data["date"]

        date_str = date_obj.strftime("%Y-%m-%d")

        try:
            forecast_data = weather_service.get_forecast(city, date_str)

            response_serializer = ForecastResponseSerializer(data=forecast_data)
            response_serializer.is_valid(raise_exception=True)

            logger.info(f"Successfully returned forecast for {city} on {date_str}")
            return Response(
                response_serializer.validated_data, status=status.HTTP_200_OK
            )

        except WeatherAPIException as e:
            logger.error(f"Weather API error for city {city} on {date_str}: {e}")
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error in forecast for {city} on {date_str}: {e}")
            return Response(
                {"error": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Создать/обновить пользовательский прогноз",
        description="Позволяет вручную задать или переопределить прогноз погоды для указанного города на текущую или будущую дату",
        request=CustomForecastCreateSerializer,
        responses={
            200: ForecastResponseSerializer,
            201: ForecastResponseSerializer,
            400: ErrorResponseSerializer,
        },
        tags=["Weather"],
    )
    def post(self, request):
        """Создание/обновление пользовательского прогноза"""

        serializer = CustomForecastCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Ошибка валидации данных", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            forecast = serializer.save()

            response_data = {
                "min_temperature": float(forecast.min_temperature),
                "max_temperature": float(forecast.max_temperature),
            }

            response_status = status.HTTP_201_CREATED

            logger.info(f"Custom forecast saved for {forecast.city} on {forecast.date}")
            return Response(response_data, status=response_status)

        except Exception as e:
            logger.error(f"Error saving custom forecast: {e}")
            return Response(
                {"error": "Ошибка сохранения прогноза"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomForecastView(APIView):
    """
    API эндпоинт для создания/обновления пользовательского прогноза
    POST /api/weather/forecast
    """

    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Создать/обновить пользовательский прогноз",
        description="Позволяет вручную задать или переопределить прогноз погоды для указанного города на текущую или будущую дату",
        request=CustomForecastCreateSerializer,
        responses={
            200: ForecastResponseSerializer,
            201: ForecastResponseSerializer,
            400: ErrorResponseSerializer,
        },
        tags=["Weather"],
    )
    def post(self, request):
        """Создание/обновление пользовательского прогноза"""

        serializer = CustomForecastCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Ошибка валидации данных", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            forecast = serializer.save()

            response_data = {
                "min_temperature": float(forecast.min_temperature),
                "max_temperature": float(forecast.max_temperature),
            }

            response_status = status.HTTP_201_CREATED

            logger.info(f"Custom forecast saved for {forecast.city} on {forecast.date}")
            return Response(response_data, status=response_status)

        except Exception as e:
            logger.error(f"Error saving custom forecast: {e}")
            return Response(
                {"error": "Ошибка сохранения прогноза"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

from rest_framework.response import Response
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
from .base import ServiceAPIView

logger = logging.getLogger(__name__)


class CurrentWeatherView(ServiceAPIView):
    throttle_classes = [AnonRateThrottle]
    input_serializer_class = CurrentWeatherQuerySerializer
    output_serializer_class = CurrentWeatherResponseSerializer
    service_method = staticmethod(weather_service.get_current_weather)

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
    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)


class ForecastView(ServiceAPIView):
    throttle_classes = [AnonRateThrottle]
    input_serializer_class = ForecastQuerySerializer
    output_serializer_class = ForecastResponseSerializer
    service_method = staticmethod(
        lambda city, date: weather_service.get_forecast(city, date.strftime("%Y-%m-%d"))
    )

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
    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)


class CombinedForecastView(ServiceAPIView):
    throttle_classes = [AnonRateThrottle]
    input_serializer_class = ForecastQuerySerializer
    output_serializer_class = ForecastResponseSerializer
    service_method = staticmethod(
        lambda city, date: weather_service.get_forecast(city, date.strftime("%Y-%m-%d"))
    )

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
    def get(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

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
    def post(self, request, *args, **kwargs):
        serializer = CustomForecastCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        result = weather_service.create_custom_forecast(
            validated_data["city"],
            validated_data["date"],
            validated_data["min_temperature"],
            validated_data["max_temperature"],
        )
        output_serializer = ForecastResponseSerializer(result)
        return Response(output_serializer.data, status=201)


class CustomForecastView(ServiceAPIView):
    throttle_classes = [AnonRateThrottle]
    input_serializer_class = CustomForecastCreateSerializer
    output_serializer_class = ForecastResponseSerializer
    service_method = staticmethod(
        lambda city,
        date,
        min_temperature,
        max_temperature: weather_service.create_custom_forecast(
            city, date, min_temperature, max_temperature
        )
    )
    success_status = 201

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
    def post(self, request, *args, **kwargs):
        return self.handle(request, *args, **kwargs)

from rest_framework import serializers
from datetime import datetime, date, timedelta
import re
from .models import CustomForecast
from .constants import (
    CITY_NAME_MAX_LENGTH,
    CITY_NAME_MIN_LENGTH,
    MAX_FORECAST_DAYS,
    ERROR_MESSAGES,
)
from django.db import IntegrityError


class CityValidator:
    """Валидатор для названий городов"""

    @staticmethod
    def validate_city_name(city):
        """Валидация названия города"""
        if not city or not city.strip():
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        if not re.match(r"^[a-zA-Z\s\-\'\.]+$", city.strip()):
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        if len(city.strip()) < CITY_NAME_MIN_LENGTH:
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        if len(city.strip()) > CITY_NAME_MAX_LENGTH:
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        return city.strip().title()


class DateValidator:
    """Валидатор для дат прогноза"""

    @staticmethod
    def validate_forecast_date(date_value):
        """Валидация даты прогноза"""
        today = date.today()

        if date_value < today:
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        max_date = today + timedelta(days=MAX_FORECAST_DAYS)
        if date_value > max_date:
            raise serializers.ValidationError(
                f"Дата не может быть больше чем на {MAX_FORECAST_DAYS} дней вперед. "
                f"Максимальная дата: {max_date.strftime('%d.%m.%Y')}"
            )

        return date_value


class TemperatureValidator:
    """Валидатор для температур"""

    @staticmethod
    def validate_temperature_range(min_temp, max_temp):
        """Валидация диапазона температур"""
        if min_temp is not None and max_temp is not None:
            if min_temp > max_temp:
                raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        return min_temp, max_temp


class CurrentWeatherQuerySerializer(serializers.Serializer):
    """Сериализатор для query параметров текущей погоды"""

    city = serializers.CharField(
        max_length=CITY_NAME_MAX_LENGTH, help_text="Название города на английском языке"
    )

    def validate_city(self, value):
        """Валидация города"""
        return CityValidator.validate_city_name(value)


class CurrentWeatherResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа текущей погоды"""

    temperature = serializers.SerializerMethodField()
    local_time = serializers.CharField(
        max_length=5, help_text="Локальное время в формате HH:mm"
    )

    def get_temperature(self, obj):
        return (
            float(obj["temperature"])
            if isinstance(obj["temperature"], (float, int, str))
            else float(obj["temperature"])
            if obj["temperature"] is not None
            else None
        )


class ForecastQuerySerializer(serializers.Serializer):
    """Сериализатор для query параметров прогноза"""

    city = serializers.CharField(
        max_length=CITY_NAME_MAX_LENGTH, help_text="Название города на английском языке"
    )
    date = serializers.CharField(max_length=10, help_text="Дата в формате dd.MM.yyyy")

    def validate_city(self, value):
        """Валидация города"""
        return CityValidator.validate_city_name(value)

    def validate_date(self, value):
        """Валидация и парсинг даты"""
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        return DateValidator.validate_forecast_date(parsed_date)


class ForecastResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа прогноза"""

    min_temperature = serializers.SerializerMethodField()
    max_temperature = serializers.SerializerMethodField()

    def get_min_temperature(self, obj):
        return (
            float(obj["min_temperature"])
            if isinstance(obj["min_temperature"], (float, int, str))
            else float(obj["min_temperature"])
            if obj["min_temperature"] is not None
            else None
        )

    def get_max_temperature(self, obj):
        return (
            float(obj["max_temperature"])
            if isinstance(obj["max_temperature"], (float, int, str))
            else float(obj["max_temperature"])
            if obj["max_temperature"] is not None
            else None
        )


class CustomForecastCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользовательского прогноза"""

    date = serializers.CharField(
        max_length=10, help_text="Дата в формате dd.MM.yyyy", write_only=True
    )

    class Meta:
        model = CustomForecast
        fields = ["city", "date", "min_temperature", "max_temperature"]
        validators = []

    def validate_city(self, value):
        """Валидация города"""
        return CityValidator.validate_city_name(value)

    def validate_date(self, value):
        """Валидация и парсинг даты"""
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise serializers.ValidationError(ERROR_MESSAGES["VALIDATION_ERROR"])

        return DateValidator.validate_forecast_date(parsed_date)

    def validate(self, attrs):
        """Общая валидация"""
        min_temp = attrs.get("min_temperature")
        max_temp = attrs.get("max_temperature")

        TemperatureValidator.validate_temperature_range(min_temp, max_temp)

        return attrs

    def create(self, validated_data):
        """Создание или обновление прогноза"""
        city = validated_data["city"]
        date_value = validated_data["date"]
        min_temp = validated_data["min_temperature"]
        max_temp = validated_data["max_temperature"]

        try:
            forecast = CustomForecast.objects.filter(city=city, date=date_value).first()
            if forecast:
                forecast.min_temperature = min_temp
                forecast.max_temperature = max_temp
            else:
                forecast = CustomForecast(
                    city=city,
                    date=date_value,
                    min_temperature=min_temp,
                    max_temperature=max_temp,
                )
            forecast.full_clean()
            forecast.save()
            return forecast
        except IntegrityError:
            raise serializers.ValidationError(
                {"non_field_errors": ["The fields city, date must make a unique set."]}
            )
        except Exception as e:
            from django.core.exceptions import ValidationError as DjangoValidationError

            if isinstance(e, DjangoValidationError):
                raise serializers.ValidationError(e.message_dict)
            raise


class ErrorResponseSerializer(serializers.Serializer):
    """Сериализатор для ответов с ошибками"""

    error = serializers.CharField(help_text="Описание ошибки")
    details = serializers.DictField(required=False, help_text="Детали ошибки")

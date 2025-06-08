from rest_framework import serializers
from datetime import datetime, date, timedelta
import re
from .models import CustomForecast


class CityValidator:
    """Валидатор для названий городов"""

    @staticmethod
    def validate_city_name(city):
        """Валидация названия города"""
        if not city or not city.strip():
            raise serializers.ValidationError("Название города не может быть пустым")

        if not re.match(r"^[a-zA-Z\s\-\'\.]+$", city.strip()):
            raise serializers.ValidationError(
                "Название города должно содержать только английские буквы, пробелы и дефисы"
            )

        # Проверка длины
        if len(city.strip()) < 2:
            raise serializers.ValidationError("Название города слишком короткое")

        if len(city.strip()) > 100:
            raise serializers.ValidationError("Название города слишком длинное")

        return city.strip().title()


class DateValidator:
    """Валидатор для дат прогноза"""

    @staticmethod
    def validate_forecast_date(date_value):
        """Валидация даты прогноза"""
        today = date.today()

        if date_value < today:
            raise serializers.ValidationError("Дата не может быть в прошлом")

        max_date = today + timedelta(days=10)
        if date_value > max_date:
            raise serializers.ValidationError(
                f"Дата не может быть больше чем на 10 дней вперед. "
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
                raise serializers.ValidationError(
                    "Минимальная температура не может быть больше максимальной"
                )

        return min_temp, max_temp


class CurrentWeatherQuerySerializer(serializers.Serializer):
    """Сериализатор для query параметров текущей погоды"""

    city = serializers.CharField(
        max_length=100, help_text="Название города на английском языке"
    )

    def validate_city(self, value):
        """Валидация города"""
        return CityValidator.validate_city_name(value)


class CurrentWeatherResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа текущей погоды"""

    temperature = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Текущая температура в градусах Цельсия",
    )
    local_time = serializers.CharField(
        max_length=5, help_text="Локальное время в формате HH:mm"
    )


class ForecastQuerySerializer(serializers.Serializer):
    """Сериализатор для query параметров прогноза"""

    city = serializers.CharField(
        max_length=100, help_text="Название города на английском языке"
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
            raise serializers.ValidationError(
                "Неверный формат даты. Используйте формат dd.MM.yyyy (например: 30.06.2025)"
            )

        return DateValidator.validate_forecast_date(parsed_date)


class ForecastResponseSerializer(serializers.Serializer):
    """Сериализатор для ответа прогноза"""

    min_temperature = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Минимальная температура в градусах Цельсия",
    )
    max_temperature = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        help_text="Максимальная температура в градусах Цельсия",
    )


class CustomForecastCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользовательского прогноза"""

    date = serializers.CharField(
        max_length=10, help_text="Дата в формате dd.MM.yyyy", write_only=True
    )

    class Meta:
        model = CustomForecast
        fields = ["city", "date", "min_temperature", "max_temperature"]

    def validate_city(self, value):
        """Валидация города"""
        return CityValidator.validate_city_name(value)

    def validate_date(self, value):
        """Валидация и парсинг даты"""
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise serializers.ValidationError(
                "Неверный формат даты. Используйте формат dd.MM.yyyy (например: 30.06.2025)"
            )

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

        forecast, created = CustomForecast.objects.update_or_create(
            city=city,
            date=date_value,
            defaults={
                "min_temperature": validated_data["min_temperature"],
                "max_temperature": validated_data["max_temperature"],
            },
        )

        return forecast


class ErrorResponseSerializer(serializers.Serializer):
    """Сериализатор для ответов с ошибками"""

    error = serializers.CharField(help_text="Описание ошибки")
    details = serializers.DictField(required=False, help_text="Детали ошибки")

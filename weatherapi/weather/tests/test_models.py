from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal

from ..models import CustomForecast


class CustomForecastModelTest(TestCase):
    """Тесты для модели CustomForecast"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.valid_data = {
            "city": "Moscow",
            "date": date.today() + timedelta(days=1),
            "min_temperature": Decimal("-10.5"),
            "max_temperature": Decimal("5.0"),
        }

    def test_create_valid_forecast(self):
        """Тест создания валидного прогноза"""
        forecast = CustomForecast.objects.create(**self.valid_data)

        self.assertEqual(forecast.city, "Moscow")
        self.assertEqual(forecast.min_temperature, Decimal("-10.5"))
        self.assertEqual(forecast.max_temperature, Decimal("5.0"))
        self.assertIsNotNone(forecast.created_at)
        self.assertIsNotNone(forecast.updated_at)

    def test_string_representation(self):
        """Тест строкового представления модели"""
        forecast = CustomForecast.objects.create(**self.valid_data)
        expected_str = f"Moscow - {self.valid_data['date']}: -10.5°C to 5.0°C"

        self.assertEqual(str(forecast), expected_str)

    def test_unique_constraint(self):
        """Тест уникального ограничения на город и дату"""
        CustomForecast.objects.create(**self.valid_data)

        with self.assertRaises(ValidationError):
            CustomForecast.objects.create(**self.valid_data)

    def test_update_existing_forecast(self):
        """Тест обновления существующего прогноза"""
        forecast = CustomForecast.objects.create(**self.valid_data)

        # Обновляем температуры
        forecast.min_temperature = Decimal("-15.0")
        forecast.max_temperature = Decimal("10.0")
        forecast.save()

        updated_forecast = CustomForecast.objects.get(id=forecast.id)
        self.assertEqual(updated_forecast.min_temperature, Decimal("-15.0"))
        self.assertEqual(updated_forecast.max_temperature, Decimal("10.0"))

    def test_temperature_validation_min_greater_than_max(self):
        """Тест валидации: минимальная температура больше максимальной"""
        invalid_data = self.valid_data.copy()
        invalid_data["min_temperature"] = Decimal("10.0")
        invalid_data["max_temperature"] = Decimal("5.0")

        forecast = CustomForecast(**invalid_data)

        with self.assertRaises(ValidationError):
            forecast.full_clean()

    def test_temperature_validation_extreme_values(self):
        """Тест валидации экстремальных значений температуры"""
        invalid_data = self.valid_data.copy()
        invalid_data["min_temperature"] = Decimal("-150.0")

        forecast = CustomForecast(**invalid_data)
        with self.assertRaises(ValidationError):
            forecast.full_clean()

        invalid_data = self.valid_data.copy()
        invalid_data["max_temperature"] = Decimal("150.0")

        forecast = CustomForecast(**invalid_data)
        with self.assertRaises(ValidationError):
            forecast.full_clean()

    def test_city_case_insensitive_uniqueness(self):
        """Тест что уникальность города не зависит от регистра"""
        CustomForecast.objects.create(**self.valid_data)

        invalid_data = self.valid_data.copy()
        invalid_data["city"] = "moscow"

        with self.assertRaises(ValidationError):
            CustomForecast.objects.create(**invalid_data)

    def test_past_date_allowed(self):
        """Тест что прошедшие даты разрешены для пользовательских прогнозов"""
        past_data = self.valid_data.copy()
        past_data["date"] = date.today() - timedelta(days=1)

        forecast = CustomForecast.objects.create(**past_data)
        self.assertIsNotNone(forecast.id)

    def test_ordering(self):
        """Тест сортировки по дате"""
        today = date.today()

        forecast1 = CustomForecast.objects.create(
            city="Moscow",
            date=today + timedelta(days=2),
            min_temperature=Decimal("0"),
            max_temperature=Decimal("10"),
        )

        forecast2 = CustomForecast.objects.create(
            city="London",
            date=today + timedelta(days=1),
            min_temperature=Decimal("5"),
            max_temperature=Decimal("15"),
        )

        forecasts = list(CustomForecast.objects.all())
        self.assertEqual(forecasts[0], forecast2)
        self.assertEqual(forecasts[1], forecast1)

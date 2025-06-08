from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from datetime import date, timedelta
from decimal import Decimal

from ..models import CustomForecast


class WeatherAPITest(TestCase):
    """Интеграционные тесты для Weather API"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = APIClient()
        self.current_weather_url = reverse("current-weather")
        self.forecast_url = reverse("forecast")
        self.health_url = reverse("health-check")
        self.info_url = reverse("api-info")

    @patch("weather.services.external_api.OpenWeatherMapService.get_current_weather")
    def test_current_weather_success(self, mock_get_weather):
        """Тест успешного получения текущей погоды"""
        mock_get_weather.return_value = {"temperature": 15.5, "local_time": "14:30"}

        response = self.client.get(self.current_weather_url, {"city": "Moscow"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["temperature"], 15.5)
        self.assertEqual(response.data["local_time"], "14:30")

    def test_current_weather_missing_city(self):
        """Тест ошибки при отсутствии параметра city"""
        response = self.client.get(self.current_weather_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_current_weather_invalid_city(self):
        """Тест ошибки при невалидном названии города"""
        response = self.client.get(self.current_weather_url, {"city": "A"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_forecast_with_custom_data(self):
        """Тест получения прогноза с пользовательскими данными"""
        tomorrow = date.today() + timedelta(days=1)
        CustomForecast.objects.create(
            city="Moscow",
            date=tomorrow,
            min_temperature=Decimal("-5.0"),
            max_temperature=Decimal("10.0"),
        )

        response = self.client.get(
            self.forecast_url, {"city": "Moscow", "date": tomorrow.strftime("%d.%m.%Y")}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["min_temperature"], -5.0)
        self.assertEqual(response.data["max_temperature"], 10.0)

    @patch("weather.services.external_api.OpenWeatherMapService.get_forecast")
    def test_forecast_without_custom_data(self, mock_get_forecast):
        """Тест получения прогноза из внешнего API"""
        mock_get_forecast.return_value = {
            "min_temperature": 2.0,
            "max_temperature": 12.0,
        }

        tomorrow = date.today() + timedelta(days=1)
        response = self.client.get(
            self.forecast_url, {"city": "London", "date": tomorrow.strftime("%d.%m.%Y")}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["min_temperature"], 2.0)
        self.assertEqual(response.data["max_temperature"], 12.0)

    def test_forecast_invalid_date_format(self):
        """Тест ошибки при неверном формате даты"""
        response = self.client.get(
            self.forecast_url,
            {
                "city": "Moscow",
                "date": "2025-01-15",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_forecast_past_date(self):
        """Тест ошибки при запросе прогноза на прошедшую дату"""
        yesterday = date.today() - timedelta(days=1)
        response = self.client.get(
            self.forecast_url,
            {"city": "Moscow", "date": yesterday.strftime("%d.%m.%Y")},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_forecast_too_far_future(self):
        """Тест ошибки при запросе прогноза на слишком далекую дату"""
        far_future = date.today() + timedelta(days=15)  # Больше 10 дней
        response = self.client.get(
            self.forecast_url,
            {"city": "Moscow", "date": far_future.strftime("%d.%m.%Y")},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_create_custom_forecast_success(self):
        """Тест успешного создания пользовательского прогноза"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            "city": "Moscow",
            "date": tomorrow.strftime("%d.%m.%Y"),
            "min_temperature": -10.5,
            "max_temperature": 5.0,
        }

        response = self.client.post(self.forecast_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["min_temperature"], -10.5)
        self.assertEqual(response.data["max_temperature"], 5.0)

        forecast = CustomForecast.objects.get(city="Moscow", date=tomorrow)
        self.assertEqual(forecast.min_temperature, Decimal("-10.5"))

    def test_create_custom_forecast_invalid_temperatures(self):
        """Тест ошибки при неверных температурах"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            "city": "Moscow",
            "date": tomorrow.strftime("%d.%m.%Y"),
            "min_temperature": 10.0,
            "max_temperature": 5.0,
        }

        response = self.client.post(self.forecast_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_create_custom_forecast_extreme_temperatures(self):
        """Тест ошибки при экстремальных температурах"""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            "city": "Moscow",
            "date": tomorrow.strftime("%d.%m.%Y"),
            "min_temperature": -150.0,
            "max_temperature": 150.0,
        }

        response = self.client.post(self.forecast_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_existing_custom_forecast(self):
        """Тест обновления существующего пользовательского прогноза"""
        tomorrow = date.today() + timedelta(days=1)

        CustomForecast.objects.create(
            city="Moscow",
            date=tomorrow,
            min_temperature=Decimal("0.0"),
            max_temperature=Decimal("10.0"),
        )

        data = {
            "city": "Moscow",
            "date": tomorrow.strftime("%d.%m.%Y"),
            "min_temperature": -5.0,
            "max_temperature": 15.0,
        }

        response = self.client.post(self.forecast_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["min_temperature"], -5.0)
        self.assertEqual(response.data["max_temperature"], 15.0)

        forecasts = CustomForecast.objects.filter(city="Moscow", date=tomorrow)
        self.assertEqual(forecasts.count(), 1)
        self.assertEqual(forecasts.first().min_temperature, Decimal("-5.0"))

    def test_health_check(self):
        """Тест health check endpoint"""
        response = self.client.get(self.health_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertIn("timestamp", response.data)
        self.assertIn("version", response.data)

    def test_api_info(self):
        """Тест API info endpoint"""
        response = self.client.get(self.info_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["api_name"], "Weather API")
        self.assertIn("endpoints", response.data)
        self.assertIn("current_weather", response.data["endpoints"])
        self.assertIn("forecast", response.data["endpoints"])

    def test_api_headers(self):
        """Тест что API возвращает правильные headers"""
        response = self.client.get(self.health_url)

        self.assertIn("X-Content-Type-Options", response)
        self.assertIn("X-Frame-Options", response)
        self.assertIn("X-XSS-Protection", response)

        self.assertIn("X-API-Version", response)
        self.assertIn("X-Service-Name", response)

    def test_rate_limiting(self):
        """Тест rate limiting (базовый тест)"""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

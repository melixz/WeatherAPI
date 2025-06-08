from django.test import TestCase, override_settings
from unittest.mock import Mock, patch
from datetime import date, timedelta
from decimal import Decimal

from ..services import WeatherService, OpenWeatherMapService
from ..models import CustomForecast
from ..exceptions import ExternalAPIException, CityNotFoundException


class WeatherServiceTest(TestCase):
    """Тесты для WeatherService"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.service = WeatherService()
        self.test_city = "Moscow"
        self.test_date = date.today() + timedelta(days=1)
        self.test_date_str = self.test_date.strftime("%Y-%m-%d")

    @patch("weather.services.weather_service.OpenWeatherMapService")
    def test_get_current_weather_calls_external_api(self, mock_external_api):
        """Тест что get_current_weather вызывает внешний API"""
        mock_instance = mock_external_api.return_value
        mock_instance.get_current_weather.return_value = {
            "temperature": 15.5,
            "local_time": "14:30",
        }

        service = WeatherService()
        result = service.get_current_weather(self.test_city)

        self.assertEqual(result["temperature"], 15.5)
        self.assertEqual(result["local_time"], "14:30")
        mock_instance.get_current_weather.assert_called_once_with(self.test_city)

    def test_get_forecast_with_custom_forecast(self):
        """Тест получения прогноза с пользовательскими данными"""
        CustomForecast.objects.create(
            city=self.test_city,
            date=self.test_date,
            min_temperature=Decimal("-5.0"),
            max_temperature=Decimal("10.0"),
        )

        result = self.service.get_forecast(self.test_city, self.test_date_str)

        self.assertEqual(result["min_temperature"], -5.0)
        self.assertEqual(result["max_temperature"], 10.0)

    @patch("weather.services.weather_service.OpenWeatherMapService")
    def test_get_forecast_without_custom_forecast(self, mock_external_api):
        """Тест получения прогноза без пользовательских данных"""
        mock_instance = mock_external_api.return_value
        mock_instance.get_forecast.return_value = {
            "min_temperature": 2.0,
            "max_temperature": 12.0,
        }

        service = WeatherService()
        result = service.get_forecast(self.test_city, self.test_date_str)

        self.assertEqual(result["min_temperature"], 2.0)
        self.assertEqual(result["max_temperature"], 12.0)
        mock_instance.get_forecast.assert_called_once_with(
            self.test_city, self.test_date_str
        )

    def test_create_custom_forecast_new(self):
        """Тест создания нового пользовательского прогноза"""
        result = self.service.create_custom_forecast(
            self.test_city, self.test_date, -10.0, 5.0
        )

        self.assertEqual(result["min_temperature"], -10.0)
        self.assertEqual(result["max_temperature"], 5.0)

        forecast = CustomForecast.objects.get(city=self.test_city, date=self.test_date)
        self.assertEqual(forecast.min_temperature, Decimal("-10.0"))
        self.assertEqual(forecast.max_temperature, Decimal("5.0"))

    def test_create_custom_forecast_update(self):
        """Тест обновления существующего пользовательского прогноза"""
        CustomForecast.objects.create(
            city=self.test_city,
            date=self.test_date,
            min_temperature=Decimal("0.0"),
            max_temperature=Decimal("10.0"),
        )

        result = self.service.create_custom_forecast(
            self.test_city, self.test_date, -5.0, 15.0
        )

        self.assertEqual(result["min_temperature"], -5.0)
        self.assertEqual(result["max_temperature"], 15.0)

        forecasts = CustomForecast.objects.filter(
            city=self.test_city, date=self.test_date
        )
        self.assertEqual(forecasts.count(), 1)
        self.assertEqual(forecasts.first().min_temperature, Decimal("-5.0"))


@override_settings(
    OPENWEATHER_API_KEY="test_api_key", OPENWEATHER_BASE_URL="http://test.api.com"
)
class OpenWeatherMapServiceTest(TestCase):
    """Тесты для OpenWeatherMapService"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.service = OpenWeatherMapService()
        self.test_city = "Moscow"

    @patch("weather.services.external_api.requests.get")
    def test_get_current_weather_success(self, mock_get):
        """Тест успешного получения текущей погоды"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 15.5},
            "timezone": 10800,
        }
        mock_get.return_value = mock_response

        with patch("weather.services.external_api.datetime") as mock_datetime:
            from datetime import datetime, timezone

            mock_datetime.now.return_value = datetime(
                2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strftime = datetime.strftime

            result = self.service.get_current_weather(self.test_city)

        self.assertEqual(result["temperature"], 15.5)
        self.assertIn("local_time", result)

    @patch("weather.services.external_api.requests.get")
    def test_get_current_weather_city_not_found(self, mock_get):
        """Тест обработки ошибки 404 (город не найден)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(CityNotFoundException):
            self.service.get_current_weather("NonExistentCity")

    @patch("weather.services.external_api.requests.get")
    def test_get_current_weather_api_error(self, mock_get):
        """Тест обработки ошибки API (401)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(ExternalAPIException):
            self.service.get_current_weather(self.test_city)

    @patch("weather.services.external_api.requests.get")
    def test_get_forecast_success(self, mock_get):
        """Тест успешного получения прогноза"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": [
                {"dt": 1642204800, "main": {"temp": 10.0}},
                {"dt": 1642208400, "main": {"temp": 12.0}},
                {"dt": 1642291200, "main": {"temp": 8.0}},
            ]
        }
        mock_get.return_value = mock_response

        with patch("weather.services.external_api.datetime") as mock_datetime:
            from datetime import datetime, timezone

            mock_datetime.fromtimestamp.side_effect = [
                datetime(2022, 1, 15, 12, 0, 0, tzinfo=timezone.utc),  # Нужная дата
                datetime(2022, 1, 15, 13, 0, 0, tzinfo=timezone.utc),  # Нужная дата
                datetime(2022, 1, 16, 12, 0, 0, tzinfo=timezone.utc),  # Другая дата
            ]
            mock_datetime.strptime.return_value = datetime(2022, 1, 15)

            result = self.service.get_forecast(self.test_city, "2022-01-15")

        self.assertEqual(result["min_temperature"], 10.0)
        self.assertEqual(result["max_temperature"], 12.0)

    @patch("weather.services.external_api.requests.get")
    def test_get_forecast_no_data_for_date(self, mock_get):
        """Тест когда нет данных для запрашиваемой даты"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"list": []}
        mock_get.return_value = mock_response

        with patch("weather.services.external_api.datetime") as mock_datetime:
            from datetime import datetime

            mock_datetime.strptime.return_value = datetime(2022, 1, 15)

            with self.assertRaises(ExternalAPIException):
                self.service.get_forecast(self.test_city, "2022-01-15")

    @patch("weather.services.external_api.cache")
    @patch("weather.services.external_api.requests.get")
    def test_caching_current_weather(self, mock_get, mock_cache):
        """Тест кэширования текущей погоды"""
        mock_cache.get.return_value = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"main": {"temp": 15.5}, "timezone": 10800}
        mock_get.return_value = mock_response

        with patch("weather.services.external_api.datetime") as mock_datetime:
            from datetime import datetime, timezone

            mock_datetime.now.return_value = datetime(
                2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc
            )

            result = self.service.get_current_weather(self.test_city)

        mock_cache.set.assert_called_once()

        cached_data = {"temperature": 15.5, "local_time": "15:00"}
        mock_cache.get.return_value = cached_data

        result = self.service.get_current_weather(self.test_city)

        self.assertEqual(result, cached_data)

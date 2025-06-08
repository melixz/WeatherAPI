import logging
from typing import Dict
from datetime import datetime

from .external_api import OpenWeatherMapService

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Основной сервис для работы с погодными данными
    Объединяет внешний API и локальные данные
    """

    def __init__(self):
        self.external_api = OpenWeatherMapService()

    def get_current_weather(self, city: str) -> Dict:
        """
        Получает текущую погоду (всегда из внешнего API)
        """
        return self.external_api.get_current_weather(city)

    def get_forecast(self, city: str, date_str: str) -> Dict:
        """
        Получает прогноз погоды с приоритетом пользовательских данных
        date_str в формате YYYY-MM-DD
        """
        from ..models import CustomForecast

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            custom_forecast = CustomForecast.objects.get(
                city__iexact=city, date=date_obj
            )

            logger.info(f"Using custom forecast for {city} on {date_str}")
            return {
                "min_temperature": float(custom_forecast.min_temperature),
                "max_temperature": float(custom_forecast.max_temperature),
            }

        except CustomForecast.DoesNotExist:
            logger.info(
                f"No custom forecast found, using external API for {city} on {date_str}"
            )
            return self.external_api.get_forecast(city, date_str)

    def create_custom_forecast(
        self, city: str, date_obj, min_temp: float, max_temp: float
    ) -> Dict:
        """
        Создает или обновляет пользовательский прогноз
        """
        from ..models import CustomForecast

        city = city.strip().title() if city else city

        forecast, created = CustomForecast.objects.update_or_create(
            city=city,
            date=date_obj,
            defaults={"min_temperature": min_temp, "max_temperature": max_temp},
        )
        forecast.full_clean()
        forecast.save()

        action = "создан" if created else "обновлен"
        logger.info(f"Custom forecast {action} for {city} on {date_obj}")

        return {
            "min_temperature": float(forecast.min_temperature),
            "max_temperature": float(forecast.max_temperature),
        }

    def validate_city(self, city: str) -> bool:
        """
        Проверяет существование города через внешний API
        """
        try:
            coordinates = self.external_api.get_city_coordinates(city)
            return coordinates is not None
        except Exception:
            return False


weather_service = WeatherService()

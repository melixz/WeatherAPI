# Импорты из external_api.py
from .external_api import OpenWeatherMapService

# Импорты из weather_service.py
from .weather_service import WeatherService, weather_service

# Экспорт всех сервисов для обратной совместимости
__all__ = [
    "OpenWeatherMapService",
    "WeatherService",
    "weather_service",  # Глобальный экземпляр
]

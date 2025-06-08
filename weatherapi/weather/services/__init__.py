from .external_api import OpenWeatherMapService

# Импорты из weather_service.py
from .weather_service import WeatherService, weather_service

__all__ = [
    "OpenWeatherMapService",
    "WeatherService",
    "weather_service",
]

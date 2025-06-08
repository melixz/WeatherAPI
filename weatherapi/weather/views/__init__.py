# Импорты из weather_views.py
from .weather_views import (
    CurrentWeatherView,
    ForecastView,
    CombinedForecastView,
    CustomForecastView,
)

# Импорты из system_views.py
from .system_views import (
    HealthCheckView,
    APIInfoView,
)

# Экспорт всех views для обратной совместимости
__all__ = [
    # Weather views
    "CurrentWeatherView",
    "ForecastView",
    "CombinedForecastView",
    "CustomForecastView",
    # System views
    "HealthCheckView",
    "APIInfoView",
]

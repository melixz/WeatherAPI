from django.urls import path
from .views import (
    CurrentWeatherView,
    CombinedForecastView,
    HealthCheckView,
    APIInfoView,
)

urlpatterns = [
    path("weather/current/", CurrentWeatherView.as_view(), name="current-weather"),
    path("weather/forecast/", CombinedForecastView.as_view(), name="forecast"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("info/", APIInfoView.as_view(), name="api-info"),
]

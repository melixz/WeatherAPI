import requests
from datetime import datetime, timezone, timedelta
from django.conf import settings
from django.core.cache import cache
import logging
import time
from typing import Dict, Optional, Tuple

from ..constants import (
    OPENWEATHER_REQUEST_TIMEOUT,
    OPENWEATHER_MAX_RETRIES,
    OPENWEATHER_RETRY_DELAY,
    CACHE_TIMEOUT_CURRENT_WEATHER,
    CACHE_TIMEOUT_FORECAST,
)
from ..exceptions import (
    ExternalAPIException,
    CityNotFoundException,
    handle_external_api_error,
    validate_city_exists,
)

logger = logging.getLogger(__name__)


class OpenWeatherMapService:
    """
    Сервис для работы с OpenWeatherMap API
    """

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.timeout = OPENWEATHER_REQUEST_TIMEOUT
        self.max_retries = OPENWEATHER_MAX_RETRIES
        self.retry_delay = OPENWEATHER_RETRY_DELAY

        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")

    def _make_request(self, url: str, params: Dict) -> Dict:
        """
        Выполняет HTTP запрос с retry логикой
        """
        params["appid"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to {url}, attempt {attempt + 1}")

                response = requests.get(url, params=params, timeout=self.timeout)

                if response.status_code == 404:
                    raise CityNotFoundException("Город не найден в OpenWeatherMap")

                if response.status_code == 401:
                    raise ExternalAPIException("Неверный API ключ OpenWeatherMap")

                if response.status_code == 429:
                    raise ExternalAPIException(
                        "Превышен лимит запросов к OpenWeatherMap"
                    )

                response.raise_for_status()

                data = response.json()
                logger.info(f"Successful response from {url}")
                return data

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    raise ExternalAPIException("Таймаут при обращении к сервису погоды")

            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    raise ExternalAPIException("Ошибка соединения с сервисом погоды")

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if e.response.status_code >= 500:
                    if attempt == self.max_retries - 1:
                        raise ExternalAPIException("Сервис погоды временно недоступен")
                else:
                    raise ExternalAPIException(f"Ошибка API: {e}")

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == self.max_retries - 1:
                    raise ExternalAPIException(f"Неожиданная ошибка: {e}")

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        raise ExternalAPIException("Не удалось получить данные после всех попыток")

    def _get_cache_key(self, endpoint: str, city: str, date: str = None) -> str:
        """Генерирует ключ для кэша"""
        if date:
            return f"weather_{endpoint}_{city.lower()}_{date}"
        return f"weather_{endpoint}_{city.lower()}"

    @handle_external_api_error
    @validate_city_exists
    def get_current_weather(self, city: str) -> Dict:
        """
        Получает текущую погоду для города
        """
        cache_key = self._get_cache_key("current", city)
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(f"Returning cached current weather for {city}")
            return cached_data

        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "units": "metric",
            "lang": "en",
        }

        data = self._make_request(url, params)

        temperature = round(data["main"]["temp"], 1)

        timezone_offset = data["timezone"]
        utc_time = datetime.now(timezone.utc)
        local_time = utc_time + timedelta(seconds=timezone_offset)
        local_time_str = local_time.strftime("%H:%M")

        result = {"temperature": temperature, "local_time": local_time_str}

        cache.set(cache_key, result, CACHE_TIMEOUT_CURRENT_WEATHER)

        logger.info(f"Retrieved current weather for {city}: {temperature}°C")
        return result

    @handle_external_api_error
    @validate_city_exists
    def get_forecast(self, city: str, target_date: str) -> Dict:
        """
        Получает прогноз погоды для города на определенную дату
        target_date в формате YYYY-MM-DD
        """
        cache_key = self._get_cache_key("forecast", city, target_date)
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(f"Returning cached forecast for {city} on {target_date}")
            return cached_data

        url = f"{self.base_url}/forecast"
        params = {"q": city, "units": "metric", "lang": "en"}

        data = self._make_request(url, params)

        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")

        daily_temps = []

        for item in data["list"]:
            forecast_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc)

            if forecast_time.date() == target_datetime.date():
                daily_temps.append(item["main"]["temp"])

        if not daily_temps:
            raise ExternalAPIException(
                f"Прогноз для даты {target_date} недоступен. "
                f"Доступны прогнозы только на ближайшие 5 дней."
            )

        min_temp = round(min(daily_temps), 1)
        max_temp = round(max(daily_temps), 1)

        result = {"min_temperature": min_temp, "max_temperature": max_temp}

        cache.set(cache_key, result, CACHE_TIMEOUT_FORECAST)

        logger.info(
            f"Retrieved forecast for {city} on {target_date}: {min_temp}°C - {max_temp}°C"
        )
        return result

    def get_city_coordinates(self, city: str) -> Optional[Tuple[float, float]]:
        """
        Получает координаты города (для дополнительной валидации)
        """
        try:
            url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {"q": city, "limit": 1, "appid": self.api_key}

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            if data:
                return data[0]["lat"], data[0]["lon"]

            return None

        except Exception as e:
            logger.warning(f"Could not get coordinates for {city}: {e}")
            return None

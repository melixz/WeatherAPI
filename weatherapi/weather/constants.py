API_VERSION = "1.0.0"
API_NAME = "Weather API"

CACHE_TIMEOUT_CURRENT_WEATHER = 300
CACHE_TIMEOUT_FORECAST = 3600

OPENWEATHER_REQUEST_TIMEOUT = 10
OPENWEATHER_MAX_RETRIES = 3
OPENWEATHER_RETRY_DELAY = 1

MIN_TEMPERATURE = -100.0
MAX_TEMPERATURE = 100.0

MAX_FORECAST_DAYS = 10

CITY_NAME_MAX_LENGTH = 100
CITY_NAME_MIN_LENGTH = 2

ERROR_MESSAGES = {
    "VALIDATION_ERROR": "Ошибка валидации параметров",
    "INTERNAL_ERROR": "Внутренняя ошибка сервера",
    "CITY_NOT_FOUND": "Город не найден",
    "FORECAST_SAVE_ERROR": "Ошибка сохранения прогноза",
    "EXTERNAL_API_ERROR": "Ошибка внешнего API",
    "RATE_LIMIT_EXCEEDED": "Превышен лимит запросов",
}

ENDPOINTS_INFO = {
    "current_weather": {
        "url": "/api/weather/current",
        "method": "GET",
        "description": "Получить текущую погоду",
        "parameters": ["city"],
    },
    "forecast": {
        "url": "/api/weather/forecast",
        "method": "GET",
        "description": "Получить прогноз погоды",
        "parameters": ["city", "date"],
    },
    "custom_forecast": {
        "url": "/api/weather/forecast",
        "method": "POST",
        "description": "Создать пользовательский прогноз",
        "body": ["city", "date", "min_temperature", "max_temperature"],
    },
}

LOG_FORMATS = {
    "REQUEST": "[{request_id}] {method} {path} from {ip}",
    "RESPONSE": "[{request_id}] Response {status_code} in {duration}ms",
    "ERROR": "[{request_id}] Error: {error_type}: {error_message}",
}

__all__ = [
    "API_VERSION",
    "API_NAME",
    "CACHE_TIMEOUT_CURRENT_WEATHER",
    "CACHE_TIMEOUT_FORECAST",
    "OPENWEATHER_REQUEST_TIMEOUT",
    "OPENWEATHER_MAX_RETRIES",
    "OPENWEATHER_RETRY_DELAY",
    "MIN_TEMPERATURE",
    "MAX_TEMPERATURE",
    "MAX_FORECAST_DAYS",
    "CITY_NAME_MAX_LENGTH",
    "CITY_NAME_MIN_LENGTH",
    "ERROR_MESSAGES",
    "ENDPOINTS_INFO",
    "LOG_FORMATS",
]

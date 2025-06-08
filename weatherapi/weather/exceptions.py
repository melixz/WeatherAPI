from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)


class WeatherAPIException(Exception):
    """Базовое исключение для Weather API"""

    default_message = "Произошла ошибка в Weather API"
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message=None, status_code=None):
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        super().__init__(self.message)


class CityNotFoundException(WeatherAPIException):
    """Исключение для случая когда город не найден"""

    default_message = "Город не найден"
    default_status_code = status.HTTP_404_NOT_FOUND


class ExternalAPIException(WeatherAPIException):
    """Исключение для ошибок внешнего API"""

    default_message = "Ошибка получения данных о погоде"
    default_status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ValidationException(WeatherAPIException):
    """Исключение для ошибок валидации"""

    default_message = "Ошибка валидации данных"
    default_status_code = status.HTTP_400_BAD_REQUEST


class DateRangeException(ValidationException):
    """Исключение для ошибок диапазона дат"""

    default_message = "Неверный диапазон дат"


class TemperatureRangeException(ValidationException):
    """Исключение для ошибок диапазона температур"""

    default_message = "Неверный диапазон температур"


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для Weather API
    """
    response = exception_handler(exc, context)

    logger.error(f"Exception in {context.get('view', 'Unknown view')}: {exc}")

    if isinstance(exc, WeatherAPIException):
        custom_response_data = {"error": exc.message}
        return Response(custom_response_data, status=exc.status_code)

    if isinstance(exc, DjangoValidationError):
        custom_response_data = {
            "error": "Ошибка валидации",
            "details": exc.message_dict if hasattr(exc, "message_dict") else str(exc),
        }
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)

    if response is not None:
        custom_response_data = {"error": "Произошла ошибка"}

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data["error"] = "Ошибка валидации данных"
            if isinstance(response.data, dict):
                custom_response_data["details"] = response.data
            else:
                custom_response_data["details"] = str(response.data)

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data["error"] = "Ресурс не найден"

        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            custom_response_data["error"] = "Метод не разрешен"

        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data["error"] = "Слишком много запросов. Попробуйте позже"

        elif response.status_code >= 500:
            custom_response_data["error"] = "Внутренняя ошибка сервера"

        response.data = custom_response_data

    return response


def handle_external_api_error(func):
    """
    Декоратор для обработки ошибок внешнего API
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"External API error in {func.__name__}: {e}")
            raise ExternalAPIException(f"Не удалось получить данные о погоде: {str(e)}")

    return wrapper


def validate_city_exists(func):
    """
    Декоратор для проверки существования города
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise CityNotFoundException(
                    "Указанный город не найден. Проверьте правильность написания"
                )
            raise

    return wrapper

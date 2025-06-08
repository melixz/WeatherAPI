import time
import functools
import logging
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


def timing_decorator(func: Callable) -> Callable:
    """
    Декоратор для измерения времени выполнения функций
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        duration = round((end_time - start_time) * 1000, 2)
        logger.info(f"{func.__name__} executed in {duration}ms")

        return result

    return wrapper


def cache_key_builder(prefix: str, *args, **kwargs) -> str:
    """
    Строит ключ для кэша из префикса и аргументов
    """
    key_parts = [prefix]

    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg).lower())

    for key, value in sorted(kwargs.items()):
        if isinstance(value, (str, int, float)):
            key_parts.append(f"{key}:{str(value).lower()}")

    return "_".join(key_parts)


def smart_cache(timeout: int = 300, key_prefix: str = "default"):
    """
    Умный декоратор кэширования с автоматическим построением ключей
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_builder(
                f"{key_prefix}_{func.__name__}", *args, **kwargs
            )

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            result = func(*args, **kwargs)

            cache.set(cache_key, result, timeout)
            logger.info(f"Cache set for {func.__name__}: {cache_key}")

            return result

        return wrapper

    return decorator


def format_temperature(temp: float, precision: int = 1) -> float:
    """
    Форматирует температуру с заданной точностью
    """
    return round(float(temp), precision)


def format_local_time(utc_time: datetime, timezone_offset: int) -> str:
    """
    Конвертирует UTC время в локальное время города

    Args:
        utc_time: UTC время
        timezone_offset: Смещение в секундах от UTC

    Returns:
        Локальное время в формате HH:MM
    """
    local_time = utc_time + timedelta(seconds=timezone_offset)
    return local_time.strftime("%H:%M")


def validate_date_range(date_obj, max_days_future: int = 10) -> bool:
    """
    Проверяет что дата находится в допустимом диапазоне

    Args:
        date_obj: Объект даты для проверки
        max_days_future: Максимальное количество дней в будущем

    Returns:
        True если дата валидна, False иначе
    """
    today = datetime.now().date()
    max_future_date = today + timedelta(days=max_days_future)

    return today <= date_obj <= max_future_date


def sanitize_city_name(city: str) -> str:
    """
    Очищает и нормализует название города
    """
    if not city:
        return ""

    sanitized = city.strip().title()

    sanitized = " ".join(sanitized.split())

    return sanitized


def build_error_response(
    message: str, details: Optional[Dict] = None, request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Строит стандартизированный ответ об ошибке
    """
    error_response = {
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if details:
        error_response["details"] = details

    if request_id:
        error_response["request_id"] = request_id

    return error_response


def get_client_ip(request) -> str:
    """
    Получает IP адрес клиента из запроса
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        return x_real_ip.strip()

    return request.META.get("REMOTE_ADDR", "unknown")


def log_api_call(func: Callable) -> Callable:
    """
    Декоратор для логирования API вызовов
    """

    @functools.wraps(func)
    def wrapper(self, request, *args, **kwargs):
        request_id = getattr(request, "request_id", "unknown")
        client_ip = get_client_ip(request)

        logger.info(
            f"[{request_id}] API call: {func.__name__} "
            f"from {client_ip} with params: {request.query_params.dict()}"
        )

        start_time = time.time()

        try:
            response = func(self, request, *args, **kwargs)
            duration = round((time.time() - start_time) * 1000, 2)

            logger.info(
                f"[{request_id}] API response: {response.status_code} in {duration}ms"
            )

            return response

        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)

            logger.error(
                f"[{request_id}] API error: {type(e).__name__}: {e} after {duration}ms"
            )
            raise

    return wrapper


def retry_on_failure(
    max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0
):
    """
    Декоратор для повторных попыток при ошибках
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff_factor**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


class PerformanceMonitor:
    """
    Класс для мониторинга производительности
    """

    def __init__(self):
        self.metrics = {}

    def record_metric(self, name: str, value: float, tags: Optional[Dict] = None):
        """Записывает метрику производительности"""
        if name not in self.metrics:
            self.metrics[name] = []

        metric_data = {
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": tags or {},
        }

        self.metrics[name].append(metric_data)

        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-500:]

    def get_average(self, name: str, last_n: Optional[int] = None) -> Optional[float]:
        """Получает среднее значение метрики"""
        if name not in self.metrics or not self.metrics[name]:
            return None

        values = self.metrics[name]
        if last_n:
            values = values[-last_n:]

        return sum(m["value"] for m in values) / len(values)

    def get_stats(self, name: str) -> Optional[Dict]:
        """Получает статистику по метрике"""
        if name not in self.metrics or not self.metrics[name]:
            return None

        values = [m["value"] for m in self.metrics[name]]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "last": values[-1] if values else None,
        }


performance_monitor = PerformanceMonitor()

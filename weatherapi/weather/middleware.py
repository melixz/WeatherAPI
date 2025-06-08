import logging
import time
import uuid
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования всех API запросов
    """

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())[:8]
        request.start_time = time.time()

        logger.info(
            f"[{request.request_id}] {request.method} {request.path} "
            f"from {self.get_client_ip(request)}"
        )

        return None

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = round((time.time() - request.start_time) * 1000, 2)
            request_id = getattr(request, "request_id", "unknown")

            logger.info(
                f"[{request_id}] Response {response.status_code} in {duration}ms"
            )

        return response

    def get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "unknown")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления security headers
    """

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if request.path.startswith("/api/") and not any(
            path in request.path for path in ["/swagger-ui/", "/redoc/", "/schema/"]
        ):
            response["Content-Security-Policy"] = "default-src 'none'"

        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware для обработки необработанных исключений
    """

    def process_exception(self, request, exception):
        request_id = getattr(request, "request_id", "unknown")

        logger.error(
            f"[{request_id}] Unhandled exception: {type(exception).__name__}: {exception}",
            exc_info=True,
        )

        if request.path.startswith("/api/"):
            error_response = {
                "error": "Внутренняя ошибка сервера",
                "request_id": request_id,
            }

            if settings.DEBUG:
                error_response["debug"] = {
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception),
                }

            return JsonResponse(
                error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return None


class APIVersionMiddleware(MiddlewareMixin):
    """
    Middleware для добавления версии API в headers
    """

    def process_response(self, request, response):
        if request.path.startswith("/api/"):
            response["X-API-Version"] = "1.0.0"
            response["X-Service-Name"] = "Weather API"

        return response

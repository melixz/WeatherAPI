from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class ErrorHandlingMixin:
    """
    Миксин для централизованной обработки ошибок сервисного слоя
    """

    def handle_service_error(self, exc):
        logger.error(f"Service error: {exc}")
        return Response(
            {"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ServiceAPIView(ErrorHandlingMixin, APIView):
    """
    Базовый класс для APIView, который реализует паттерн:
    - валидация входных данных через сериализатор
    - вызов сервиса
    - сериализация результата
    - обработка ошибок и логирование
    """

    input_serializer_class = None
    output_serializer_class = None
    service_method = None
    success_status = status.HTTP_200_OK

    def handle(self, request, *args, **kwargs):
        serializer = self.input_serializer_class(data=self.get_input_data(request))
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        try:
            result = self.service_method(**validated_data)
        except Exception as e:
            return self.handle_service_error(e)

        output_serializer = self.output_serializer_class(result)
        return Response(output_serializer.data, status=self.success_status)

    def get_input_data(self, request):
        if request.method in ["POST", "PUT", "PATCH"]:
            return request.data
        return request.query_params

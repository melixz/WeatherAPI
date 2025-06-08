from django.contrib import admin
from .models import CustomForecast


@admin.register(CustomForecast)
class CustomForecastAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для управления пользовательскими прогнозами
    """

    list_display = [
        "city",
        "date",
        "min_temperature",
        "max_temperature",
        "created_at",
        "updated_at",
    ]
    list_filter = ["date", "city", "created_at"]
    search_fields = ["city", "date"]
    ordering = ["-date", "city"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Основная информация", {"fields": ("city", "date")}),
        ("Температурные данные", {"fields": ("min_temperature", "max_temperature")}),
        (
            "Метаданные",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related()

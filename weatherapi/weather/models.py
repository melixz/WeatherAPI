from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from .constants import (
    CITY_NAME_MAX_LENGTH,
    MIN_TEMPERATURE,
    MAX_TEMPERATURE,
)


class CustomForecast(models.Model):
    """
    Модель для хранения пользовательских прогнозов погоды.
    Переопределяет реальные данные для конкретного города и даты.
    """

    city = models.CharField(
        max_length=CITY_NAME_MAX_LENGTH,
        verbose_name="Город",
        help_text="Название города на английском языке",
    )
    date = models.DateField(
        verbose_name="Дата прогноза", help_text="Дата в формате YYYY-MM-DD"
    )
    min_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Минимальная температура",
        help_text="Минимальная температура в градусах Цельсия",
        validators=[
            MinValueValidator(MIN_TEMPERATURE),
            MaxValueValidator(MAX_TEMPERATURE),
        ],
    )
    max_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Максимальная температура",
        help_text="Максимальная температура в градусах Цельсия",
        validators=[
            MinValueValidator(MIN_TEMPERATURE),
            MaxValueValidator(MAX_TEMPERATURE),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Пользовательский прогноз"
        verbose_name_plural = "Пользовательские прогнозы"
        unique_together = ["city", "date"]
        indexes = [
            models.Index(fields=["city", "date"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["date", "city"]

    def __str__(self):
        return f"{self.city} - {self.date}: {self.min_temperature}°C to {self.max_temperature}°C"

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError

        if self.min_temperature and self.max_temperature:
            if self.min_temperature > self.max_temperature:
                raise ValidationError(
                    "Минимальная температура не может быть больше максимальной"
                )
        if self.city and self.date:
            qs = CustomForecast.objects.filter(date=self.date, city__iexact=self.city)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Прогноз для этого города и даты уже существует (без учета регистра)"
                )

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean()"""
        if self.city:
            self.city = self.city.strip().title()
        self.clean()
        super().save(*args, **kwargs)

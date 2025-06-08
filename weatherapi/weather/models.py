from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomForecast(models.Model):
    """
    Модель для хранения пользовательских прогнозов погоды.
    Переопределяет реальные данные для конкретного города и даты.
    """

    city = models.CharField(
        max_length=100,
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
        validators=[MinValueValidator(-100.0), MaxValueValidator(100.0)],
    )
    max_temperature = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name="Максимальная температура",
        help_text="Максимальная температура в градусах Цельсия",
        validators=[MinValueValidator(-100.0), MaxValueValidator(100.0)],
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
        ordering = ["-date", "city"]

    def __str__(self):
        return f"{self.city} - {self.date}: {self.min_temperature}°C / {self.max_temperature}°C"

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError

        if self.min_temperature and self.max_temperature:
            if self.min_temperature > self.max_temperature:
                raise ValidationError(
                    "Минимальная температура не может быть больше максимальной"
                )

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean()"""
        self.clean()
        super().save(*args, **kwargs)

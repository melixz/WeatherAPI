# Weather API

REST API для получения данных о погоде с возможностью переопределения прогнозов.

## Особенности

- **Текущая погода**: Получение актуальной температуры и локального времени
- **Прогноз погоды**: 5-дневный прогноз с возможностью пользовательских переопределений
- **Кэширование**: Оптимизированная производительность с Redis кэшированием
- **Валидация**: Комплексная валидация входных данных
- **Безопасность**: Rate limiting, security headers, логирование
- **Документация**: Автоматическая OpenAPI/Swagger документация

## Быстрый старт

### Требования

- Python 3.12+
- Django 5.2.2
- PostgreSQL (опционально, по умолчанию SQLite)
- OpenWeatherMap API ключ

### Установка

1. Установите [uv](https://github.com/astral-sh/uv):

```bash
# На Linux/macOS через curl
curl -LsSf https://astral.sh/uv/install.sh | sh
# или через pipx
pipx install uv
```

2. Создайте виртуальное окружение и активируйте его:

```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
```

3. Установите зависимости проекта:

```bash
uv sync
```

4. Запустите сервер 

```bash
python manage.py runserver
```

API будет доступно по адресу: `http://localhost:8000/api/`

## API Документация

### Автоматическая документация

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Основные эндпоинты

#### 1. Текущая погода

```http
GET /api/weather/current?city=Moscow
```

**Параметры:**
- `city` (string, обязательный) - Название города на английском языке

**Ответ:**
```json
{
  "temperature": 15.5,
  "local_time": "14:30"
}
```

#### 2. Прогноз погоды

```http
GET /api/weather/forecast?city=Paris&date=15.01.2025
```

**Параметры:**
- `city` (string, обязательный) - Название города на английском языке
- `date` (string, обязательный) - Дата в формате dd.MM.yyyy

**Ответ:**
```json
{
  "min_temperature": 2.0,
  "max_temperature": 12.0
}
```

#### 3. Создание пользовательского прогноза

```http
POST /api/weather/forecast
Content-Type: application/json

{
  "city": "Moscow",
  "date": "20.01.2025",
  "min_temperature": -10.5,
  "max_temperature": 5.0
}
```

**Ответ:**
```json
{
  "min_temperature": -10.5,
  "max_temperature": 5.0
}
```

#### 4. Системные эндпоинты

**Health Check:**
```http
GET /api/health
```

**API Info:**
```http
GET /api/info
```

## Конфигурация

### Переменные окружения

```env
# OpenWeatherMap API
OPENWEATHER_API_KEY=your_api_key_here
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (опционально)
DATABASE_URL=postgresql://user:password@localhost:5432/weatherapi

# Cache (опционально)
REDIS_URL=redis://localhost:6379/0
```

### Настройки кэширования

- **Текущая погода**: 5 минут
- **Прогноз погоды**: 1 час
- **Пользовательские прогнозы**: Приоритет над внешним API

### Rate Limiting

- **Анонимные пользователи**: 100 запросов/час
- **Burst limit**: 10 запросов/минуту

## Тестирование

### Запуск тестов

```bash
# Все тесты
python weatherapi/manage.py test

# Конкретные тесты
python weatherapi/manage.py test weather.tests.test_models
python weatherapi/manage.py test weather.tests.test_services
python weatherapi/manage.py test weather.tests.test_api
```

### Покрытие тестами

- **Модели**: Валидация, ограничения, бизнес-логика
- **Сервисы**: Внешний API, кэширование, обработка ошибок
- **API**: Интеграционные тесты всех эндпоинтов

## Архитектура

### Структура проекта

```
weatherapi/
├── weather/                    # Основное приложение
│   ├── views/                  # API views (модульная структура)
│   │   ├── weather_views.py    # Weather endpoints
│   │   └── system_views.py     # System endpoints
│   ├── services/               # Бизнес-логика
│   │   ├── external_api.py     # OpenWeatherMap интеграция
│   │   └── weather_service.py  # Основной сервис
│   ├── tests/                  # Тесты
│   ├── models.py               # Модели данных
│   ├── serializers.py          # DRF сериализаторы
│   ├── exceptions.py           # Обработка исключений
│   ├── middleware.py           # Custom middleware
│   └── constants.py            # Константы
└── settings/                   # Настройки Django
```

### Принципы архитектуры

1. **Модульность**: Разделение на логические модули
2. **Слоистость**: Views → Services → Models
3. **Единая ответственность**: Каждый модуль имеет четкую роль
4. **Тестируемость**: Высокое покрытие тестами
5. **Масштабируемость**: Готовность к росту нагрузки

## Безопасность

### Реализованные меры

- **Rate Limiting**: Защита от DDoS атак
- **Security Headers**: XSS, CSRF, Clickjacking защита
- **Input Validation**: Валидация всех входных данных
- **Error Handling**: Безопасная обработка ошибок
- **Logging**: Детальное логирование для аудита

### Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'none'` (для API)

## Мониторинг и логирование

### Логирование

- **Уровни**: INFO, WARNING, ERROR
- **Форматы**: Структурированные логи с request ID
- **Файлы**: `weather_api.log` для WARNING+
- **Консоль**: Все логи в development

### Метрики

- **Request ID**: Уникальный идентификатор для каждого запроса
- **Response Time**: Время обработки запросов
- **Error Tracking**: Отслеживание ошибок с контекстом

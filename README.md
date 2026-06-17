# NutriBot

Telegram-бот, который возвращает БЖУ (белки, жиры, углеводы) и калорийность продуктов питания. Работает на русском и английском языках.

## Технологии

- **Python 3.10+**
- **python-telegram-bot** — взаимодействие с Telegram API
- **Google Gemini 2.5 Flash Lite** — генерация ответов о питании (через `google-genai`)
- **python-dotenv** — загрузка переменных окружения

## Архитектура

```
bot.py          — основной файл: обработчики команд, валидация, rate limiting, логика запросов к Gemini
test_bot.py     — unit-тесты (pytest + pytest-asyncio)
Procfile        — конфигурация для Heroku (worker process)
requirements.txt — зависимости продакшена
requirements-dev.txt — зависимости для тестов
```

### Поток данных

1. Пользователь отправляет сообщение в Telegram
2. `handle_message` проверяет: пустое ли сообщение, длина, rate limit (5 сек на пользователя)
3. Формируется промпт для Gemini с инструкциями по формату ответа
4. Gemini возвращает БЖУ — бот отправляет ответ пользователю
5. При ошибке API пользователь получает понятное сообщение

### Rate Limiting

- Один запрос в 5 секунд на пользователя
- Хранится в `defaultdict(float)` в оперативной памяти (сбрасывается при перезапуске)

## Переменные окружения

| Переменная | Описание | Как получить |
|------------|----------|--------------|
| `TELEGRAM_TOKEN` | Токен Telegram бота | @BotFather → /newbot |
| `GEMINI_API_KEY` | API ключ Google Gemini | https://aistudio.google.com/apikey |

## Установка и запуск

```bash
git clone https://github.com/IvanAlekseenko-sys/nutribot.git
cd nutribot
pip install -r requirements.txt

# Создать .env файл
echo "TELEGRAM_TOKEN=your_token" > .env
echo "GEMINI_API_KEY=your_key" >> .env

# Запуск
python bot.py
```

## Тесты

```bash
pip install -r requirements-dev.txt
python -m pytest test_bot.py -v
```

### Покрытие тестов

| Класс | Что тестирует |
|-------|---------------|
| `TestCheckRateLimit` | Блокировка повторных запросов, независимость пользователей, сброс по времени |
| `TestHandleMessage` | Пустые сообщения, длинные сообщения, rate limit, успешный запрос, ошибки API (429, 401, 503), транкация |
| `TestStartCommand` | Ответ на /start |
| `TestHelpCommand` | Ответ на /help |

## Деплой

Текущий деплой — **Heroku** (worker process через `Procfile`).

Альтернативы:
- **Docker** — контейнеризация для переноса на любой сервер
- **VPS** — $3-5/мес (DigitalOcean, Hetzner)

## Контакты

- Автор: [IvanAlekseenko-sys](https://github.com/IvanAlekseenko-sys)

# NutriBot

Telegram-бот для получения информации о БЖУ и калорийности продуктов питания.

Telegram bot for nutrition info (calories, protein, fat, carbs).

## Установка / Installation

```bash
git clone https://github.com/IvanAlekseenko-sys/nutribot.git
cd nutribot
pip install -r requirements.txt
```

## Настройка / Setup

Создайте файл `.env`:

```
TELEGRAM_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

## Запуск / Run

```bash
python bot.py
```

## Использование / Usage

1. Найдите бота в Telegram: `/start`
2. Отправьте название продукта (например: `курица`, `гречка 200г`)
3. Получите информацию о БЖУ

## Примеры / Examples

- `курица` → БЖУ на 100г
- `куриная грудка 200г` → БЖУ на 200г
- `buckwheat` → БЖУ на 100г
- `chicken breast 200g` → БЖУ на 200г

## Лицензия / License

MIT

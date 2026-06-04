from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🥗 Я помогу узнать БЖУ и калорийность продуктов.\n"
        "Просто напиши название продукта — например: *курица* или *курица 150г*\n\n"
        "Hi! 🥗 I can help you find nutrition info.\n"
        "Just type a product name — e.g. *chicken* or *chicken 150g*",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    await update.message.reply_text("⏳ Считаю... / Calculating...")

    prompt = f"""
Дай информацию о БЖУ и калорийности: {text}

Правила определения порции:
- Если в тексте есть любое число (например: 150, 150г, 150 г, 150ml, 150 мл, 150 грамм) — используй его как объём/вес
- Если числа нет — дай данные на 100г или 100мл в зависимости от продукта
- Для жидкостей (молоко, сок, кефир, вода, напитки, супы и т.д.) используй мл
- Для твёрдых продуктов используй г

Ответь строго в таком формате:
🍽 Продукт: [название]
⚖️ Порция: [количество]г или [количество]мл (в зависимости от типа продукта)

🔥 Калории: [число] ккал
💪 Белки: [число]г
🧈 Жиры: [число]г
🍞 Углеводы: [число]г

ВАЖНО: Отвечай СТРОГО на том же языке, на котором написан запрос. Если запрос на английском — весь ответ на английском, включая названия полей. Если на русском — весь ответ на русском.
Коротко, без лишнего текста.
"""

    try:
        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как пользоваться:\n"
        "• Напиши продукт → БЖУ на 100г\n"
        "• Напиши продукт + граммы → БЖУ на порцию\n\n"
        "How to use:\n"
        "• Type a product → nutrition per 100g\n"
        "• Type a product + grams → nutrition per portion\n\n"
        "Примеры / Examples:\n"
        "  *гречка* / *buckwheat*\n"
        "  *куриная грудка 200г* / *chicken breast 200g*",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен...")
app.run_polling()
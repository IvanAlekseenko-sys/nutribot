from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from dotenv import load_dotenv
import os

print("ENV vars direct:", os.environ.get("GEMINI_API_KEY", "NOT FOUND"))
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"TOKEN загружен: {bool(TELEGRAM_TOKEN)}")
print(f"GEMINI загружен: {bool(GEMINI_API_KEY)}")

client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🥗 Я помогу узнать БЖУ и калорийность продуктов.\n\n"
        "Просто напиши название продукта — например: *курица* или *курица 150г*",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    await update.message.reply_text("⏳ Считаю...")

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

Коротко, без лишнего текста.
"""

    try:
        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как пользоваться:\n\n"
        "• Напиши название продукта → получишь БЖУ на 100г\n"
        "• Напиши продукт + граммы → получишь БЖУ на эту порцию\n\n"
        "Примеры:\n"
        "  *гречка*\n"
        "  *куриная грудка 200г*\n"
        "  *творог 5% 150г*",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен...")
app.run_polling()
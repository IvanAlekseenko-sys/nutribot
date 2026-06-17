from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from dotenv import load_dotenv
import os
import logging
from collections import defaultdict
from time import time

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not set")
    raise ValueError("TELEGRAM_TOKEN environment variable is required")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set")
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=GEMINI_API_KEY)

RATE_LIMIT_SECONDS = 5
MAX_MESSAGE_LENGTH = 500
user_last_request = defaultdict(float)


def check_rate_limit(user_id: int) -> bool:
    now = time()
    if now - user_last_request[user_id] < RATE_LIMIT_SECONDS:
        return False
    user_last_request[user_id] = now
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User %s started the bot", update.effective_user.id)
    await update.message.reply_text(
        "Привет! 🥗 Я помогу узнать БЖУ и калорийность продуктов.\n"
        "Просто напиши название продукта — например: *курица* или *курица 150г*\n\n"
        "Hi! 🥗 I can help you find nutrition info.\n"
        "Just type a product name — e.g. *chicken* or *chicken 150g*",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("❌ Пустое сообщение / Empty message")
        return

    if len(text) > MAX_MESSAGE_LENGTH:
        await update.message.reply_text(
            f"❌ Сообщение слишком длинное (макс. {MAX_MESSAGE_LENGTH} символов) / "
            f"Message too long (max {MAX_MESSAGE_LENGTH} characters)"
        )
        return

    if not check_rate_limit(user_id):
        await update.message.reply_text(
            "⏳ Подожди немного перед следующим запросом / Wait before next request"
        )
        return

    logger.info("User %s: %s", user_id, text)

    await update.message.reply_text("⏳ Считаю... / Calculating...")

    prompt = f"""
You are a nutrition assistant. The user wrote: "{text}"

First check: is this actually a food or drink?
- If it is NOT a food (e.g. dinosaur, car, person, fictional creature) — reply only with:
 "❌ This is not a food item / Это не продукт питания. Please enter a food or drink name / Напиши название еды или напитка."

If it IS a food, follow these rules:
- If the input contains a number — use it as the portion size, BUT maximum allowed is 5000g or 5000ml. If the number exceeds 5000, reply only with:
 "❌ Portion too large / Слишком большая порция. Please enter a value up to 5000g / Введи значение до 5000г."
- If no number — use 100g or 100ml depending on product type
- For liquids (milk, juice, soup, drinks) use ml
- For solid foods use g

Always reply in this exact format:
🍽 Product / Продукт: [name]
⚖️ Portion / Порция: [amount]g or [amount]ml

🔥 Calories / Калории: [number] kcal
💪 Protein / Белки: [number]g
🧈 Fat / Жиры: [number]g
🍞 Carbs / Углеводы: [number]g

Short reply, no extra text.
"""

    try:
        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
        reply = response.text.strip()

        if len(reply) > 4000:
            reply = reply[:4000] + "\n\n⚠️ Ответ обрезан / Response truncated"

        await update.message.reply_text(reply)
        logger.info("Response sent to user %s", user_id)

    except Exception as e:
        error_str = str(e)
        logger.error("Gemini API error for user %s: %s", user_id, error_str)

        if "429" in error_str:
            await update.message.reply_text(
                "⏳ Слишком много запросов, попробуй через минуту. / Too many requests, try again in a minute."
            )
        elif "API_KEY_INVALID" in error_str or "401" in error_str:
            await update.message.reply_text(
                "❌ Ошибка API ключа. Свяжитесь с администратором. / API key error. Contact admin."
            )
        elif "503" in error_str or "UNAVAILABLE" in error_str:
            await update.message.reply_text(
                "⏳ Сервис временно недоступен, попробуй позже. / Service temporarily unavailable."
            )
        else:
            await update.message.reply_text(
                "❌ Что-то пошло не так, попробуй ещё раз. / Something went wrong, please try again."
            )


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


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()

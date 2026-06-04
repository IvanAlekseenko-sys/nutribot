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
You are a nutrition assistant. The user wrote: "{text}"

Rules:
- Detect the language of the user's input and respond in that exact language
- If the input contains a number (e.g. 150, 150g, 150ml, 150 grams) — use it as the portion size
- If no number — use 100g or 100ml depending on product type
- For liquids (milk, juice, soup, drinks) use ml
- For solid foods use g

Reply STRICTLY in this format (translate field names to the user's language):
🍽 Product: [name]
⚖️ Portion: [amount]g or [amount]ml

🔥 Calories: [number] kcal
💪 Protein: [number]g
🧈 Fat: [number]g
🍞 Carbs: [number]g

Short reply, no extra text.
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
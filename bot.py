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
           reply = reply[:4000] + "..."
       await update.message.reply_text(reply)
   except Exception as e:
       error_str = str(e)
       if "429" in error_str:
           await update.message.reply_text("⏳ Слишком много запросов, попробуй через минуту. / Too many requests, try again in a minute.")
       else:
           await update.message.reply_text("❌ Что-то пошло не так, попробуй ещё раз. / Something went wrong, please try again.")

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

print("Бот запущен... / Bot started...")
app.run_polling()

#BOT_TOKEN = "7676108205:AAF9oKzkm8IiM28QdXDMstBEzjrstvI9pXc"
import warnings
import sys
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# Suppress scheduler warnings
warnings.filterwarnings("ignore", category=UserWarning, module="apscheduler")

# Add root path so we can import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import claim detection + fact-check search
from model.claim_detector import is_potential_fake
from api.fact_check_api import search_fact_check

# 🔐 Bot Token (get from environment variable for security)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7676108205:AAF9oKzkm8IiM28QdXDMstBEzjrstvI9pXc")

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to AI Fact Checker. Send me a message to verify it!")

# Fact-check handler
async def fact_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    if not user_message:
        await update.message.reply_text("❗ Please send a text message.")
        return

    # 🧠 Run model prediction
    prediction = is_potential_fake(user_message)
    label = prediction["label"]
    score = round(prediction["score"] * 100, 2)

    # 🔎 Run fact-check API
    fact_info = search_fact_check(user_message)

    # Map label to status message
    if label.upper() == "FAKE":
        status = "⚠️ *Fake News Detected!*"
    elif label.upper() == "REAL":
        status = "✅ *Likely Real Information*"
    else:
        status = "❔ *Uncertain - Needs Verification*"

    confidence = f"📊 *Confidence Score:* {score}%"

    if fact_info:
        fact_summary = f"📰 _Fact-check Summary:_\n{fact_info}"
    else:
        fact_summary = "_No official fact-check found._"

    # Combine into final reply
    reply = f"{status}\n{confidence}\n\n{fact_summary}"

    # Escape Markdown for Telegram
    escaped_reply = escape_markdown(reply, version=2)

    await update.message.reply_text(escaped_reply, parse_mode=ParseMode.MARKDOWN_V2)

# Main function
def run_bot():
    if BOT_TOKEN == "7676108205:AAF9oKzkm8IiM28QdXDMstBEzjrstvI9pXc":
        print("❌ BOT_TOKEN not set. Please set TELEGRAM_BOT_TOKEN in environment.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fact_check))

    print("✅ Telegram bot is running...")
    app.run_polling()

# Run bot
if __name__ == "__main__":
    run_bot()

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='apscheduler')
from telegram.constants import ParseMode
...
# update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from model.claim_detector import is_potential_fake
from api.fact_check_api import search_fact_check

BOT_TOKEN = "7676108205:AAF9oKzkm8IiM28QdXDMstBEzjrstvI9pXc"

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to AI Fact Checker. Send me a message to verify it!")
from telegram.constants import ParseMode  
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from model.claim_detector import is_potential_fake
# from model.fact_checker import search_fact_check

from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from model.claim_detector import is_potential_fake  
from api.fact_check_api import search_fact_check

async def fact_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    if not user_message:
        await update.message.reply_text("❗ Please send a text message.")
        return

    # 🧠 Get prediction and score
    prediction = is_potential_fake(user_message)  
    label = prediction['label']
    score = round(prediction['score'] * 100, 2)  

   
    fact_info = search_fact_check(user_message)

    if label.upper() == "FAKE":
        status = f"⚠️ *Fake News Detected!*"
    else:
        status = f"✅ *Likely Real Information*"

    confidence = f"📊 *Confidence Score:* {score}%"

    if fact_info:
        fact_summary = f"📰 _Fact-check Summary:_\n{fact_info}"
    else:
        fact_summary = "_No official fact-check found._"

    # 🧾 Final reply
    reply = f"{status}\n{confidence}\n\n{fact_summary}"

    # ✅ Escape for Markdown V2
    escaped_reply = escape_markdown(reply, version=2)

    await update.message.reply_text(escaped_reply, parse_mode=ParseMode.MARKDOWN_V2)





# Main function to run bot
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fact_check))

    print("✅ Telegram bot is running...")
    app.run_polling()

# Run bot when script is executed
if __name__ == "__main__":
    run_bot()

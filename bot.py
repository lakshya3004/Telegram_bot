import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from model.claim_detector import is_potential_fake
import wikipediaapi

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='ai-fact-checker-bot/1.0 (https://github.com/yourusername/yourrepo)'
)
def check_wikipedia_claim(claim: str) -> str:
    """
    Check a claim against Wikipedia and return:
    'real', 'maybe real', 'fake', 'maybe fake'
    """
    words = claim.split()
    for word in words:
        page = wiki_wiki.page(word)
        if page.exists():
            # If any claim word appears in summary, mark as real
            if any(w.lower() in page.summary.lower() for w in words):
                return "real"
    return "maybe fake"

# Your Telegram Bot token
BOT_TOKEN = "7676108205:AAF9oKzkm8IiM28QdXDMstBEzjrstvI9pXc"

# Build Telegram application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me text to check if it's fake news.")

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    # Step 1: Model prediction
    result = is_potential_fake(user_text)
    pred = result["prediction"]  # 'fake' or 'real'
    conf = result["confidence"]  # 0.0 to 1.0

    # Step 2: Wikipedia fact-check
    wiki_pred = check_wikipedia_claim(user_text)

    # Step 3: Combine model + Wikipedia results
    if wiki_pred == "real":
        final_pred = "real"
    else:
        if pred == "fake":
            final_pred = "fake" if conf > 0.85 else "maybe fake"
        elif pred == "real":
            final_pred = "real" if conf > 0.85 else "maybe real"
        else:
            final_pred = "maybe"

    # Step 4: Reply
    reply_text = f"Prediction: *{final_pred}*\nConfidence: {conf:.2f}"
    await update.message.reply_text(reply_text, parse_mode="Markdown")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Run bot
if __name__ == "__main__":
    application.run_polling()

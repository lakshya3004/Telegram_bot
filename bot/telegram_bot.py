import os
import warnings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.helpers import escape_markdown
import wikipediaapi
from sentence_transformers import SentenceTransformer, util
from model.claim_detector import is_potential_fake
from api.fact_check_api import search_fact_check
from serpapi import GoogleSearch

# -----------------------
# Suppress warnings
# -----------------------
warnings.filterwarnings("ignore", category=UserWarning, module="apscheduler")

# -----------------------
# Load environment variables
# -----------------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set in environment variables")
    exit()

if not SERPAPI_API_KEY:
    print("❌ SERPAPI_API_KEY not set in environment variables")
    # You can choose to continue without web search

# -----------------------
# Initialize Wikipedia API
# -----------------------
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='ai-fact-checker-bot/1.0 (https://github.com/yourusername/yourrepo)'
)

# -----------------------
# Semantic similarity model
# -----------------------
sim_model = SentenceTransformer('all-MiniLM-L6-v2')

# -----------------------
# Helper: Wikipedia check
# -----------------------
def check_wikipedia_claim(claim: str) -> str:
    """Check a claim against Wikipedia and return real/maybe real/maybe fake."""
    page = wiki_wiki.page(claim)
    if page.exists():
        return "real"
    # fallback: check individual words
    for word in claim.split():
        page = wiki_wiki.page(word)
        if page.exists():
            return "maybe real"
    return "maybe fake"

# -----------------------
# Helper: Google search for web verification
# -----------------------
def search_web_articles(query: str, num_results: int = 5):
    if not SERPAPI_API_KEY:
        return []

    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
        "num": num_results,
        "hl": "en"
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        articles = []

        for item in results.get("organic_results", []):
            articles.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "url": item.get("link")
            })
        return articles
    except Exception as e:
        print(f"Error fetching web articles: {e}")
        return []

# -----------------------
# Start command
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to AI Fact Checker Bot!\nSend me a news/article text to verify."
    )

# -----------------------
# Fact-check handler
# -----------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text:
        await update.message.reply_text("❗ Please send some text to check.")
        return

    # 1️⃣ Model prediction
    model_result = is_potential_fake(user_text)
    model_pred = model_result["prediction"]
    model_conf = model_result["confidence"]

    # 2️⃣ Wikipedia check
    wiki_pred = check_wikipedia_claim(user_text)

    # 3️⃣ Multi-source fact-check (optional API)
    fact_results = []
    try:
        api_fact = search_fact_check(user_text)
        if api_fact:
            fact_results.append(f"📰 *Official Fact Check:* {api_fact}")
    except Exception:
        pass

    # 4️⃣ Web search + semantic similarity
    claim_emb = sim_model.encode(user_text)
    for article in search_web_articles(user_text, num_results=5)[:3]:
        article_emb = sim_model.encode(article["snippet"])
        similarity = util.cos_sim(claim_emb, article_emb).item()
        if similarity > 0.65:
            fact_results.append(
                f"📰 *Web Article:* {article['title']} ({similarity*100:.1f}% match)\n{article['url']}"
            )

    # 5️⃣ Combine Wikipedia + Model + Web sources for final label
    if wiki_pred == "real":
        final_label = "real"
    else:
        if model_pred.lower() == "fake":
            final_label = "fake" if model_conf > 0.8 else "maybe fake"
        elif model_pred.lower() == "real":
            final_label = "real" if model_conf > 0.8 else "maybe real"
        else:
            final_label = "maybe"

    # 6️⃣ Confidence display
    combined_conf = min(1.0, model_conf + len(fact_results)*0.1)

    # 7️⃣ Prepare reply (Markdown-safe)
    reply_text = f"*Prediction:* {escape_markdown(final_label, version=2)}\n*Confidence:* {combined_conf:.2f}"
    if fact_results:
        reply_text += "\n\n" + "\n\n".join([escape_markdown(fr, version=2) for fr in fact_results])

    await update.message.reply_text(reply_text, parse_mode="MarkdownV2")

# -----------------------
# Build application
# -----------------------
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -----------------------
# Run bot
# -----------------------
if __name__ == "__main__":
    print("✅ AI Fact Checker Bot is running...")
    application.run_polling()

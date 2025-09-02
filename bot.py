import os
import warnings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import wikipediaapi
from sentence_transformers import SentenceTransformer, util
from model.claim_detector import is_potential_fake
from api.fact_check_api import search_fact_check
from serpapi import GoogleSearch
from transformers import pipeline

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

# -----------------------
# Initialize Wikipedia API
# -----------------------
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='ai-fact-checker-bot/1.0'
)

# -----------------------
# Semantic similarity model
# -----------------------
sim_model = SentenceTransformer('all-MiniLM-L6-v2')

# -----------------------
# Summarization pipeline
# -----------------------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_text(text, max_length=100):
    try:
        summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text

# -----------------------
# Telegram max message length
# -----------------------
MAX_TELEGRAM_MESSAGE_LENGTH = 4000

async def send_long_message(update, text):
    for i in range(0, len(text), MAX_TELEGRAM_MESSAGE_LENGTH):
        await update.message.reply_text(text[i:i + MAX_TELEGRAM_MESSAGE_LENGTH])

# -----------------------
# Helper: Wikipedia check
# -----------------------
def check_wikipedia_claim(claim: str) -> str:
    page = wiki_wiki.page(claim)
    if page.exists():
        return "Real"
    for word in claim.split():
        page = wiki_wiki.page(word)
        if page.exists():
            return "Maybe Real"
    return "Maybe False"

# -----------------------
# Helper: Google search
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
            title = item.get("title")
            snippet = item.get("snippet")
            url = item.get("link")
            articles.append(f"{title}\n{snippet}\nLink: {url}")
        return articles
    except Exception as e:
        print(f"Error fetching web articles: {e}")
        return []

# -----------------------
# Start command
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to AI Fact Checker Bot! Send me any news/article text to verify."
    )

# -----------------------
# Fact-check handler
# -----------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text:
        await update.message.reply_text("❗ Please send some text to check.")
        return

    # Model prediction
    model_result = is_potential_fake(user_text)
    model_pred = model_result["prediction"].lower()
    model_conf = model_result["confidence"]

    if model_pred == "fake":
        model_label = "False" if model_conf > 0.8 else "Maybe False"
    elif model_pred == "real":
        model_label = "True" if model_conf > 0.8 else "Maybe True"
    else:
        model_label = "Not Sure"

    # Wikipedia check
    wiki_label = check_wikipedia_claim(user_text)

    # Official fact-check
    top_fact = None
    try:
        api_fact = search_fact_check(user_text)
        if api_fact:
            claim_review = api_fact[0].get('claimReview', [{}])[0]
            publisher = claim_review.get('publisher', {}).get('name', '')
            title = claim_review.get('title', '')
            url = claim_review.get('url', '')
            textual_rating = claim_review.get('textualRating', '')
            top_fact = f"{title} ({publisher})\nLink: {url}\nRating: {textual_rating}"
    except Exception:
        pass

    # Web search + semantic similarity + summarization
    claim_emb = sim_model.encode(user_text)
    web_sources = []
    for article_text in search_web_articles(user_text, num_results=5)[:5]:
        snippet_emb = sim_model.encode(article_text)
        similarity = util.cos_sim(claim_emb, snippet_emb).item()
        if similarity > 0.7:
            summarized = summarize_text(article_text)
            web_sources.append((similarity, summarized))

    # Take top 2 web sources
    web_sources = [text for sim, text in sorted(web_sources, reverse=True)[:2]]

    # Final prediction logic
    if top_fact:
        final_label = "False" if "false" in top_fact.lower() else "True"
    elif wiki_label == "Real":
        final_label = "True"
    elif wiki_label == "Maybe Real":
        final_label = model_label
    else:
        final_label = model_label

    # Prepare reply
    reply_text = f"Prediction: {final_label}\n"
    reply_text += f"Model Prediction: {model_label} (Confidence: {model_conf:.2f})\n"
    reply_text += f"Wikipedia Check: {wiki_label}\n"
    if top_fact:
        reply_text += f"\nOfficial Fact-Check:\n{top_fact}\n"
    if web_sources:
        reply_text += "\nTop Web Sources:\n" + "\n\n".join(web_sources)

    reply_text += f"\n\nFinal Verdict: Based on model, Wikipedia, official fact-check, and top web sources, the above claim is most likely {final_label}."

    await send_long_message(update, reply_text)

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

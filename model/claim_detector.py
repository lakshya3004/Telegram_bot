from transformers import pipeline
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

from api.fact_check_api import search_fact_check
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load model
classifier = pipeline("text-classification", model="Pulk17/Fake-News-Detection")

# Map model labels to human-readable outputs
label_mapping = {
    "LABEL_0": "fake",
    "LABEL_1": "real",
    "LABEL_2": "not sure, check again from verified sources"  
}

def is_potential_fake(text: str) -> dict:
    result = classifier(text)[0]
    human_label = label_mapping.get(result["label"], "unknown")  # map LABEL_X to real/fake/maybe
    return {
        "prediction": human_label,
        "confidence": round(float(result["score"]), 4)
    }

if __name__ == "__main__":
    text = input("Enter news/article text: ")
    output = is_potential_fake(text)
    print(output)

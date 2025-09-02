from transformers import pipeline
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import escape_markdown

# claim_detector.py
from transformers import pipeline

# Load transformer model
classifier = pipeline("text-classification", model="Pulk17/Fake-News-Detection")

# Map model labels to human-readable outputs
label_mapping = {
    "LABEL_0": "FAKE",
    "LABEL_1": "REAL",
    "LABEL_2": "UNCERTAIN"
}

def is_potential_fake(text: str) -> dict:
    """
    Predict whether the input text is likely fake, real, or uncertain.
    Returns prediction and confidence score.
    """
    result = classifier(text)[0]
    human_label = label_mapping.get(result["label"], "UNCERTAIN")
    return {
        "prediction": human_label,
        "confidence": float(result["score"])
    }

if __name__ == "__main__":
    text = input("Enter news/article text: ")
    output = is_potential_fake(text)
    print(output)

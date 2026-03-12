import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

# --- Keyword Maps ---
CATEGORY_KEYWORDS = {
    "Technical": ["app", "lag", "crash", "bug", "error", "slow", "login", "loading",
                  "freeze", "glitch", "down", "offline", "network", "server", "update"],
    "Pricing":   ["price", "expensive", "cost", "cheap", "billing", "invoice",
                  "subscription", "refund", "payment", "fee", "charge"],
    "Support":   ["support", "help", "service", "staff", "team", "response",
                  "reply", "agent", "customer", "waiting", "ignored"],
    "Features":  ["feature", "design", "ui", "interface", "layout", "dashboard",
                  "button", "option", "missing", "wish", "would be nice", "add"],
}

HIGH_URGENCY_KEYWORDS = ["crash", "down", "urgent", "critical", "broken",
                          "cannot login", "login", "app lag", "not working",
                          "emergency", "serious", "major", "fail", "error"]

MEDIUM_URGENCY_KEYWORDS = ["slow", "issue", "problem", "bug", "glitch",
                            "disappointing", "frustrated", "bad", "wrong"]


def clean_text(text: str) -> str:
    """Remove URLs, emojis, and extra whitespace."""
    text = re.sub(r"http\S+|www\S+", "", text)          # remove URLs
    text = re.sub(r"[^\x00-\x7F]+", "", text)           # remove non-ASCII (emojis)
    text = re.sub(r"\s+", " ", text).strip()             # collapse whitespace
    return text


def get_sentiment(text: str) -> tuple[str, float]:
    """Return (label, compound_score) using VADER."""
    scores = analyzer.polarity_scores(text)
    compound = round(scores["compound"], 4)
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return label, compound


def get_category(text: str) -> str:
    """Classify feedback into a category based on keywords."""
    lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return "General"


def get_urgency(text: str) -> str:
    """Flag urgency level based on keywords."""
    lower = text.lower()
    if any(kw in lower for kw in HIGH_URGENCY_KEYWORDS):
        return "High"
    if any(kw in lower for kw in MEDIUM_URGENCY_KEYWORDS):
        return "Medium"
    return "Low"


def analyze(text: str, source: str) -> dict:
    """Full analysis pipeline: clean → sentiment → category → urgency."""
    cleaned = clean_text(text)
    sentiment, score = get_sentiment(cleaned)
    category = get_category(cleaned)
    urgency = get_urgency(cleaned)

    return {
        "source":    source,
        "text":      cleaned,
        "sentiment": sentiment,
        "score":     score,
        "category":  category,
        "urgency":   urgency,
    }


if __name__ == "__main__":
    samples = [
        ("The app keeps crashing and I cannot login at all!", "Twitter"),
        ("Really loving the new dashboard design, great work team!", "Survey"),
        ("The pricing is way too expensive for what you get.", "Facebook"),
        ("Support team responded quickly and solved my problem.", "Survey"),
    ]
    for text, source in samples:
        result = analyze(text, source)
        print(result)

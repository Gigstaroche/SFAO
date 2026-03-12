"""
SFAO - Social Media Feed Simulator
Sends realistic mock feedback to the FastAPI backend.
Usage: python scripts/simulator.py
"""

import random
import time
import json
import urllib.request
import urllib.error

API_URL = "http://localhost:8000/ingest"

SOURCES = ["Twitter", "Facebook", "Instagram", "LinkedIn", "Reddit"]

SAMPLES = [
    # Technical - Negative
    ("The app keeps crashing every time I try to open it!", "Twitter"),
    ("Cannot login at all today. This is unacceptable.", "Facebook"),
    ("App lag is really bad during peak hours, very frustrating.", "Twitter"),
    ("Server error 500 on the dashboard. Is it down?", "Reddit"),
    ("The loading screen just freezes and never loads.", "Instagram"),
    # Technical - Positive
    ("New update fixed the login bug. Much faster now!", "Twitter"),
    ("The dashboard loads instantly today. Great improvement!", "LinkedIn"),
    # Pricing - Negative
    ("The subscription is way too expensive for small businesses.", "Facebook"),
    ("Hidden charges on my billing statement. Not happy.", "Twitter"),
    ("Competitors offer the same features at half the price.", "Reddit"),
    # Pricing - Positive
    ("The pricing is fair for what you get. Worth it!", "LinkedIn"),
    # Support - Positive
    ("Customer support resolved my issue in under 10 minutes. Excellent!", "Twitter"),
    ("The support team is so helpful and professional.", "Facebook"),
    ("Shoutout to the support team, very responsive!", "Instagram"),
    # Support - Negative
    ("Been waiting 3 days for a response from support. Ridiculous.", "Twitter"),
    ("Support agent was rude and dismissed my issue.", "Facebook"),
    # Features - Positive
    ("Love the new dashboard design! Very intuitive UI.", "Instagram"),
    ("The new export feature is exactly what I needed.", "LinkedIn"),
    ("Really impressed with the latest feature rollout.", "Twitter"),
    # Features - Negative
    ("Wish there was a dark mode option. Basic feature missing.", "Reddit"),
    ("The mobile interface is really hard to use.", "Instagram"),
    # General - Positive
    ("Overall great product. Highly recommend to other businesses!", "LinkedIn"),
    ("Very satisfied with the platform so far.", "Facebook"),
    # General - Negative
    ("Disappointed with recent changes. Feels like a step backward.", "Twitter"),
    ("Not what I expected based on the marketing.", "Facebook"),
]


def post(source, text):
    payload = json.dumps({"source": source, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"[{source}] {data['sentiment']:8s} | {data['category']:10s} | {data['urgency']:6s} | {text[:60]}")
    except urllib.error.URLError as e:
        print(f"[ERROR] Cannot reach API: {e.reason}. Is the backend running?")
        return False
    return True


def run(count=20, delay=1.5):
    print("=" * 70)
    print("  SFAO Social Media Simulator")
    print("=" * 70)
    print(f"Sending {count} simulated feedback entries...\n")
    for i in range(count):
        text, suggested_source = random.choice(SAMPLES)
        source = random.choice(SOURCES)
        ok = post(source, text)
        if not ok:
            print("Stopping simulator.")
            break
        time.sleep(delay)
    print("\nSimulation complete.")


if __name__ == "__main__":
    run(count=20, delay=1.0)

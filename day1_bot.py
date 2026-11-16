# ☕ Day 1 bot - Kopi Uncle with if/else rules (no AI yet)
#
#   In Codespaces:  python day1_bot.py   (Ctrl + C to stop)
#   On Vercel:      Vercel runs the `app` in part 5 for you
#
# Telegram lets a bot use ONE of these at a time:
#   polling = we keep asking Telegram for new messages (part 6)
#   webhook = Telegram sends each new message to our web app (part 5)

import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header

# ----- 1. Settings: keys from your .env file (or Vercel settings) -----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")


# ----- 2. The brain: your rules (notebook 04) -----
prices = {
    "kopi": 1.40,
    "kopi-o": 1.20,
    "kopi-c": 1.50,
    "teh": 1.40,
    "teh-o": 1.20,
    "teh-c": 1.50,
    "milo": 1.80,
}


def reply(text, name):
    text = text.lower().strip()

    if text in ["/start", "hi", "hello"]:
        return f"Hello {name}! Uncle here. Type 'menu' to see what we have."

    if text == "menu":
        lines = [f"{drink.title()}: ${price:.2f}" for drink, price in prices.items()]
        return "Today's menu:\n" + "\n".join(lines)

    # check longer names first, so "kopi-o" isn't mistaken for "kopi"
    for drink in sorted(prices, key=len, reverse=True):
        if drink in text:
            return f"One {drink.title()} coming up! That's ${prices[drink]:.2f}."

    return "Aiyo, Uncle don't understand. Type 'menu' lah."


# ----- 3. Talking to Telegram (notebook 03) -----
def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text})


# ----- 4. One message in, one reply out -----
def handle_update(update):
    message = update.get("message", {})
    if "text" not in message:
        return   # skip stickers, photos...

    chat_id = message["chat"]["id"]
    name = message["from"]["first_name"]
    text = message["text"]

    answer = reply(text, name)
    send_message(chat_id, answer)
    print(f"{name}: {text}  ->  {answer}")


# ----- 5. Webhook: the web app Vercel runs -----
# Telegram sends every new message here, instead of us asking for it
app = FastAPI()


@app.get("/")
def home():
    return {"status": "Kopi Uncle is running!"}


@app.post("/webhook")
def webhook(update: dict, x_telegram_bot_api_secret_token: str = Header("")):
    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        return {"ok": False}   # not from Telegram - ignore it
    handle_update(update)
    return {"ok": True}


# ----- 6. Polling: runs only when you type `python day1_bot.py` -----
if __name__ == "__main__":
    requests.post(f"{BASE}/deleteWebhook")   # switch Telegram from webhook to polling
    print("Bot is running... message it on Telegram!")

    offset = None   # which messages we've already handled
    while True:
        params = {"offset": offset, "timeout": 30}   # wait up to 30s for new messages
        for update in requests.get(f"{BASE}/getUpdates", params=params).json()["result"]:
            offset = update["update_id"] + 1   # don't handle this one again
            handle_update(update)

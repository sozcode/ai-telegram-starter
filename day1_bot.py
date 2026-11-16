# ☕ Day 1 bot - Kopi Uncle with if/else rules (no AI yet)
#
#   Run it:   python day1_bot.py
#   Stop it:  Ctrl + C   (you'll see "KeyboardInterrupt" - that's normal)

import os

import requests
from dotenv import load_dotenv

# ----- 1. Settings: your bot token from the .env file -----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"


# ----- 2. The brain: your rules -----
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


# ----- 3. Talking to Telegram -----
def get_updates(offset):
    # timeout 30 = Telegram waits up to 30 seconds for a new message
    params = {"offset": offset, "timeout": 30}
    return requests.get(f"{BASE}/getUpdates", params=params).json()["result"]


def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text})


# ----- 4. Go live: ask, decide, reply, repeat forever -----
print("Bot is running... message it on Telegram!")

offset = None   # which messages we've already handled
while True:
    for update in get_updates(offset):
        offset = update["update_id"] + 1   # don't handle this one again

        message = update.get("message", {})
        if "text" not in message:
            continue   # skip stickers, photos...

        chat_id = message["chat"]["id"]
        name = message["from"]["first_name"]
        text = message["text"]

        answer = reply(text, name)
        send_message(chat_id, answer)
        print(f"{name}: {text}  ->  {answer}")

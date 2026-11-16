# ☕ Day 2 bot - Kopi Uncle, an AI agent on Telegram
#
#   In Codespaces:  python main.py   (Ctrl + C to stop)
#   On Vercel:      Vercel runs the `app` in part 6 for you
#
# Read it top to bottom - each part matches a notebook.

import os

import pandas as pd
import requests
from agents import Agent, ModelSettings, OpenAIConversationsSession, Runner, function_tool
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from supabase import create_client


# ----- 1. Settings: keys from your .env file (or Vercel settings) -----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

db = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SECRET_KEY"))


# ----- 2. Tools: things the agent can do (notebook 06) -----
menu = pd.read_csv("menu.csv")
prices = dict(zip(menu["item"].str.lower(), menu["price"]))   # {"kopi": 1.4, "teh": 1.4, ...}


@function_tool
def get_menu() -> str:
    """Get the kopitiam menu with prices."""
    return menu.to_string(index=False)


@function_tool
def calculate_bill(items: list[str]) -> str:
    """Add up the bill. List every item separately using menu names,
    e.g. ["Kopi-O Peng", "Kopi-O Peng", "Kaya Toast Set"]. Add ' Peng' for iced drinks."""
    total = 0
    for item in items:
        item = item.lower()
        if item.endswith(" peng"):
            total = total + 0.30   # iced costs 30 cents more
            item = item.replace(" peng", "")
        total = total + prices.get(item, 0)
    return f"Total: ${total:.2f}"


@function_tool
def get_weather(area: str) -> str:
    """Get the live weather forecast for a Singapore area, e.g. 'Bedok' or 'City'."""
    data = requests.get("https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast").json()
    for forecast in data["data"]["items"][0]["forecasts"]:
        if area.lower() in forecast["area"].lower():
            return f"{forecast['area']}: {forecast['forecast']}"
    return f"No area called {area}"


# ----- 3. The agent: personality + model + tools (notebook 05) -----
uncle = Agent(
    name="Kopi Uncle",
    instructions="""You are Kopi Uncle, a friendly kopitiam uncle in Singapore chatting on Telegram.
Speak light Singlish. Keep replies short, 1-4 lines.
ALWAYS use get_menu for prices and calculate_bill for totals. Never guess a price.
'Peng' means iced. If someone asks what to drink, check the weather first.
Only talk about food, drinks and the weather. Politely decline anything else.""",
    model=os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
    model_settings=ModelSettings(reasoning={"effort": "low"}),   # low = faster replies
    tools=[get_menu, calculate_bill, get_weather],
)


# ----- 4. Memory: save each chat's conversation ID in Supabase (notebooks 07-08) -----
def get_conversation_id(chat_id):
    rows = db.table("chats").select("conversation_id").eq("chat_id", chat_id).execute().data
    if rows:
        return rows[0]["conversation_id"]
    return None   # a new customer


def save_conversation_id(chat_id, conversation_id):
    db.table("chats").upsert({"chat_id": chat_id, "conversation_id": conversation_id}).execute()


def save_message(chat_id, name, role, text):
    db.table("messages").insert({"chat_id": chat_id, "user_name": name, "role": role, "text": text}).execute()


# ----- 5. One message in, one reply out -----
def ask_uncle(chat_id, text):
    session = OpenAIConversationsSession(conversation_id=get_conversation_id(chat_id))
    result = Runner.run_sync(uncle, text, session=session)
    save_conversation_id(chat_id, session.session_id)
    return result.final_output


def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text})


def handle_update(update):
    message = update.get("message", {})
    if "text" not in message:
        return   # skip stickers, photos...

    chat_id = message["chat"]["id"]
    name = message["from"]["first_name"]
    text = message["text"]

    answer = ask_uncle(chat_id, text)
    send_message(chat_id, answer)
    save_message(chat_id, name, "user", text)
    save_message(chat_id, name, "bot", answer)
    print(f"{name}: {text}  ->  {answer}")


# ----- 6. Online 24/7: the web app Vercel runs (notebook 09) -----
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


# ----- 7. Polling: runs only when you type `python main.py` (same loop as Day 1) -----
if __name__ == "__main__":
    requests.post(f"{BASE}/deleteWebhook")   # Telegram allows webhook OR polling, not both
    print("Bot is running... message it on Telegram!")

    offset = None
    while True:
        params = {"offset": offset, "timeout": 30}
        for update in requests.get(f"{BASE}/getUpdates", params=params).json()["result"]:
            offset = update["update_id"] + 1
            handle_update(update)

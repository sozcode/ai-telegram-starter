# 🇸🇬 Day 2 bot - SG Data Bot, an AI assistant on Telegram (OpenAI Responses API)
#
#   In Codespaces:  python main.py   (Ctrl + C to stop)
#   On Vercel:      Vercel runs the `app` in part 6 for you
#
# One bot, one person chatting with it, text messages only.
# Read top to bottom - each part matches a notebook.

import json
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from openai import OpenAI

# ----- 1. Settings: keys and IDs from your .env file (or Vercel settings) -----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")

client = OpenAI()   # reads OPENAI_API_KEY by itself

# Saved in notebook 08 - or made fresh here if you haven't saved them yet.
# The conversation is the bot's memory (your PDF notes are inside it, notebook 08).
CONVERSATION_ID = os.environ.get("OPENAI_CONVERSATION_ID") or client.conversations.create().id
# The HDB prices file, uploaded to OpenAI so the python tool can read it (notebook 07).
HDB_FILE_ID = os.environ.get("OPENAI_HDB_FILE_ID") or client.files.create(
    file=open("hdb_resale_prices.csv", "rb"), purpose="user_data"
).id


# ----- 2. Function tools: live data from data.gov.sg (notebook 06) -----
def get_weather(area):
    data = requests.get("https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast").json()
    for forecast in data["data"]["items"][0]["forecasts"]:
        if area.lower() in forecast["area"].lower():
            return f"{forecast['area']}: {forecast['forecast']}"
    return f"No area called {area}"


def get_air_quality():
    data = requests.get("https://api-open.data.gov.sg/v2/real-time/api/psi").json()
    psi = data["data"]["items"][0]["readings"]["psi_twenty_four_hourly"]
    return f"24-hour PSI by region: {psi}"   # under 50 = good, 51-100 = moderate


# the names the AI uses -> our Python functions
functions = {"get_weather": get_weather, "get_air_quality": get_air_quality}


# ----- 3. All the tools the bot can use (notebooks 06-07) -----
tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the live 2-hour weather forecast for a Singapore area, e.g. 'Bedok' or 'Tampines'.",
        "parameters": {
            "type": "object",
            "properties": {"area": {"type": "string"}},
            "required": ["area"],
        },
    },
    {
        "type": "function",
        "name": "get_air_quality",
        "description": "Get the live air quality (24-hour PSI) for north, south, east, west and central Singapore.",
        "parameters": {"type": "object", "properties": {}},
    },
    # OpenAI runs Python for us, with the HDB prices file ready inside
    {"type": "code_interpreter", "container": {"type": "auto", "file_ids": [HDB_FILE_ID]}},
    {"type": "web_search"},   # OpenAI searches the web for us
]

instructions = """You are SG Data Bot, a helpful assistant for life in Singapore, chatting on Telegram.
Keep replies short and in plain text (no tables or markdown).
For HDB resale prices, use the python tool to analyse hdb_resale_prices.csv
(HDB resale flats sold in the last 12 months, from data.gov.sg).
For live weather or air quality, use get_weather and get_air_quality.
Use web search for news and anything else that changes.
The user's own notes (a PDF) may be earlier in this conversation - use them when relevant."""


# ----- 4. Ask the bot: one message in, one reply out (notebooks 05-08) -----
def ask(text):
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        tools=tools,
        reasoning={"effort": "low"},          # low = faster replies
        conversation=CONVERSATION_ID,         # OpenAI remembers the chat
        input=text,
    )

    # Did the AI ask to use one of OUR functions? Run it and send back the result.
    while any(item.type == "function_call" for item in response.output):
        results = []
        for item in response.output:
            if item.type == "function_call":
                arguments = json.loads(item.arguments)
                output = functions[item.name](**arguments)
                results.append({"type": "function_call_output", "call_id": item.call_id, "output": output})
                print(f"   🔧 {item.name}({arguments})")

        response = client.responses.create(
            model=MODEL,
            instructions=instructions,
            tools=tools,
            reasoning={"effort": "low"},
            conversation=CONVERSATION_ID,
            input=results,
        )

    return response.output_text


# ----- 5. Telegram: text in, text out (notebook 03) -----
def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text[:4096]})   # Telegram's limit


def handle_update(update):
    message = update.get("message", {})
    if "text" not in message:
        return   # text only for now - skip photos, stickers...

    chat_id = message["chat"]["id"]
    text = message["text"]

    answer = ask(text)
    send_message(chat_id, answer)
    print(f"You: {text}\nBot: {answer}\n")


# ----- 6. Webhook: the web app Vercel runs (notebook 09) -----
# Telegram sends every new message here, instead of us asking for it
app = FastAPI()


@app.get("/")
def home():
    return {"status": "SG Data Bot is running!"}


@app.post("/webhook")
def webhook(update: dict, x_telegram_bot_api_secret_token: str = Header("")):
    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        return {"ok": False}   # not from Telegram - ignore it
    handle_update(update)
    return {"ok": True}


# ----- 7. Polling: runs only when you type `python main.py` (same loop as Day 1) -----
if __name__ == "__main__":
    requests.post(f"{BASE}/deleteWebhook")   # switch Telegram from webhook to polling
    print("Bot is running... message it on Telegram!")

    offset = None
    while True:
        params = {"offset": offset, "timeout": 30}
        for update in requests.get(f"{BASE}/getUpdates", params=params).json()["result"]:
            offset = update["update_id"] + 1
            handle_update(update)

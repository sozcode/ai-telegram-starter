# ☕ Day 2 bot - Kopi Uncle, an AI agent on Telegram (OpenAI Responses API)
#
#   In Codespaces:  python main.py   (Ctrl + C to stop)
#   On Vercel:      Vercel runs the `app` in part 6 for you
#
# One bot, one person chatting with it. Read top to bottom - each part matches a notebook.

import base64
import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header
from openai import OpenAI

# ----- 1. Settings: keys from your .env file (or Vercel settings) -----
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")

client = OpenAI()   # reads OPENAI_API_KEY by itself

# Memory (notebook 08): one conversation that OpenAI stores for us.
# Save its ID as OPENAI_CONVERSATION_ID so Uncle still remembers after a restart.
CONVERSATION_ID = os.environ.get("OPENAI_CONVERSATION_ID") or client.conversations.create().id


# ----- 2. Function tools: our own Python functions (notebook 06) -----
menu = pd.read_csv("menu.csv")


def get_menu():
    return menu.to_string(index=False)


def get_weather(area):
    data = requests.get("https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast").json()
    for forecast in data["data"]["items"][0]["forecasts"]:
        if area.lower() in forecast["area"].lower():
            return f"{forecast['area']}: {forecast['forecast']}"
    return f"No area called {area}"


# the names the AI uses -> our Python functions
functions = {"get_menu": get_menu, "get_weather": get_weather}


# ----- 3. All the tools Uncle can use (notebooks 06-07) -----
tools = [
    {
        "type": "function",
        "name": "get_menu",
        "description": "Get the kopitiam menu with prices.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the live weather forecast for a Singapore area, e.g. 'Bedok' or 'City'.",
        "parameters": {
            "type": "object",
            "properties": {"area": {"type": "string"}},
            "required": ["area"],
        },
    },
    {"type": "web_search"},                                         # OpenAI searches the web
    {"type": "code_interpreter", "container": {"type": "auto"}},    # OpenAI runs Python code
]

instructions = """You are Kopi Uncle, a friendly kopitiam uncle in Singapore chatting on Telegram.
Speak light Singlish. Keep replies short, 1-4 lines, plain text.
Use get_menu for prices and never guess. Use the python tool to add up bills.
'Peng' means iced and costs $0.30 more. If someone asks what to drink, check the weather first.
Use web search for questions about places and news in Singapore.
If someone sends a photo or file (like a receipt), read it and help them."""


# ----- 4. Ask Uncle: one message in, one reply out (notebooks 05-08) -----
def ask_uncle(content):
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        tools=tools,
        reasoning={"effort": "low"},          # low = faster replies
        conversation=CONVERSATION_ID,         # OpenAI remembers the chat
        input=[{"role": "user", "content": content}],
    )

    # Did Uncle ask to use one of OUR functions? Run it and send back the result.
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


# ----- 5. Telegram: messages, photos and files (notebooks 03 + 07) -----
def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text})


def download(file_id):
    # Telegram gives us a file path, then we download the file and turn it into base64 text
    file_path = requests.get(f"{BASE}/getFile", params={"file_id": file_id}).json()["result"]["file_path"]
    data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file_path}").content
    return base64.b64encode(data).decode()


def handle_update(update):
    message = update.get("message", {})
    if not any(key in message for key in ["text", "photo", "document"]):
        return   # skip stickers, voice notes...

    chat_id = message["chat"]["id"]
    text = message.get("text") or message.get("caption") or "What's this?"
    content = [{"type": "input_text", "text": text}]

    if "photo" in message:   # Telegram sends a few sizes - take the biggest one
        photo = message["photo"][-1]
        content.append({"type": "input_image", "image_url": "data:image/jpeg;base64," + download(photo["file_id"])})

    if "document" in message:   # a file, e.g. a PDF receipt
        doc = message["document"]
        content.append({
            "type": "input_file",
            "filename": doc["file_name"],
            "file_data": f"data:{doc['mime_type']};base64," + download(doc["file_id"]),
        })

    answer = ask_uncle(content)
    send_message(chat_id, answer)
    print(f"You: {text}  ->  Uncle: {answer}")


# ----- 6. Webhook: the web app Vercel runs (notebook 09) -----
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
    requests.post(f"{BASE}/deleteWebhook")   # switch Telegram from webhook to polling
    print("Bot is running... message it on Telegram!")
    print("Conversation ID:", CONVERSATION_ID)

    offset = None
    while True:
        params = {"offset": offset, "timeout": 30}
        for update in requests.get(f"{BASE}/getUpdates", params=params).json()["result"]:
            offset = update["update_id"] + 1
            handle_update(update)

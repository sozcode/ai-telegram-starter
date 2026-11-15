# Talking to Telegram with plain `requests` - the same calls you made in notebook 03
import requests
from bot import config


def api_url(method):
    return f"https://api.telegram.org/bot{config.telegram_token()}/{method}"


def send_message(chat_id, text):
    # Telegram limits a message to 4096 characters
    response = requests.post(api_url("sendMessage"), json={"chat_id": chat_id, "text": text[:4096]}, timeout=15)
    return response.json()


def send_typing(chat_id):
    # Shows "typing..." while the agent thinks
    requests.post(api_url("sendChatAction"), json={"chat_id": chat_id, "action": "typing"}, timeout=10)


def get_updates(offset=None, timeout=30):
    # Long polling: Telegram waits up to `timeout` seconds for a new message
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    data = requests.get(api_url("getUpdates"), params=params, timeout=timeout + 10).json()
    if not data.get("ok"):
        # e.g. "Unauthorized" = wrong token, "Conflict" = bot is running somewhere else
        raise SystemExit(f"Telegram says: {data.get('description')}")
    return data["result"]


def set_webhook(url, secret=""):
    data = {"url": url, "allowed_updates": ["message"]}
    if secret:
        data["secret_token"] = secret
    return requests.post(api_url("setWebhook"), json=data, timeout=15).json()


def delete_webhook():
    # Needed before polling again: Telegram only allows webhook OR polling
    return requests.post(api_url("deleteWebhook"), timeout=15).json()


def get_webhook_info():
    return requests.get(api_url("getWebhookInfo"), timeout=15).json()

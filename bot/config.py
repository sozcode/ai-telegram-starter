# All settings come from environment variables (.env in Codespaces, Project Settings on Vercel)
import os
from dotenv import load_dotenv

load_dotenv()


def get(name, default=""):
    return os.environ.get(name, default).strip()


def telegram_token():
    return get("TELEGRAM_BOT_TOKEN")


def openai_ready():
    return get("OPENAI_API_KEY") != ""


def openai_model():
    return get("OPENAI_MODEL") or "gpt-6-luna"


def reasoning_effort():
    # How hard the model "thinks" before answering: none, low, medium, high
    # Low = fast replies for chat. Set OPENAI_REASONING_EFFORT=off for non-reasoning models.
    return get("OPENAI_REASONING_EFFORT") or "low"


def supabase_ready():
    return get("SUPABASE_URL") != "" and get("SUPABASE_SECRET_KEY") != ""


def webhook_secret():
    return get("WEBHOOK_SECRET")

# Deploy day: the SAME bot, but Telegram calls us (webhook) instead of us asking (polling).
# Vercel finds the `app` below automatically.
from fastapi import Body, FastAPI, Header, Request

from bot import config, memory, telegram
from bot.handler import brain, handle_update

app = FastAPI(title="Kopi Uncle")


@app.get("/")
def health():
    # Open this page in your browser to check your settings (never shows the secret values)
    status = {
        "bot": "Kopi Uncle",
        "telegram_token_set": config.telegram_token() != "",
        "brain": brain(),
        "model": config.openai_model() if brain() == "agent" else None,
        "memory": memory.mode(),
        "webhook_secret_set": config.webhook_secret() != "",
    }
    try:
        from bot.agent import kopi_uncle  # checks the agent code loads without errors
        status["agent_tools"] = [tool.name for tool in kopi_uncle.tools]
    except Exception as error:
        status["agent_error"] = str(error)
    return status


@app.post("/webhook")
def webhook(update: dict = Body(...), x_telegram_bot_api_secret_token: str = Header(default="")):
    # Telegram sends this header back to us - if it doesn't match, it's not Telegram
    if config.webhook_secret() and x_telegram_bot_api_secret_token != config.webhook_secret():
        return {"ok": False, "error": "wrong secret"}
    handle_update(update)
    return {"ok": True}  # always say OK, or Telegram keeps re-sending the message


@app.get("/setup")
def setup(request: Request):
    # Visit /setup ONCE after deploying: tells Telegram where your bot lives
    if not config.telegram_token():
        return {"ok": False, "error": "Add TELEGRAM_BOT_TOKEN in Vercel > Settings > Environment Variables, then redeploy."}
    if not config.webhook_secret():
        # Without a secret, anyone who finds your URL could make your bot spend your OpenAI credit
        return {"ok": False, "error": "Add WEBHOOK_SECRET (any random text) in Vercel > Settings > Environment Variables, then redeploy."}
    host = config.get("VERCEL_PROJECT_PRODUCTION_URL") or request.url.hostname
    url = f"https://{host}/webhook"
    result = telegram.set_webhook(url, config.webhook_secret())
    return {"webhook_url": url, "telegram_says": result}

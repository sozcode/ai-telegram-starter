# THE one function both ways of running the bot share:
#   run_polling.py (Codespaces)  ->  handle_update(update)
#   main.py        (Vercel)      ->  handle_update(update)
import traceback

from bot import config, memory, telegram
from bot.rules import reply_with_rules


def brain():
    return "agent" if config.openai_ready() else "rules"


def make_reply(chat_id, text, name):
    if text.strip().lower() == "/reset":
        memory.forget(chat_id)
        return "Okay, Uncle forget everything already. Start again!"

    if brain() == "rules":
        return reply_with_rules(text, name)

    from bot.agent import reply_with_agent  # only load the AI when we need it
    conversation_id = memory.get_conversation_id(chat_id)
    try:
        reply, new_id = reply_with_agent(text, conversation_id)
    except Exception:
        if conversation_id is None:
            raise
        # The old conversation is broken or deleted - start a fresh one
        reply, new_id = reply_with_agent(text, None)
    if new_id != conversation_id:
        memory.save_conversation_id(chat_id, new_id)
    return reply


def handle_update(update):
    message = update.get("message")
    if not message or "text" not in message:
        return None  # stickers, photos, edits... ignore for now

    chat_id = message["chat"]["id"]
    name = message["from"].get("first_name", "friend")
    text = message["text"]
    print(f"{name}: {text}")

    try:
        if brain() == "agent":
            telegram.send_typing(chat_id)
        memory.log_message(chat_id, name, "user", text)
        reply = make_reply(chat_id, text, name)
        memory.log_message(chat_id, name, "bot", reply)
    except Exception:
        traceback.print_exc()
        reply = "Aiyo, Uncle's brain got problem. Try again later."

    print(f"Bot: {reply}")
    telegram.send_message(chat_id, reply)
    return reply

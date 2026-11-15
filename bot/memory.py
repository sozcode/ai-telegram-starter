# Day 2: memory. OpenAI stores the actual chat (a "Conversation").
# We only need to remember which Telegram chat belongs to which conversation_id.
# Uses Supabase if keys are set, otherwise a Python dict.
# The dict "forgets" whenever the program restarts - that's why we need a database!
from bot import config

_memory = {}  # chat_id -> conversation_id
_client = None


def _db():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(config.get("SUPABASE_URL"), config.get("SUPABASE_SECRET_KEY"))
    return _client


def mode():
    return "supabase" if config.supabase_ready() else "in-memory"


def get_conversation_id(chat_id):
    if not config.supabase_ready():
        return _memory.get(chat_id)
    rows = _db().table("chats").select("conversation_id").eq("chat_id", chat_id).execute().data
    return rows[0]["conversation_id"] if rows else None


def save_conversation_id(chat_id, conversation_id):
    if not config.supabase_ready():
        _memory[chat_id] = conversation_id
        return
    _db().table("chats").upsert({"chat_id": chat_id, "conversation_id": conversation_id}).execute()


def forget(chat_id):
    if not config.supabase_ready():
        _memory.pop(chat_id, None)
        return
    _db().table("chats").delete().eq("chat_id", chat_id).execute()


def log_message(chat_id, user_name, role, text):
    # Every message goes into a table - great for the demo-day leaderboard
    if not config.supabase_ready():
        return
    _db().table("messages").insert(
        {"chat_id": chat_id, "user_name": user_name, "role": role, "text": text}
    ).execute()

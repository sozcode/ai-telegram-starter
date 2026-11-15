# Run with:  pytest -q
# These tests need NO keys - Telegram and OpenAI are replaced with fakes.
import pytest
from fastapi.testclient import TestClient

from bot import handler, memory, rules, telegram, tools


@pytest.fixture(autouse=True)
def no_keys(monkeypatch):
    for key in ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SECRET_KEY", "WEBHOOK_SECRET"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    memory._memory.clear()


@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(telegram, "send_message", lambda chat_id, text: messages.append((chat_id, text)))
    monkeypatch.setattr(telegram, "send_typing", lambda chat_id: None)
    return messages


def make_update(text, chat_id=111, name="Mei Ling"):
    return {"update_id": 1, "message": {"from": {"first_name": name}, "chat": {"id": chat_id}, "text": text}}


# ---- Day 1 rules ----
def test_rules_greeting():
    assert "Hello Mei Ling" in rules.reply_with_rules("/start", "Mei Ling")


def test_rules_longest_match_first():
    assert "Kopi-O" in rules.reply_with_rules("one KOPI-O please")
    assert "$1.20" in rules.reply_with_rules("one KOPI-O please")


def test_rules_unknown():
    assert "don't understand" in rules.reply_with_rules("bubble tea")


# ---- Day 2 tools ----
def test_menu_has_items():
    assert "Kaya Toast Set" in tools.menu_text()
    assert "Kaya" not in tools.menu_text("drink")


def test_bill_with_peng():
    order = [tools.OrderLine(item="kopi-o", quantity=2, iced=True), tools.OrderLine(item="Kaya Toast Set", quantity=1, iced=False)]
    bill = tools.bill_text(order)
    assert "2 x Kopi-O Peng = $3.00" in bill
    assert "TOTAL: $7.80" in bill


def test_bill_unknown_item():
    assert "not on the menu" in tools.bill_text([tools.OrderLine(item="bubble tea", quantity=1, iced=False)])


# ---- handler + memory ----
def test_handler_rules_mode(sent):
    handler.handle_update(make_update("menu"))
    assert sent[0][0] == 111
    assert "Today's menu" in sent[0][1]


def test_handler_ignores_stickers(sent):
    assert handler.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "from": {}, "sticker": {}}}) is None
    assert sent == []


def test_handler_agent_mode_remembers(monkeypatch, sent):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    calls = []

    def fake_agent(text, conversation_id):
        calls.append(conversation_id)
        return f"Uncle heard: {text}", conversation_id or "conv_1"

    import bot.agent
    monkeypatch.setattr(bot.agent, "reply_with_agent", fake_agent)

    handler.handle_update(make_update("one kopi"))
    handler.handle_update(make_update("what did I order?"))
    assert calls == [None, "conv_1"]          # 2nd message continues the same conversation
    assert memory.get_conversation_id(111) == "conv_1"

    handler.handle_update(make_update("/reset"))
    assert memory.get_conversation_id(111) is None


def test_handler_survives_errors(monkeypatch, sent):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    import bot.agent

    def broken(text, conversation_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(bot.agent, "reply_with_agent", broken)
    handler.handle_update(make_update("hello"))
    assert "brain got problem" in sent[0][1]


# ---- Vercel web app ----
def test_webhook_and_health(sent):
    from main import app
    client = TestClient(app)
    assert client.get("/").json()["brain"] == "rules"
    assert client.post("/webhook", json=make_update("hi")).json() == {"ok": True}
    assert "Hello Mei Ling" in sent[0][1]


def test_webhook_rejects_wrong_secret(monkeypatch, sent):
    monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
    from main import app
    client = TestClient(app)
    r = client.post("/webhook", json=make_update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"})
    assert r.json()["ok"] is False
    assert sent == []
    r = client.post("/webhook", json=make_update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
    assert r.json()["ok"] is True


# ---- Supabase memory (with a fake client) ----
class FakeQuery:
    def __init__(self, store, table):
        self.store, self.table, self.op, self.filters, self.payload = store, table, None, [], None

    def select(self, cols="*"):
        self.op = "select"; return self

    def upsert(self, payload):
        self.op, self.payload = "upsert", payload; return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload; return self

    def delete(self):
        self.op = "delete"; return self

    def eq(self, col, val):
        self.filters.append((col, val)); return self

    def execute(self):
        rows = self.store.setdefault(self.table, [])
        match = [r for r in rows if all(r.get(c) == v for c, v in self.filters)]
        if self.op == "upsert":
            rows[:] = [r for r in rows if r["chat_id"] != self.payload["chat_id"]] + [dict(self.payload)]
        elif self.op == "insert":
            rows.append(dict(self.payload))
        elif self.op == "delete":
            rows[:] = [r for r in rows if r not in match]
        return type("Res", (), {"data": match})()


def test_supabase_memory(monkeypatch):
    store = {}
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "sb_secret_x")
    monkeypatch.setattr(memory, "_client", type("DB", (), {"table": lambda self, t: FakeQuery(store, t)})())
    assert memory.mode() == "supabase"
    assert memory.get_conversation_id(5) is None
    memory.save_conversation_id(5, "conv_a")
    memory.save_conversation_id(5, "conv_b")
    assert memory.get_conversation_id(5) == "conv_b"
    assert len(store["chats"]) == 1
    memory.log_message(5, "Mei Ling", "user", "hi")
    assert store["messages"][0]["text"] == "hi"
    memory.forget(5)
    assert memory.get_conversation_id(5) is None

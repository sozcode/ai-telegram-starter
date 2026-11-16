# Trainer checks - run with:  pytest
# No keys needed: Telegram, OpenAI and Supabase are replaced with fakes.
import os
import runpy

import pytest
import requests

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_example")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:test")

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class Res:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def update(text, chat_id=111, name="Mei Ling"):
    return {"update_id": 10, "message": {"from": {"first_name": name}, "chat": {"id": chat_id}, "text": text}}


# ---------- Day 1: day1_bot.py ----------
import day1_bot  # noqa: E402


def test_day1_polling(monkeypatch):
    sent, calls = [], []
    updates = [
        update("menu", 1),
        {"update_id": 11, "message": {"from": {"first_name": "Ahmad"}, "chat": {"id": 2}, "text": "one kopi-o please"}},
        {"update_id": 12, "message": {"from": {"first_name": "Ahmad"}, "chat": {"id": 2}, "sticker": {}}},
    ]

    def fake_get(url, params=None):
        calls.append(params["offset"])
        if len(calls) == 1:
            return Res({"ok": True, "result": updates})
        raise KeyboardInterrupt   # pretend someone pressed Ctrl + C

    posts = []
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", lambda url, json=None: (posts.append(url), sent.append(json)))
    with pytest.raises(KeyboardInterrupt):
        runpy.run_path("day1_bot.py", run_name="__main__")

    assert posts[0].endswith("/deleteWebhook")      # switches Telegram to polling first
    assert calls == [None, 13]
    texts = [j["text"] for j in sent if j]
    assert "Today's menu" in texts[0]
    assert texts[1] == "One Kopi-O coming up! That's $1.20."
    assert len(texts) == 2                           # the sticker was skipped


def test_day1_webhook(monkeypatch):
    sent = []
    monkeypatch.setattr(day1_bot, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    monkeypatch.setattr(day1_bot, "WEBHOOK_SECRET", "s3cret")
    client = TestClient(day1_bot.app)
    assert client.get("/").json() == {"status": "Kopi Uncle is running!"}
    wrong = client.post("/webhook", json=update("menu"), headers={"X-Telegram-Bot-Api-Secret-Token": "nope"})
    assert wrong.json() == {"ok": False} and sent == []
    right = client.post("/webhook", json=update("one teh-c"), headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
    assert right.json() == {"ok": True}
    assert sent == [(111, "One Teh-C coming up! That's $1.50.")]


# ---------- Day 2: main.py ----------
class FakeTable:
    def __init__(self, rows):
        self.rows, self.filters, self.op, self.payload = rows, [], None, None

    def select(self, cols):
        self.op = "select"
        return self

    def upsert(self, payload):
        self.op, self.payload = "upsert", payload
        return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self

    def eq(self, col, val):
        self.filters.append((col, val))
        return self

    def execute(self):
        match = [r for r in self.rows if all(r.get(c) == v for c, v in self.filters)]
        if self.op == "upsert":
            self.rows[:] = [r for r in self.rows if r["chat_id"] != self.payload["chat_id"]] + [self.payload]
        if self.op == "insert":
            self.rows.append(self.payload)
        return Res(match)


@pytest.fixture
def fake_db(monkeypatch):
    tables = {"chats": [], "messages": []}
    monkeypatch.setattr(main, "db", type("DB", (), {"table": lambda self, name: FakeTable(tables[name])})())
    return tables


def test_memory(fake_db):
    assert main.get_conversation_id(5) is None
    main.save_conversation_id(5, "conv_a")
    main.save_conversation_id(5, "conv_b")
    assert main.get_conversation_id(5) == "conv_b"
    assert len(fake_db["chats"]) == 1


def test_handle_update(monkeypatch, fake_db):
    sent = []
    monkeypatch.setattr(main, "ask_uncle", lambda chat_id, text: f"Uncle heard: {text}")
    monkeypatch.setattr(main, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    main.handle_update(update("one kopi"))
    main.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "from": {}, "sticker": {}}})
    assert sent == [(111, "Uncle heard: one kopi")]
    assert [m["role"] for m in fake_db["messages"]] == ["user", "bot"]


def test_tools_and_agent():
    assert main.prices["kopi-o"] == 1.2
    assert [t.name for t in main.uncle.tools] == ["get_menu", "calculate_bill", "get_weather"]


def test_web_app(monkeypatch):
    handled = []
    monkeypatch.setattr(main, "handle_update", lambda u: handled.append(u))
    monkeypatch.setattr(main, "WEBHOOK_SECRET", "s3cret")
    client = TestClient(main.app)
    assert client.get("/").json() == {"status": "Kopi Uncle is running!"}
    wrong = client.post("/webhook", json=update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "nope"})
    assert wrong.json() == {"ok": False} and handled == []
    right = client.post("/webhook", json=update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
    assert right.json() == {"ok": True} and len(handled) == 1

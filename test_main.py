# Trainer checks - run with:  pytest
# No keys needed: Telegram, OpenAI and Supabase are replaced with fakes.
import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def fake_world(monkeypatch):
    sent = []
    monkeypatch.setattr(main, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    monkeypatch.setattr(main, "send_typing", lambda chat_id: None)
    monkeypatch.setattr(main, "OPENAI_API_KEY", "")
    monkeypatch.setattr(main, "WEBHOOK_SECRET", "")
    monkeypatch.setattr(main, "db", None)
    main.conversations.clear()
    return sent


def update(text, chat_id=111, name="Mei Ling"):
    return {"update_id": 1, "message": {"from": {"first_name": name}, "chat": {"id": chat_id}, "text": text}}


def test_rules():
    assert "Hello Mei Ling" in main.reply_with_rules("/start", "Mei Ling")
    assert "$1.20" in main.reply_with_rules("one KOPI-O please", "x")
    assert "don't understand" in main.reply_with_rules("bubble tea", "x")


def test_tool_schemas_build():
    assert "order" in main.calculate_bill.params_json_schema["properties"]
    assert [t.name for t in main.uncle.tools] == ["get_menu", "calculate_bill", "get_weather"]


def test_rules_bot_replies(fake_world):
    main.handle_update(update("menu"))
    assert "Today's menu" in fake_world[0][1]


def test_ignores_stickers(fake_world):
    main.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "from": {}, "sticker": {}}})
    assert fake_world == []


def test_agent_memory(monkeypatch, fake_world):
    monkeypatch.setattr(main, "OPENAI_API_KEY", "fake")
    seen = []

    def fake_agent(text, conversation_id):
        seen.append(conversation_id)
        return f"Uncle heard: {text}", conversation_id or "conv_1"

    monkeypatch.setattr(main, "reply_with_agent", fake_agent)
    main.handle_update(update("one kopi"))
    main.handle_update(update("what did I order?"))
    assert seen == [None, "conv_1"]
    main.handle_update(update("/reset"))
    assert main.get_conversation_id(111) is None


def test_errors_dont_crash(monkeypatch, fake_world):
    monkeypatch.setattr(main, "OPENAI_API_KEY", "fake")
    monkeypatch.setattr(main, "reply_with_agent", lambda t, c: 1 / 0)
    main.handle_update(update("hello"))
    assert "brain got problem" in fake_world[0][1]


def test_web_app(monkeypatch, fake_world):
    client = TestClient(main.app)
    assert client.get("/").json()["brain"] == "rules"
    assert client.post("/webhook", json=update("hi")).json() == {"ok": True}
    monkeypatch.setattr(main, "WEBHOOK_SECRET", "s3cret")
    wrong = client.post("/webhook", json=update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "nope"})
    assert wrong.json() == {"ok": False}
    assert len(fake_world) == 1


# ---- Day 1 bot (day1_bot.py) ----
def test_day1_bot(monkeypatch, capsys):
    import runpy
    import requests

    sent, calls = [], []
    updates = [
        {"update_id": 10, "message": {"from": {"first_name": "Mei Ling"}, "chat": {"id": 1}, "text": "menu"}},
        {"update_id": 11, "message": {"from": {"first_name": "Ahmad"}, "chat": {"id": 2}, "text": "one kopi-o please"}},
        {"update_id": 12, "message": {"from": {"first_name": "Ahmad"}, "chat": {"id": 2}, "sticker": {}}},
    ]

    class Res:
        def __init__(self, data): self.data = data
        def json(self): return self.data

    def fake_get(url, params=None, timeout=None):
        calls.append(params["offset"])
        if len(calls) == 1:
            return Res({"ok": True, "result": updates})
        raise KeyboardInterrupt   # pretend the trainer pressed Ctrl + C

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", lambda url, json=None: sent.append(json))
    runpy.run_path("day1_bot.py")

    assert calls == [None, 13]
    assert "Today's menu" in sent[0]["text"]
    assert sent[1] == {"chat_id": 2, "text": "One Kopi-O coming up! That's $1.20."}
    assert "Bot stopped." in capsys.readouterr().out


def test_day1_bot_wrong_token(monkeypatch, capsys):
    import runpy
    import requests

    class Res:
        def json(self): return {"ok": False, "description": "Unauthorized"}

    monkeypatch.setattr(requests, "get", lambda url, params=None, timeout=None: Res())
    runpy.run_path("day1_bot.py")
    out = capsys.readouterr().out
    assert "Telegram says: Unauthorized" in out and "Bot stopped." in out

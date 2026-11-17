# Trainer checks - run with:  pytest
# No keys needed: Telegram and OpenAI are replaced with fakes.
import os
import runpy

import pytest
import requests

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_CONVERSATION_ID", "conv_test")

import day1_bot  # noqa: E402
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
class Item:
    def __init__(self, type, **fields):
        self.type = type
        self.__dict__.update(fields)


class FakeResponses:
    """Scripted OpenAI: first asks for get_menu, then answers with what the tool returned."""

    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        first = kwargs["input"][0]
        if first.get("type") == "function_call_output":
            return Item("response", output=[Item("message")], output_text="Kopi-O is $1.20 lah!")
        call = Item("function_call", name="get_menu", arguments="{}", call_id="call_1")
        return Item("response", output=[call], output_text="")


def test_ask_uncle_runs_function_tools(monkeypatch):
    fake = FakeResponses()
    monkeypatch.setattr(main, "client", Item("client", responses=fake))
    answer = main.ask_uncle([{"type": "input_text", "text": "how much is kopi-o?"}])

    assert answer == "Kopi-O is $1.20 lah!"
    assert len(fake.calls) == 2
    tool_result = fake.calls[1]["input"][0]
    assert tool_result["call_id"] == "call_1" and "Kopi-O" in tool_result["output"]
    assert all(c["conversation"] == main.CONVERSATION_ID for c in fake.calls)   # one remembered chat
    assert {t.get("name") or t["type"] for t in fake.calls[0]["tools"]} == {"get_menu", "get_weather", "web_search", "code_interpreter"}


def test_handle_update_text_photo_file(monkeypatch):
    asked, sent = [], []
    monkeypatch.setattr(main, "ask_uncle", lambda content: asked.append(content) or "Can lah!")
    monkeypatch.setattr(main, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    monkeypatch.setattr(main, "download", lambda file_id: "QUJD")   # base64 for "ABC"

    main.handle_update(update("hello"))
    main.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "caption": "split this", "photo": [{"file_id": "s"}, {"file_id": "big"}]}})
    main.handle_update({"update_id": 3, "message": {"chat": {"id": 1}, "document": {"file_id": "d", "file_name": "receipt.pdf", "mime_type": "application/pdf"}}})
    main.handle_update({"update_id": 4, "message": {"chat": {"id": 1}, "sticker": {}}})

    assert len(asked) == 3 and len(sent) == 3          # the sticker was skipped
    assert asked[0] == [{"type": "input_text", "text": "hello"}]
    assert asked[1][1] == {"type": "input_image", "image_url": "data:image/jpeg;base64,QUJD"}
    assert asked[2][1]["filename"] == "receipt.pdf"
    assert asked[2][1]["file_data"] == "data:application/pdf;base64,QUJD"


def test_function_tools():
    assert "Kaya Toast Set" in main.get_menu()
    assert set(main.functions) == {"get_menu", "get_weather"}


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

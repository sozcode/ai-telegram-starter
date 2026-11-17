# Trainer checks - run with:  pytest
# No keys needed: Telegram and OpenAI are replaced with fakes.
import os
import runpy

import pytest
import requests

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("OPENAI_CONVERSATION_ID", "conv_test")
os.environ.setdefault("OPENAI_HDB_FILE_ID", "file_test")

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
    """Scripted OpenAI: first asks for get_air_quality, then answers with what the tool returned."""

    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(kwargs["input"], list) and kwargs["input"][0].get("type") == "function_call_output":
            return Item("response", output=[Item("message")], output_text="Air is good today!")
        call = Item("function_call", name="get_air_quality", arguments="{}", call_id="call_1")
        return Item("response", output=[call], output_text="")


def test_ask_runs_function_tools(monkeypatch):
    fake = FakeResponses()
    monkeypatch.setattr(main, "client", Item("client", responses=fake))
    monkeypatch.setattr(main, "get_air_quality", lambda: "24-hour PSI by region: {'east': 38}")
    answer = main.ask("how's the air?")

    assert answer == "Air is good today!"
    assert len(fake.calls) == 2
    tool_result = fake.calls[1]["input"][0]
    assert tool_result["call_id"] == "call_1" and "PSI" in tool_result["output"]
    assert all(c["conversation"] == main.CONVERSATION_ID for c in fake.calls)   # one remembered chat
    tools = fake.calls[0]["tools"]
    assert {t.get("name") or t["type"] for t in tools} == {"get_weather", "get_air_quality", "code_interpreter", "web_search"}
    python_tool = [t for t in tools if t["type"] == "code_interpreter"][0]
    assert python_tool["container"]["file_ids"] == [main.HDB_FILE_ID]      # the HDB csv goes to the python tool


def test_handle_update_text_only(monkeypatch):
    asked, sent = [], []
    monkeypatch.setattr(main, "ask", lambda text: asked.append(text) or "Can!")
    monkeypatch.setattr(main, "send_message", lambda chat_id, text: sent.append((chat_id, text)))
    main.handle_update(update("hello"))
    main.handle_update({"update_id": 2, "message": {"chat": {"id": 1}, "photo": [{"file_id": "x"}]}})
    main.handle_update({"update_id": 3, "message": {"chat": {"id": 1}, "sticker": {}}})
    assert asked == ["hello"]
    assert sent == [(111, "Can!")]


def test_ask_runs_get_weather_with_area(monkeypatch):
    calls = []

    class WeatherThenTalk:
        def create(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return Item("response", output=[Item("function_call", name="get_weather", arguments='{"area": "Bedok"}', call_id="w")], output_text="")
            return Item("response", output=[Item("message")], output_text="Cloudy in Bedok!")

    monkeypatch.setattr(main, "client", Item("client", responses=WeatherThenTalk()))
    monkeypatch.setattr(main, "get_weather", lambda area: f"{area}: Cloudy")
    assert main.ask("weather in bedok?") == "Cloudy in Bedok!"
    assert calls[1]["input"] == [{"type": "function_call_output", "call_id": "w", "output": "Bedok: Cloudy"}]


def test_data_gov_functions(monkeypatch):
    weather = {"data": {"items": [{"forecasts": [{"area": "Tampines", "forecast": "Cloudy"}]}]}}
    psi = {"data": {"items": [{"readings": {"psi_twenty_four_hourly": {"east": 38}}}]}}
    monkeypatch.setattr(main.requests, "get", lambda url: Res(weather if "forecast" in url else psi))
    assert main.get_weather("tampines") == "Tampines: Cloudy"
    assert "No area" in main.get_weather("Narnia")
    assert "'east': 38" in main.get_air_quality()


def test_web_app(monkeypatch):
    handled = []
    monkeypatch.setattr(main, "handle_update", lambda u: handled.append(u))
    monkeypatch.setattr(main, "WEBHOOK_SECRET", "s3cret")
    client = TestClient(main.app)
    assert client.get("/").json() == {"status": "SG Data Bot is running!"}
    wrong = client.post("/webhook", json=update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "nope"})
    assert wrong.json() == {"ok": False} and handled == []
    right = client.post("/webhook", json=update("hi"), headers={"X-Telegram-Bot-Api-Secret-Token": "s3cret"})
    assert right.json() == {"ok": True} and len(handled) == 1


def test_ask_fallback_when_reply_is_empty(monkeypatch):
    class AlwaysCalls:
        def create(self, **kwargs):   # keeps asking for a tool, never writes text
            return Item("response", output=[Item("function_call", name="get_air_quality", arguments="{}", call_id="c")], output_text="")

    monkeypatch.setattr(main, "client", Item("client", responses=AlwaysCalls()))
    monkeypatch.setattr(main, "get_air_quality", lambda: "PSI 40")
    assert main.ask("air?") == "Sorry, I got stuck - please ask again."


def test_ask_without_tools(monkeypatch):
    calls = []

    class JustTalks:
        def create(self, **kwargs):
            calls.append(kwargs)
            return Item("response", output=[Item("message")], output_text="Hello!")

    monkeypatch.setattr(main, "client", Item("client", responses=JustTalks()))
    assert main.ask("hi") == "Hello!"
    assert len(calls) == 1   # no tools asked for, so only one call to OpenAI

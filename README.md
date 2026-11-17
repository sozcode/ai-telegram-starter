# ☕ Kopi Uncle — Build & Deploy Your Own AI Agent

Starter repo for the Sozcode 2-day course. By the end you'll have a **live AI agent on Telegram** that you can chat with — and send photos and files to.

```
Day 1   Python basics  →  Telegram API  →  your first bot (if/else rules)  →  live on Vercel
Day 2   OpenAI Responses API  →  function tools  →  web search, Python & files  →  memory  →  live AI bot 🚀
```

## 🚀 Quick start

1. Click **Use this template → Open in a codespace**.
2. Wait ~2 minutes while it installs everything.
3. Open `notebooks/day1/01_python_basics.ipynb` and pick the **Python 3.12** kernel when asked.
4. Copy `.env.example` to `.env` — you'll fill it in as the course goes.

## 📁 What's inside

| File | What it is |
|---|---|
| `notebooks/day1/` | 01–04: Python basics → JSON → Telegram API → your first live bot |
| `notebooks/day2/` | 05–09: first response → function tools → web search, Python & files → memory → build & deploy |
| **`day1_bot.py`** | **Day 1 bot** — if/else rules, works with polling *and* webhook |
| **`main.py`** | **Day 2 bot** — the AI agent: tools, photos & files, memory. Polling *and* webhook |
| `pyproject.toml` | The packages to install, and which bot Vercel puts online |
| `menu.csv` | The kopitiam menu & prices |
| `receipt.pdf` | A sample receipt to send Uncle (notebook 07) |

## ▶️ Run your bot

| Day 1 | Day 2 |
|---|---|
| `python day1_bot.py` | `python main.py` |
| needs `TELEGRAM_BOT_TOKEN` | also needs `OPENAI_API_KEY` (and `OPENAI_CONVERSATION_ID` from notebook 08) |

Chat with it on Telegram. **Ctrl + C** stops it (the `KeyboardInterrupt` message is normal).

Both bots work two ways, but a Telegram bot can only use **one at a time**:
- **Polling** — `python day1_bot.py` / `python main.py` in Codespaces. Running this switches your bot to polling.
- **Webhook** — on Vercel, Telegram sends each message to your web app. Switch to it with the *setWebhook* cell (notebook 04 or 09).

Try the Day 2 bot with: *"2 kopi-o peng and 1 kaya toast set, how much?"* · *"I'm in Bedok, what should I drink?"* · *"any new hawker centres?"* · a **photo of a receipt** · *"what did I order just now?"*

## 🧰 What Uncle can do (Day 2)

| Tool | Type | Example |
|---|---|---|
| `get_menu` | function tool (our Python) | prices from `menu.csv` |
| `get_weather` | function tool (our Python) | live forecast from data.gov.sg |
| `web_search` | built-in (OpenAI runs it) | news, opening hours |
| `code_interpreter` | built-in (OpenAI runs Python) | adding up and splitting bills |
| file inputs | photos & PDFs sent on Telegram | reading a receipt |

**Memory:** one OpenAI **conversation** (`OPENAI_CONVERSATION_ID`) keeps the chat history. This bot is built for **one person** — everyone who chats with it shares that conversation.

## 🌍 Go live on Vercel

- **Day 1:** follow *Put your bot online* at the end of **notebook 04**. `pyproject.toml` tells Vercel to run `day1_bot.py`.
- **Day 2:** in `pyproject.toml`, change `entrypoint = "day1_bot:app"` to `"main:app"`, add `OPENAI_API_KEY` and `OPENAI_CONVERSATION_ID` in Vercel, then commit + sync (**notebook 09**, step 4).

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `KeyError: 'result'` when starting a bot | Wrong `TELEGRAM_BOT_TOKEN`, or the bot is already running somewhere else. |
| Bot doesn't reply after deploying | Re-run the *setWebhook* cell (notebook 04 or 09). Did you run `python day1_bot.py` / `python main.py`? That switches the bot back to polling. |
| Vercel shows the wrong bot | Check `entrypoint` in `pyproject.toml`, then commit + sync. |
| Uncle forgets everything after a restart | Add `OPENAI_CONVERSATION_ID` to `.env` (notebook 08) and to Vercel. |
| Bot stops replying on Vercel | Check **Vercel → Logs** for the error. Usually a missing or wrong key. |
| Codespace stopped | It sleeps when idle. Reopen it and run your bot again. |

---

## 👩‍🏫 Trainer checklist

**1 week before**
- [ ] Ask learners to create **GitHub**, **Telegram** and **Vercel** accounts.
- [ ] Create one OpenAI **project** with a monthly **budget limit**, and one API key per learner. Code interpreter and web search cost extra per use.

**Day before**
- [ ] Open a codespace from the template on the venue's network.
- [ ] Run all 9 notebooks with a real key.
- [ ] Multi-turn test on Telegram ("what did I order just now?"), plus send a receipt photo, to confirm memory, tools and files work with your model.
- [ ] `pytest` — checks both bots without any keys.

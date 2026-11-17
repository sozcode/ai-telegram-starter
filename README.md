# 🤖 Build & Deploy Your Own AI Agent on Telegram

Starter repo for the Sozcode 2-day course. By the end you'll have a **live AI assistant on Telegram** that uses live Singapore data, analyses HDB prices with Python, and searches your own documents.

```
Day 1   Python basics  →  Telegram API  →  ☕ Kopi Uncle (if/else rules)  →  live on Vercel
Day 2   OpenAI Responses API  →  data.gov.sg tools  →  Python & web  →  documents  →  memory  →  🇸🇬 SG Data Bot live
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
| `notebooks/day2/` | 05–10: first response → function tools → Python & web → documents → memory → build & deploy |
| **`day1_bot.py`** | **Day 1 bot** — Kopi Uncle with if/else rules. Polling *and* webhook |
| **`main.py`** | **Day 2 bot** — SG Data Bot, the AI assistant. Polling *and* webhook |
| `pyproject.toml` | The packages to install, and which bot Vercel puts online |
| `hdb_resale_prices.csv` | HDB resale flats sold in the last 12 months (from data.gov.sg) |
| `docs/` | Six sample PDFs for flat hunting — notes, 3 listings, viewing notes, renovation quotes (notebook 08). All fictional. |

## ▶️ Run your bot

| Day 1 | Day 2 |
|---|---|
| `python day1_bot.py` | `python main.py` |
| needs `TELEGRAM_BOT_TOKEN` | also needs `OPENAI_API_KEY`, plus the three IDs from notebooks 07–09 |

Chat with it on Telegram (text messages only). **Ctrl + C** stops it (the `KeyboardInterrupt` message is normal).

Both bots work two ways, but a Telegram bot can only use **one at a time**:
- **Polling** — `python day1_bot.py` / `python main.py` in Codespaces. Running this switches your bot to polling.
- **Webhook** — on Vercel, Telegram sends each message to your web app. Switch to it with the *setWebhook* cell (notebook 04 or 10).

Try the Day 2 bot with: *"What's our budget?"* · *"Which listing fits it best?"* · *"Which renovation quote is cheaper?"* · *"Median 4-room price in Bedok?"* · *"Is the air OK for cycling in the east?"*

## 🧰 What SG Data Bot can do (Day 2)

| Tool | Type | Example |
|---|---|---|
| `get_weather` | function tool (our Python) | live 2-hour forecast from data.gov.sg |
| `get_air_quality` | function tool (our Python) | live PSI from data.gov.sg |
| `code_interpreter` | built-in (OpenAI runs Python) | analysing `hdb_resale_prices.csv` |
| `web_search` | built-in (OpenAI searches) | news and anything that changes |
| `file_search` | built-in (OpenAI searches your PDFs in a vector store) | "which listing is cheapest?" |

**Memory:** one OpenAI **conversation** (`OPENAI_CONVERSATION_ID`) holds the chat history. Your PDFs live in a **vector store** (`OPENAI_VECTOR_STORE_ID`). This bot is built for **one person** — everyone who chats with it shares that conversation.

## 🌍 Go live on Vercel

- **Day 1:** follow *Put your bot online* at the end of **notebook 04**. `pyproject.toml` tells Vercel to run `day1_bot.py`.
- **Day 2:** in `pyproject.toml`, change `entrypoint = "day1_bot:app"` to `"main:app"`, add `OPENAI_API_KEY`, `OPENAI_HDB_FILE_ID`, `OPENAI_VECTOR_STORE_ID` and `OPENAI_CONVERSATION_ID` in Vercel, then commit + sync (**notebook 10**, step 4).

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `KeyError: 'result'` when starting a bot | Wrong `TELEGRAM_BOT_TOKEN`, or the bot is already running somewhere else. |
| Bot doesn't reply after deploying | Re-run the *setWebhook* cell (notebook 04 or 10). Did you run `python day1_bot.py` / `python main.py`? That switches the bot back to polling. |
| Vercel shows the wrong bot | Check `entrypoint` in `pyproject.toml`, then commit + sync. |
| Bot can't find your PDFs, or forgets you after a restart | Check all three IDs from notebooks 07–09 are in `.env` **and** in Vercel. |
| Bot stops replying on Vercel | Check **Vercel → Logs** for the error. Usually a missing or wrong key. |
| Codespace stopped | It sleeps when idle. Reopen it and run your bot again. |

---

## 👩‍🏫 Trainer checklist

**1 week before**
- [ ] Ask learners to create **GitHub**, **Telegram** and **Vercel** accounts.
- [ ] Create one OpenAI **project** with a monthly **budget limit**, and one API key per learner. The python tool, file search and web search cost extra per use (vector store storage too, after the first 1 GB).

**Day before**
- [ ] Open a codespace from the template on the venue's network.
- [ ] Run all 10 notebooks with a real key.
- [ ] On Telegram, ask a few follow-ups ("what's our budget?", "which listing fits?", "is it fairly priced?") to confirm file search, memory, the python tool and the data.gov.sg tools all work with your model.
- [ ] `pytest` — checks both bots without any keys.

## 📊 Data

`hdb_resale_prices.csv` contains information from *Resale flat prices based on registration date from Jan-2017 onwards*, accessed from [data.gov.sg](https://data.gov.sg), made available under the terms of the [Singapore Open Data Licence version 1.0](https://data.gov.sg/open-data-licence). This copy keeps the last 12 months only.

The PDFs in `docs/` are made up for this course — all names, people, agencies and prices are fictional.

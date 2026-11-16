# ☕ Kopi Uncle — Build & Deploy Your Own AI Agent

Starter repo for the Sozcode 2-day course. By the end you'll have a **live AI agent on Telegram** that anyone can chat with.

```
Day 1   Python basics  →  Telegram API  →  your first bot (if/else rules)
Day 2   AI agent + tools  →  memory  →  database  →  live on Vercel 🚀
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
| `notebooks/day2/` | 05–09: first agent → tools → memory → Supabase → build & deploy |
| **`day1_bot.py`** | **Day 1 bot** — if/else rules, one short file |
| **`main.py`** | **Day 2 bot** — the AI agent with tools, memory and a web app, one file |
| `menu.csv` | The kopitiam menu & prices |
| `setup.sql` | Creates the database tables in Supabase |

## ▶️ Run your bot

| Day 1 | Day 2 |
|---|---|
| `python day1_bot.py` | `python main.py` |
| needs `TELEGRAM_BOT_TOKEN` | also needs `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` |

Chat with it on Telegram. **Ctrl + C** stops it (the `KeyboardInterrupt` message is normal).

Try: *"2 kopi-o peng and 1 kaya toast set, how much?"* · *"I'm in Bedok, what should I drink?"* · *"what did I order just now?"*

## 🗄️ Supabase (Day 2)

1. Create a free project at [supabase.com](https://supabase.com) (no credit card, pick Singapore).
2. **SQL Editor → New query** → paste `setup.sql` → **Run**.
3. **Project Settings → API Keys** → copy the **Project URL** and a **Secret key** (`sb_secret_...`) into `.env`.

> ⚠️ The secret key can read everything. Keep it in `.env` / Vercel settings only — never in your code or on GitHub.

## 🌍 Go live on Vercel

Follow **notebook 09**, steps 4–6:
1. Commit + sync your code to GitHub.
2. Import the repo on [vercel.com](https://vercel.com), add your keys plus a `WEBHOOK_SECRET` under **Environment Variables**, then **Redeploy**.
3. Run the *"Tell Telegram where your bot lives"* cell in notebook 09.

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `KeyError: 'result'` when starting a bot | Wrong `TELEGRAM_BOT_TOKEN`, or the bot is already running somewhere else. |
| Bot doesn't reply after deploying | Re-run the webhook cell in notebook 09. Is `python main.py` still running? (It switches Telegram back to polling.) |
| Supabase `permission denied` | Run `setup.sql` again. |
| Bot stops replying on Vercel | Check **Vercel → Logs** for the error. Usually a missing or wrong key. |
| Codespace stopped | It sleeps when idle. Reopen it and run your bot again. |

---

## 👩‍🏫 Trainer checklist

**1 week before**
- [ ] Ask learners to create **GitHub**, **Telegram**, **Vercel** and **Supabase** accounts.
- [ ] Create one OpenAI **project** with a monthly **budget limit**, and one API key per learner.

**Day before**
- [ ] Open a codespace from the template on the venue's network.
- [ ] Run all 9 notebooks with a real key.
- [ ] Multi-turn test ("what did I order just now?") to confirm conversation memory works with your model.
- [ ] `pytest` — checks both bots without any keys.

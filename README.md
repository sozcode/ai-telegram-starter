# ☕ Kopi Uncle — Build & Deploy Your Own AI Agent

Starter repo for the Sozcode 2-day course. By the end you'll have a **live AI agent on Telegram** that anyone can chat with.

```
Day 1   Python basics  →  Telegram API  →  rule-based bot
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
| **`main.py`** | **Your whole bot in one file** — read it top to bottom |
| `menu.csv` | The kopitiam menu & prices |
| `setup.sql` | Creates the database tables in Supabase |
| `.env.example` | The keys you'll need |

## ▶️ Run your bot

```
python main.py
```
Chat with it on Telegram. **Ctrl + C** stops it.

The bot picks its brain by itself:
- **No `OPENAI_API_KEY`** → Day 1 if/else rules
- **With `OPENAI_API_KEY`** → the AI agent (`gpt-6-luna`, with menu, bill and weather tools)
- **With Supabase keys** → remembers every chat even after a restart

Try: *"2 kopi-o peng and 1 kaya toast set, how much?"* · *"I'm in Bedok, what should I drink?"* · *"what did I order just now?"* · `/reset`

## 🗄️ Add Supabase memory (Day 2)

1. Create a free project at [supabase.com](https://supabase.com) (no credit card, pick Singapore).
2. **SQL Editor → New query** → paste `setup.sql` → **Run**.
3. **Project Settings → API Keys** → copy the **Project URL** and a **Secret key** (`sb_secret_...`) into `.env`.

> ⚠️ The secret key can read everything. Keep it in `.env` / Vercel settings only — never in your code or on GitHub.

## 🌍 Go live on Vercel

1. **Source Control** tab → **Commit** → **Sync Changes**.
2. [vercel.com](https://vercel.com) → **Add New → Project** → import your repo → **Deploy**.
3. **Settings → Environment Variables** → add the keys from your `.env`, plus `WEBHOOK_SECRET` (any random text) → **Redeploy**.
4. Open `https://YOUR-APP.vercel.app/` — check everything says `true`.
5. Stop `python main.py`, then open `https://YOUR-APP.vercel.app/setup` **once**.

Your bot now runs 24/7. 🎉 (Running `python main.py` again switches it back to Codespaces — visit `/setup` again afterwards.)

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `Telegram says: Unauthorized` | Wrong `TELEGRAM_BOT_TOKEN` in `.env`. |
| `Telegram says: Conflict` | Your bot is running somewhere else — stop the other one. |
| Bot doesn't reply after deploying | Did you open `/setup`? Is `python main.py` still running? |
| `/` shows `"brain": "rules"` on Vercel | Add `OPENAI_API_KEY` in Vercel, then **Redeploy**. |
| Supabase `permission denied` | Run `setup.sql` again. |
| "Uncle's brain got problem" | Check the terminal (or **Vercel → Logs**) for the error. Usually a wrong key. |
| Codespace stopped | It sleeps when idle. Reopen it and run `python main.py` again. |

---

## 👩‍🏫 Trainer checklist

**1 week before**
- [ ] Ask learners to create **GitHub**, **Telegram**, **Vercel** and **Supabase** accounts.
- [ ] Create one OpenAI **project** with a monthly **budget limit**, and one API key per learner.

**Day before**
- [ ] Open a codespace from the template on the venue's network.
- [ ] Run all 9 notebooks with a real key.
- [ ] Multi-turn test ("what did I order just now?") to confirm conversation memory works with your model.
- [ ] `pytest` — checks the bot without any keys.

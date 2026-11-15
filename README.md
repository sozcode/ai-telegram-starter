# ☕ Kopi Uncle — Build & Deploy Your Own AI Agent

Starter repo for the Sozcode 2-day course. By the end you'll have a **live AI agent on Telegram** that anyone can chat with.

```
Day 1   Python basics  →  Telegram API  →  rule-based bot (running in Codespaces)
Day 2   AI agent + tools  →  memory in Supabase  →  deployed on Vercel 🚀
```

---

## 🚀 Learner quick start

1. Click **Use this template → Open in a codespace** (or **Code → Codespaces → Create codespace**).
2. Wait ~2 minutes while it installs everything.
3. Open `notebooks/day1/01_python_basics.ipynb` and pick the **Python 3.12** kernel when asked.
4. Copy `.env.example` to `.env` — you'll fill it in as the course goes.

## 📁 What's inside

| Path | What it is | When |
|---|---|---|
| `notebooks/day1/` | 01–04: Python basics → JSON → Telegram API → live rule-based bot | Day 1 |
| `notebooks/day2/` | 05–09: first agent → tools → conversation memory → Supabase → build & deploy | Day 2 |
| `bot/rules.py` | Day 1 brain: `if`/`else` rules | Day 1 |
| `bot/agent.py` | Day 2 brain: the Kopi Uncle agent (OpenAI Agents SDK, `gpt-6-luna`) | Day 2 AM |
| `bot/tools.py` | Tools the agent can use: menu (pandas), bill, live weather | Day 2 AM |
| `bot/memory.py` | Which Telegram chat ↔ which OpenAI Conversation — Supabase, or a dict if no database | Day 2 PM |
| `bot/handler.py` | **The one function** both ways of running share | — |
| `run_polling.py` | Run the bot from Codespaces: `python run_polling.py` | Day 1–2 |
| `main.py` | The same bot as a web app for Vercel (webhook) | Deploy |
| `supabase/setup.sql` | Creates the database tables | Day 2 PM |
| `data/menu.csv` | Kopitiam menu & prices | Day 2 |

The bot picks its brain automatically: **no `OPENAI_API_KEY` → rules, key set → AI agent.**
Same for memory: **no Supabase keys → Python dict, keys set → Supabase.**

## 🧠 Day 2: switch on the AI

Add to `.env`:
```
OPENAI_API_KEY=sk-...
```
Run `python run_polling.py` again — same bot, new brain. The default model is **`gpt-6-luna`** with low reasoning effort (fast replies); change it with `OPENAI_MODEL` / `OPENAI_REASONING_EFFORT`.

**How memory works:** the Agents SDK stores each chat in an **OpenAI Conversation** (`OpenAIConversationsSession`). The bot only saves the conversation ID for each Telegram chat.

Try:
- *"2 kopi-o peng and 1 kaya toast set, how much?"* → uses `calculate_bill`
- *"hot today or not? what should I drink in Bedok?"* → uses `get_weather` (live data.gov.sg)
- *"what did I order just now?"* → memory
- `/reset` → forget the conversation

## 🗄️ Day 2: add Supabase memory

1. Create a free project at [supabase.com](https://supabase.com) (no credit card).
2. **SQL Editor → New query** → paste `supabase/setup.sql` → **Run**.
3. **Project Settings → API Keys** → copy the **Project URL** and a **Secret key** (`sb_secret_...`).
4. Add to `.env`:
   ```
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_SECRET_KEY=sb_secret_...
   ```
5. Restart the bot, chat, then watch rows appear in **Table Editor → messages**.

> ⚠️ The secret key bypasses all security. It lives **only** in `.env` / Vercel settings — never in your code or on GitHub.

## 🌍 Deploy to Vercel

1. Commit and push your code (Source Control tab → Commit → Sync).
2. On [vercel.com](https://vercel.com) → **Add New → Project** → import your repo → **Deploy**.
3. **Settings → Environment Variables**, add the same keys as your `.env`, plus `WEBHOOK_SECRET` (any random text). Then **Deployments → ⋯ → Redeploy**.
4. Open `https://YOUR-APP.vercel.app/` — check everything says `true`.
5. Open `https://YOUR-APP.vercel.app/setup` **once** — this tells Telegram where your bot lives.
6. Stop `run_polling.py` in Codespaces. Your bot now runs 24/7 without your laptop. 🎉

> Want to code in Codespaces again? `run_polling.py` removes the webhook automatically. Visit `/setup` again when you're done.

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Bot doesn't reply after deploying | Did you visit `/setup`? Is `run_polling.py` still running somewhere? (Only one can be active.) |
| `/` shows `"brain": "rules"` on Vercel | Add `OPENAI_API_KEY` in Vercel, then **Redeploy** — env changes need a redeploy. |
| Supabase `permission denied` | Run `supabase/setup.sql` again — the `grant` lines give the server access. |
| "Uncle's brain got problem" | Check **Vercel → Logs** (or your terminal) for the error. Usually a wrong key. |
| Codespace stopped | It sleeps after ~30 min idle. Reopen it and run the bot again. |

---

## 👩‍🏫 Trainer checklist

**1 week before**
- [ ] Make this repo a **template** (Settings → Template repository).
- [ ] Ask learners to create **GitHub**, **Telegram**, **Vercel** and **Supabase** accounts (email verification takes time).
- [ ] Create one OpenAI **project** per class with a monthly **budget limit**, and one API key per learner.

**Day before**
- [ ] Open a codespace from the template on the venue's network.
- [ ] Run all 9 notebooks with a real key and `pytest` (tests pass with no keys).
- [ ] Do a multi-turn chat test ("what did I order just now?") to confirm conversation memory works with your chosen model.
- [ ] Do one full deploy end to end with a test bot.

**Tests:** `pytest -q` checks the rules, tools, memory and webhook without any keys.

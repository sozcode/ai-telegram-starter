# Run your bot from Codespaces:   python run_polling.py
# Stop it with Ctrl + C
from bot import config, memory, telegram
from bot.handler import brain, handle_update

if not config.telegram_token():
    raise SystemExit("Add TELEGRAM_BOT_TOKEN to your .env file first!")

# If the bot was deployed with a webhook, polling won't work until we remove it
telegram.delete_webhook()

print(f"Bot is running! Brain: {brain()} | Memory: {memory.mode()}")
print("Message your bot on Telegram. Press Ctrl + C to stop.\n")

offset = None
try:
    while True:
        for update in telegram.get_updates(offset):
            handle_update(update)
            offset = update["update_id"] + 1  # tell Telegram we've handled it
except KeyboardInterrupt:
    print("\nBot stopped. Bye!")

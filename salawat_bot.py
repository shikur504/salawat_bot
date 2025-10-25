# salawat_bot.py
import asyncio
import json
import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

DATA_FILE = Path("salawat_data.json")

# Initialize persistent data
def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"total": 0}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

# Helper: parse integer from a message if present
def extract_number(text):
    try:
        # Trim spaces, attempt parse integer
        t = text.strip()
        # Allow messages that are exactly a number like "100" or "500"
        if t.lstrip("+-").isdigit():
            return int(t)
        # Optional: allow numbers embedded, e.g., "added 100"
        # parts = [p for p in t.split() if p.lstrip("+-").isdigit()]
        # return int(parts[0]) if parts else None
    except Exception:
        pass
    return None

# Handler: catch messages and update counter
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    # Only respond in groups and supergroups (optional)
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        return

    text = update.message.text or ""
    num = extract_number(text)
    if num is None:
        return  # ignore non-numeric messages

    data = load_data()
    data["total"] = int(data.get("total", 0)) + int(num)
    save_data(data)

    # Build the username/label for who added
    author = update.effective_user
    # prefer username, otherwise first_name
    who = author.username if author and author.username else (author.first_name if author else "Someone")
    # Post confirmation message in group
    resp = f"{who} added {num} to {chat.title or 'Group Salawat'}\nTotal count: {data['total']}"
    await context.bot.send_message(chat_id=chat.id, text=resp)

# Optional /total command to display current total
async def total_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"Total count: {data.get('total',0)}")

if __name__ == "__main__":
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("Set BOT_TOKEN environment variable and restart.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(CommandHandler("total", total_command))

    print("Bot starting (long polling)...")
    app.run_polling()


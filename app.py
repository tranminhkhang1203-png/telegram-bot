import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'dđ', 'đđ', 'dauduoi', 'đầu', 'đuôi']
EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def process_text(text):
    tokens = re.split(r'(\s+)', text)
    output = []
    for token in tokens:
        if re.match(r'^\s+$', token):
            output.append(token)
            continue
        match = re.match(r'^(\d+([.,]\d+)?)([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', token)
        if not match:
            output.append(token)
            continue
        so_danh = match[1]
        keyword = match[3]
        so_tien = match[4]
        unit = match[6] or 'n'
        if keyword in EXCLUDED:
            output.append(token)
            continue
        if keyword not in KEYWORDS:
            output.append(token)
            continue
        so_danh_clean = so_danh.split('.')[0].split(',')[0]
        if len(so_danh_clean) != 2:
            output.append(token)
            continue
        amount = float(so_tien.replace(',', '.'))
        if amount <= 0:
            output.append(token)
            continue
        new_amount = amount * 0.93
        rounded = round(new_amount * 10) / 10
        formatted = str(rounded)
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        new_token = so_danh + keyword + formatted + unit
        output.append(new_token)
    return ''.join(output)

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

@app_flask.route('/health')
def health():
    return "OK"

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("Thiếu TELEGRAM_TOKEN!")

application = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Gửi văn bản số đề, bot xử lý theo luật 0.93.")

async def handle(update: Update, context):
    result = process_text(update.message.text)
    await update.message.reply_text(result)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    import threading
    threading.Thread(target=application.run_polling, daemon=True).start()
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

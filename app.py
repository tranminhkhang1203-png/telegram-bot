import os
import re
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def tinh_tien(so_tien):
    try:
        amount = float(so_tien.replace(',', '.'))
    except:
        return None
    if amount <= 0:
        return None
    new_amount = amount * 0.93
    rounded = round(new_amount * 10) / 10
    formatted = str(rounded)
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return formatted

def process_text(text):
    tokens = re.split(r'(\s+)', text)
    output = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if re.match(r'^\s+$', token):
            output.append(token)
            i += 1
            continue

        # Token có dạng "số tiền + đơn vị" (50n, 100n, 2.5n)
        match = re.match(r'^(\d+([.,]\d+)?)([kn]?)$', token)
        if match:
            so_tien = match.group(1)
            unit = match.group(3) or 'n'
            # Kiểm tra token trước đó có phải từ khóa loại trừ không
            prev_word = None
            j = i - 1
            while j >= 0:
                if re.match(r'^\s+$', tokens[j]):
                    j -= 1
                    continue
                prev_word = tokens[j]
                break
            if prev_word and prev_word in EXCLUDED:
                output.append(token)
                i += 1
                continue
            new_tien = tinh_tien(so_tien)
            if new_tien:
                output.append(new_tien + unit)
                i += 1
                continue
            output.append(token)
            i += 1
            continue

        output.append(token)
        i += 1

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
    await update.message.reply_text("Gửi văn bản, bot xử lý theo luật 0.93.")

async def handle(update: Update, context):
    result = process_text(update.message.text)
    await update.message.reply_text(result)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    application.run_polling()

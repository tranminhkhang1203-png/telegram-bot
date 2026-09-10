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

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    application.run_polling()
import os
import re
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'đ', 'dđ', 'đđ', 'dauduoi', 'dau dui', 'duoi', 'đầu', 'đuôi']
EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def process_text(text):
    # Tách chuỗi thành các token, nhưng giữ khoảng trắng
    tokens = re.split(r'(\s+)', text)
    output = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Nếu là khoảng trắng, giữ nguyên
        if re.match(r'^\s+$', token):
            output.append(token)
            i += 1
            continue

        # Trường hợp 1: số + từ khóa + số tiền liền nhau (23dd500n)
        match = re.match(r'^(\d+([.,]\d+)?)([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', token)
        if match:
            so_danh = match[1]
            keyword = match[3]
            so_tien = match[4]
            unit = match[6] or 'n'
            output.append(xu_ly_token(so_danh, keyword, so_tien, unit, token))
            i += 1
            continue

        # Trường hợp 2: số đứng riêng, theo sau là từ khóa + số tiền (31 b50n)
        # Kiểm tra token hiện tại có phải là số không
        if re.match(r'^\d+([.,]\d+)?$', token):
            so_danh = token
            # Xem token tiếp theo có phải là từ khóa + số tiền không
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                match2 = re.match(r'^([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', next_token)
                if match2:
                    keyword = match2[1]
                    so_tien = match2[2]
                    unit = match2[4] or 'n'
                    # Xử lý
                    new_token = xu_ly_token(so_danh, keyword, so_tien, unit, so_danh + next_token)
                    output.append(new_token)
                    i += 2
                    continue
            # Nếu không khớp, giữ nguyên số
            output.append(token)
            i += 1
            continue

        # Các trường hợp khác giữ nguyên
        output.append(token)
        i += 1

    return ''.join(output)

def xu_ly_token(so_danh, keyword, so_tien, unit, original_token):
    if keyword in EXCLUDED:
        return original_token
    if keyword not in KEYWORDS:
        return original_token
    so_danh_clean = so_danh.split('.')[0].split(',')[0]
    if len(so_danh_clean) != 2:
        return original_token
    amount = float(so_tien.replace(',', '.'))
    if amount <= 0:
        return original_token
    new_amount = amount * 0.93
    rounded = round(new_amount * 10) / 10
    formatted = str(rounded)
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return so_danh + keyword + formatted + unit

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

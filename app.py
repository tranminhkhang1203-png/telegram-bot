import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'đ', 'dđ', 'đđ', 'dauduoi', 'dau dui', 'duoi', 'đầu', 'đuôi']
EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def process_text(text):
    # Tách token nhưng giữ khoảng trắng
    tokens = re.split(r'(\s+)', text)
    output = []

    for token in tokens:
        # Giữ nguyên khoảng trắng
        if re.match(r'^\s+$', token):
            output.append(token)
            continue

        # Trường hợp 1: liền nhau (23dd500n)
        match = re.match(r'^(\d+([.,]\d+)?)([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', token)
        if match:
            so_danh = match[1]
            keyword = match[3]
            so_tien = match[4]
            unit = match[6] or 'n'
            new_token = xu_ly_token(so_danh, keyword, so_tien, unit, token)
            output.append(new_token)
            continue

        # Trường hợp 2: có khoảng cách (31 b50n) -> tách thành 2 token riêng
        # Xử lý token dạng "31" + "b50n" hoặc "31" + "b" + "50n"
        # Ta thử ghép token hiện tại với token tiếp theo (nếu có)
        # Nhưng đơn giản hơn: xử lý từng token dạng "b50n" nếu đứng sau số

        # Nếu token có từ khóa và số tiền (dạng b50n, dd500n, lo10n)
        match2 = re.match(r'^([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', token)
        if match2:
            keyword = match2[1]
            so_tien = match2[2]
            unit = match2[4] or 'n'
            # Tìm số đánh ở token trước đó (nếu có)
            if output and re.match(r'^(\d+([.,]\d+)?)$', output[-1].strip()):
                so_danh = output[-1].strip()
                # Kiểm tra số đánh có 2 chữ số không
                so_danh_clean = so_danh.split('.')[0].split(',')[0]
                if len(so_danh_clean) == 2:
                    # Xóa số đánh đã dùng khỏi output
                    output.pop()
                    new_token = xu_ly_token(so_danh, keyword, so_tien, unit, token)
                    output.append(new_token)
                    continue
        output.append(token)

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

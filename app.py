import os
import re
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'đ', 'dđ', 'đđ', 'dauduoi', 'dau dui', 'duoi', 'đầu', 'đuôi']
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
    # Tách token giữ khoảng trắng
    tokens = re.split(r'(\s+)', text)
    output = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if re.match(r'^\s+$', token):
            output.append(token)
            i += 1
            continue

        # Nếu token là số đánh
        match_so = re.match(r'^(\d+)([.,]\d+)?$', token)
        if match_so and len(match_so.group(1)) == 2:
            so_danh = token
            # Gom các token tiếp theo thành chuỗi không dấu cách (tối đa 3 token)
            j = i + 1
            buffer = ""
            used_indices = []
            while j < len(tokens) and len(buffer) < 20:
                if re.match(r'^\s+$', tokens[j]):
                    j += 1
                    continue
                buffer += tokens[j]
                used_indices.append(j)
                j += 1
                # Thử match từ buffer
                match = re.match(r'^([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?', buffer)
                if match:
                    keyword = match.group(1)
                    so_tien = match.group(2)
                    unit = match.group(4) or 'n'
                    if keyword in EXCLUDED or keyword not in KEYWORDS:
                        break
                    new_tien = tinh_tien(so_tien)
                    if new_tien is None:
                        break
                    # Giữ nguyên khoảng trắng gốc giữa số đánh và từ khóa
                    output.append(so_danh)
                    # Thêm lại các token khoảng trắng giữa số đánh và từ khóa
                    for k in range(i + 1, used_indices[0]):
                        output.append(tokens[k])
                    # Thêm từ khóa + số tiền mới
                    output.append(keyword + new_tien + unit)
                    # Phần còn lại của buffer (nếu có) giữ nguyên
                    remaining = buffer[match.end():]
                    if remaining:
                        output.append(remaining)
                    i = used_indices[-1] + 1
                    break
            else:
                # Không tìm thấy match
                output.append(token)
                i += 1
                continue
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

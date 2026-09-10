import os
import re
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

KEYWORDS = ['b', 'd', 'dd', 'bao', 'bl', 'lô', 'lo', '₫', 'đ', 'dđ', 'đđ', 'dauduoi', 'dau dui', 'duoi', 'đầu', 'đuôi']
EXCLUDED = ['dx', 'dt', 'da', 'xc', 'xdao']

def tinh_tien(so_tien):
    """Nhân 0.93, làm tròn 1 số, bỏ .0"""
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
        
        # Giữ nguyên khoảng trắng
        if re.match(r'^\s+$', token):
            output.append(token)
            i += 1
            continue
        
        # Kiểm tra token có phải là số đánh (có thể kèm dấu . ,)
        match_so = re.match(r'^(\d+)([.,]\d+)?$', token)
        if match_so:
            so_danh = token
            so_danh_clean = match_so.group(1)
            
            # Nếu số đánh không phải 2 chữ số -> giữ nguyên, bỏ qua
            if len(so_danh_clean) != 2:
                output.append(token)
                i += 1
                continue
            
            # Tìm từ khóa và số tiền phía sau (bỏ qua khoảng trắng)
            j = i + 1
            space_tokens = []
            while j < len(tokens) and re.match(r'^\s+$', tokens[j]):
                space_tokens.append(tokens[j])
                j += 1
            
            if j >= len(tokens):
                output.append(token)
                i += 1
                continue
            
            next_token = tokens[j]
            
            # Trường hợp A: next_token có dạng "keyword + số tiền + đơn vị" (vd: b50n, lô100n)
            match_a = re.match(r'^([a-zA-Z_đ]+)(\d+([.,]\d+)?)([kn])?$', next_token)
            if match_a:
                keyword = match_a.group(1)
                so_tien = match_a.group(2)
                unit = match_a.group(4) or 'n'
                
                if keyword in EXCLUDED or keyword not in KEYWORDS:
                    output.append(token)
                    i += 1
                    continue
                
                new_tien = tinh_tien(so_tien)
                if new_tien is None:
                    output.append(token)
                    i += 1
                    continue
                
                # Giữ nguyên dấu cách giữa số đánh và từ khóa
                output.append(so_danh)
                for sp in space_tokens:
                    output.append(sp)
                output.append(keyword + new_tien + unit)
                i = j + 1
                continue
            
            # Trường hợp B: next_token là từ khóa đứng riêng (vd: lô, d, b)
            if next_token in KEYWORDS and next_token not in EXCLUDED:
                keyword = next_token
                # Tìm số tiền phía sau (bỏ qua khoảng trắng)
                k = j + 1
                space_tokens2 = []
                while k < len(tokens) and re.match(r'^\s+$', tokens[k]):
                    space_tokens2.append(tokens[k])
                    k += 1
                
                if k < len(tokens):
                    next_token2 = tokens[k]
                    match_b = re.match(r'^(\d+([.,]\d+)?)([kn])?$', next_token2)
                    if match_b:
                        so_tien = match_b.group(1)
                        unit = match_b.group(3) or 'n'
                        new_tien = tinh_tien(so_tien)
                        if new_tien is not None:
                            output.append(so_danh)
                            for sp in space_tokens:
                                output.append(sp)
                            output.append(keyword)
                            for sp in space_tokens2:
                                output.append(sp)
                            output.append(new_tien + unit)
                            i = k + 1
                            continue
            
            # Nếu không khớp -> giữ nguyên số
            output.append(token)
            i += 1
            continue
        
        # Các token khác giữ nguyên
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

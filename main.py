import os
import pathlib
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import yt_dlp

# ==========================================
# 🔑 استاد جی، آپ کی چابیاں یہاں لگ گئی ہیں
# ==========================================
TELEGRAM_TOKEN = "7690264234:AAEe1YNQQMu5xikVIB-Rcg6nJVklYAuOPvc"
GEMINI_API_KEY = "AIzaSyBKzLzA8PFwzY9SqDDlOYp1tho_yI3AvF8"

# جیمنی کی کنفیگریشن
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 🌐 Flask Server (بوٹ کو 24 گھنٹے جاگتا رکھنے کے لیے)
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return "استاد جی کی وائرل فیکٹری چل رہی ہے! 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 📥 ویڈیو ڈاؤنلوڈر (yt-dlp)
# ==========================================
def download_video(url, output_path="video.mp4"):
    if os.path.exists(output_path):
        os.remove(output_path)
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best',
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# ==========================================
# 🤖 ٹیلی گرام میسج ہینڈلر
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or ("http" not in text):
        await update.message.reply_text("استاد جی! براہ کرم فیس بک یا ٹک ٹاک کی ویڈیو کا لنک بھیجیں۔ 🚀")
        return

    msg = await update.message.reply_text("⏳ لنک مل گیا! فیکٹری ویڈیو ڈاؤنلوڈ کر رہی ہے...")
    video_path = "video.mp4"
    
    try:
        # 1. ویڈیو ڈاؤنلوڈ کریں
        download_video(text, video_path)
        await msg.edit_text("🎥 ویڈیو ڈاؤنلوڈ ہو گئی! اب گوگل کا دماغ اپلوڈ بائی پاس کر کے اسے چیک کر رہا ہے...")

        # 2. گوگل کو ڈائریکٹ ڈیٹا بھیجیں (401 ایرر بائی پاس ٹرک)
        video_data = {
            "mime_type": "video/mp4",
            "data": pathlib.Path(video_path).read_bytes()
        }
        
        prompt = "اس ویڈیو کو غور سے دیکھو اور فیس بک اور ٹک ٹاک کے لیے ایک زبردست، وائرل اور پرکشش پرامپٹ (کیپشن اور ہیش ٹیگز کے ساتھ) لکھو۔"
        
        # 3. جیمنی سے وائرل پرامپٹ لکھوائیں
        response = model.generate_content([prompt, video_data])
        
        # 4. رزلٹ واپس بھیجیں
        await msg.edit_text(f"🔥 **یہ لیں آپ کا ماسٹر پرامپٹ:**\n\n{response.text}")

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "UNAUTHENTICATED" in error_msg:
            await msg.edit_text("❌ استاد جی! گوگل نے اس `AQ.` والی چابی کو پوری طرح بلاک کر دیا ہے۔ آپ کو پرانے طریقے سے `AIza` والی چابی ہی نکالنی پڑے گی (Service Account والا ڈبہ خالی چھوڑ کر)۔")
        else:
            await msg.edit_text(f"❌ مسئلہ ہو گیا:\n{error_msg}")
            
    finally:
        # صفائی (تاکہ سرور فل نہ ہو)
        if os.path.exists(video_path):
            os.remove(video_path)

# ==========================================
# 🚀 مین فنکشن (بوٹ سٹارٹر)
# ==========================================
def main():
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

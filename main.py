import os
import pathlib
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import yt_dlp

# ==========================================
# 🔑 چابیاں اب تجوری (Environment Variables) سے آئیں گی
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# جیمنی کی کنفیگریشن (لیٹسٹ 2.5 ماڈل کے ساتھ)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 🌐 سرور کو 24 گھنٹے جاگتا رکھنے کے لیے (Flask)
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return "استاد جی کی وائرل فیکٹری فل سپیڈ پر چل رہی ہے! 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 📥 ویڈیو ڈاؤنلوڈر 
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
# 🤖 ٹیلی گرام مین فنکشن
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or ("http" not in text):
        await update.message.reply_text("استاد جی! براہ کرم فیس بک یا ٹک ٹاک کی ویڈیو کا لنک بھیجیں۔ 🚀")
        return

    if not GEMINI_API_KEY or not TELEGRAM_TOKEN:
        await update.message.reply_text("❌ استاد جی! رینڈر کی تجوری میں چابیاں (Environment Variables) غائب ہیں۔")
        return

    msg = await update.message.reply_text("⏳ لنک مل گیا! فیکٹری ویڈیو ڈاؤنلوڈ کر رہی ہے...")
    video_path = "video.mp4"
    
    try:
        download_video(text, video_path)
        await msg.edit_text("🎥 ویڈیو مل گئی! جیمنی 2.5 ویڈیو کا ایکسرے (X-Ray) کر رہا ہے (تھوڑا انتظار کریں)...")

        # ویڈیو کا ڈیٹا ڈائریکٹ میموری میں (401 ایرر بائی پاس)
        video_data = {
            "mime_type": "video/mp4",
            "data": pathlib.Path(video_path).read_bytes()
        }
        
        # 🔥 نیا ماسٹر پرامپٹ (انگلش اور پوری تفصیل کے ساتھ)
        prompt = """
        Watch this video carefully and provide an extremely detailed, scene-by-scene breakdown. 
        Act like a professional film director and observer. 
        Describe everything in absolute detail:
        - Camera angles and movements (pan, zoom, close-up, wide shot).
        - Every single action, movement, and expression of the people or subjects.
        - Background details, objects, environment, houses, weather, and lighting.
        - Any spoken words, text on screen, or specific sounds you can identify.
        Leave nothing out. I want an X-ray level of detail of what is happening in the video.
        
        Finally, at the end, provide a highly engaging, viral caption along with trending hashtags for Facebook and TikTok based on this video.
        
        IMPORTANT: The entire response MUST be written in English.
        """
        
        response = model.generate_content([prompt, video_data])
        await msg.edit_text(f"🔥 **یہ لیں آپ کی ویڈیو کی مکمل تفصیل:**\n\n{response.text}")

    except Exception as e:
        await msg.edit_text(f"❌ مسئلہ ہو گیا:\n{str(e)}")
            
    finally:
        # سرور پر کچرا جمع نہ ہو
        if os.path.exists(video_path):
            os.remove(video_path)

# ==========================================
# 🚀 بوٹ سٹارٹر
# ==========================================
def main():
    if not TELEGRAM_TOKEN:
        print("❌ ٹیلی گرام ٹوکن غائب ہے!")
        return
    
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

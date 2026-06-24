import os
import time
import yt_dlp
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# 🔑 چابیاں (Keys) - Render کے Environment Variables سے آئیں گی
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 24 گھنٹے جاگنے والا سرور (Flask) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "استاد جی، فیکٹری 24 گھنٹے لائیو ہے! 🚀"

def run_server():
    web_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()
# ---------------------------------------

# ✅ نیا صحیح طریقہ - AQ. والی key کے لیے
genai.configure(api_key=GEMINI_API_KEY)

# 🎬 ماسٹر پرامپٹ
SYSTEM_PROMPT = """
You are the "Viral Master Prompt Engine", an elite Hollywood-level video director and social media expert.
Analyze this video perfectly and generate a highly detailed, cinematic MASTER PROMPT specifically optimized and tailored for **Google Veo 3.1 and Seedance.2**.

Structure your response EXACTLY like this:
---
🎯 NICHE & AUDIENCE
[Identify the niche and target audience]

🎬 VEO 3.1 & SEEDANCE.2 MASTER PROMPT
[Write a highly detailed, continuous cinematic prompt. Include: Camera Angle, Lighting, Subject details, Setting, Emotion, and Action. Use highly descriptive visual keywords suitable for these specific AI models.]

🧬 STORYTELLING DNA
[Explain why this video went viral in 1-2 lines]
---
Do not add any other conversational text. Just give me the pure Master Prompt format.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    if "http" not in url:
        await context.bot.send_message(chat_id=chat_id, text="استاد جی، کوئی فیس بک، ٹک ٹاک یا یوٹیوب کا لنک بھیجیں! 🚀")
        return

    await context.bot.send_message(chat_id=chat_id, text="⏳ لنک مل گیا! ویڈیو ڈاؤنلوڈ کر کے AI کو بھیج رہا ہوں...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'temp_video.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    try:
        # ✅ Step 1: ویڈیو ڈاؤنلوڈ کریں
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await context.bot.send_message(chat_id=chat_id, text="🎥 ویڈیو آ گئی! اب AI اسے سمجھ رہا ہے...")

        # ✅ Step 2: ویڈیو اپلوڈ کریں نئے SDK سے
        video_file = genai.upload_file(
            path="temp_video.mp4",
            mime_type="video/mp4"
        )

        # ✅ Step 3: Processing کا انتظار کریں
        while True:
            file_info = genai.get_file(video_file.name)
            state = str(file_info.state)
            if "ACTIVE" in state:
                break
            elif "FAILED" in state:
                raise Exception("گوگل اس ویڈیو کو پروسیس نہیں کر سکا۔")
            time.sleep(4)

        # ✅ Step 4: Master Prompt بنائیں
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([SYSTEM_PROMPT, video_file])

        await context.bot.send_message(chat_id=chat_id, text=response.text)

        # ✅ Step 5: Cleanup
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
        genai.delete_file(video_file.name)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ مسئلہ ہو گیا استاد جی: {str(e)}")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")

def main():
    keep_alive()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 فیکٹری چالو ہو گئی ہے! بوٹ 24 گھنٹے کے لیے لائیو ہے...")
    app.run_polling()

if __name__ == "__main__":
    main()

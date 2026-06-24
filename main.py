import os
import time
import yt_dlp
from google import genai
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# 🔑 چابیاں (Keys)
TELEGRAM_TOKEN = "7690264234:AAFOHa0hy-J2oPfuTCuxI4rJ4flByeLWWgQ"
GEMINI_API_KEY = "AQ.Ab8RN6KoxJVsgcQ8gOVtk_cgCbvsr7ggutNtOMD8xk6LaJksyg"

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

client = genai.Client(api_key=GEMINI_API_KEY)

# 🎬 آپ کا پسندیدہ پرانا ماسٹر پرامپٹ (Veo 3.1 & Seedance.2)
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await context.bot.send_message(chat_id=chat_id, text="🎥 ویڈیو آ گئی! اب گوگل کا دماغ اسے سمجھ رہا ہے (اس میں 10 سے 20 سیکنڈ لگ سکتے ہیں)...")

        # 1. ویڈیو اپلوڈ کریں
        video_file = client.files.upload(file="temp_video.mp4")
        
        # 2. ⏳ جب تک گوگل پروسیسنگ ختم نہ کرے، انتظار کریں (400 ایرر کا پکا علاج)
        while True:
            video_file = client.files.get(name=video_file.name)
            state = str(video_file.state)
            if "ACTIVE" in state:
                break 
            elif "FAILED" in state:
                raise Exception("گوگل اس ویڈیو کو پروسیس نہیں کر سکا۔")
            time.sleep(4) 

        # 3. پرامپٹ تیار کروائیں
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[SYSTEM_PROMPT, video_file]
        )

        await context.bot.send_message(chat_id=chat_id, text=response.text)

        os.remove("temp_video.mp4")
        client.files.delete(name=video_file.name)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ مسئلہ ہو گیا استاد جی: {str(e)}")

def main():
    keep_alive()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 فیکٹری چالو ہو گئی ہے! بوٹ 24 گھنٹے کے لیے لائیو ہے...")
    app.run_polling()

if __name__ == "__main__":
    main()

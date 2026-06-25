import os
import google.generativeai as genai
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import asyncio
import yt_dlp
import time
import threading
import json

# 🔑 Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # https://viral-prompt-bot-new.onrender.com

# Gemini configure
genai.configure(api_key=GEMINI_API_KEY)

# Flask app
flask_app = Flask(__name__)

# Telegram Application
ptb_app = Application.builder().token(TELEGRAM_TOKEN).build()

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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await context.bot.send_message(chat_id=chat_id, text="🎥 ویڈیو آ گئی! اب AI اسے سمجھ رہا ہے...")

        video_file = genai.upload_file(path="temp_video.mp4", mime_type="video/mp4")

        while True:
            file_info = genai.get_file(video_file.name)
            state = str(file_info.state)
            if "ACTIVE" in state:
                break
            elif "FAILED" in state:
                raise Exception("گوگل اس ویڈیو کو پروسیس نہیں کر سکا۔")
            time.sleep(4)

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([SYSTEM_PROMPT, video_file])
        await context.bot.send_message(chat_id=chat_id, text=response.text)

        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")
        genai.delete_file(video_file.name)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ مسئلہ ہو گیا استاد جی: {str(e)}")
        if os.path.exists("temp_video.mp4"):
            os.remove("temp_video.mp4")

# ✅ Webhook route - Telegram یہاں messages بھیجے گا
@flask_app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    asyncio.run(ptb_app.process_update(update))
    return 'OK', 200

# ✅ Webhook set کرنے کا route
@flask_app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/webhook"
    bot = Bot(token=TELEGRAM_TOKEN)
    result = asyncio.run(bot.set_webhook(url=webhook_url))
    if result:
        return jsonify({"status": "✅ Webhook لگ گئی!", "url": webhook_url})
    else:
        return jsonify({"status": "❌ Webhook نہیں لگی"})

@flask_app.route('/')
def home():
    return "استاد جی، فیکٹری 24 گھنٹے لائیو ہے! 🚀"

async def init_app():
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await ptb_app.initialize()
    await ptb_app.start()

if __name__ == "__main__":
    asyncio.run(init_app())
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

import os
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify
import yt_dlp
import time
import threading
import asyncio

# 🔑 Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Flask app
flask_app = Flask(__name__)
flask_app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Global event loop
loop = asyncio.new_event_loop()

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

async def process_video(chat_id, url):
    ydl_opts = {
        'format': 'best[filesize<20M]/best',
        'outtmpl': f'temp_video_{chat_id}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    video_path = None
    uploaded = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # فائل ڈھونڈو
        for ext in ['mp4', 'webm', 'mkv', 'avi']:
            path = f'temp_video_{chat_id}.{ext}'
            if os.path.exists(path):
                video_path = path
                break

        if not video_path:
            raise Exception("ویڈیو ڈاؤنلوڈ نہیں ہوئی۔")

        await ptb_app.bot.send_message(chat_id=chat_id, text="🎥 ویڈیو آ گئی! اب AI اسے سمجھ رہا ہے...")

        with open(video_path, "rb") as f:
            video_bytes = f.read()

        uploaded = client.files.upload(
            file=video_bytes,
            config=types.UploadFileConfig(mime_type="video/mp4")
        )

        while True:
            file_info = client.files.get(name=uploaded.name)
            state = str(file_info.state)
            if "ACTIVE" in state:
                break
            elif "FAILED" in state:
                raise Exception("گوگل اس ویڈیو کو پروسیس نہیں کر سکا۔")
            time.sleep(4)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_uri(file_uri=uploaded.uri, mime_type="video/mp4"),
                types.Part.from_text(SYSTEM_PROMPT)
            ]
        )

        await ptb_app.bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        await ptb_app.bot.send_message(chat_id=chat_id, text=f"❌ مسئلہ ہو گیا استاد جی: {str(e)}")
    finally:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if uploaded:
            try:
                client.files.delete(name=uploaded.name)
            except:
                pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    if "http" not in url:
        await context.bot.send_message(chat_id=chat_id, text="استاد جی، کوئی فیس بک، ٹک ٹاک یا یوٹیوب کا لنک بھیجیں! 🚀")
        return

    await context.bot.send_message(chat_id=chat_id, text="⏳ لنک مل گیا! ویڈیو ڈاؤنلوڈ کر کے AI کو بھیج رہا ہوں...")

    # Background میں چلاؤ — webhook timeout نہیں ہوگا
    asyncio.run_coroutine_threadsafe(process_video(chat_id, url), loop)

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    asyncio.run_coroutine_threadsafe(ptb_app.process_update(update), loop)
    return 'OK', 200  # فوری OK دو — processing background میں ہوگی

@flask_app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/webhook"
    future = asyncio.run_coroutine_threadsafe(
        ptb_app.bot.set_webhook(url=webhook_url), loop
    )
    result = future.result(timeout=10)
    if result:
        return jsonify({"status": "✅ Webhook لگ گئی!", "url": webhook_url})
    else:
        return jsonify({"status": "❌ Webhook نہیں لگی"})

@flask_app.route('/')
def home():
    return "استاد جی، فیکٹری 24 گھنٹے لائیو ہے! 🚀"

def run_event_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def init_ptb():
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"✅ Webhook لگ گئی: {WEBHOOK_URL}/webhook")

if __name__ == "__main__":
    t = threading.Thread(target=run_event_loop, daemon=True)
    t.start()
    asyncio.run_coroutine_threadsafe(init_ptb(), loop).result()
    print("🚀 بوٹ لائیو ہے!")
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

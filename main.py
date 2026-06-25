import os
import time
import threading
import asyncio
from google import genai
from google.genai import types
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 🔑 Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

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

async def process_video(bot, chat_id, url):
    video_path = f"video_{chat_id}.mp4"
    uploaded = None

    try:
        ydl_opts = {
            'format': 'best[filesize<20M]/best',
            'outtmpl': video_path,
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(video_path):
            raise Exception("ویڈیو ڈاؤنلوڈ نہیں ہوئی۔")

        await bot.send_message(chat_id=chat_id, text="🎥 ویڈیو آ گئی! اب AI اسے سمجھ رہا ہے...")

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

        await bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"❌ مسئلہ ہو گیا: {str(e)}")
    finally:
        if os.path.exists(video_path):
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

    await context.bot.send_message(chat_id=chat_id, text="⏳ لنک مل گیا! ویڈیو ڈاؤنلوڈ ہو رہی ہے...")

    # Background thread میں process کرو
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(process_video(context.bot, chat_id, url))

async def main():
    # پرانی webhook ہٹاؤ
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 بوٹ polling mode میں لائیو ہے!")
    
    await app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message"]
    )

if __name__ == "__main__":
    asyncio.run(main())

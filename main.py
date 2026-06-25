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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 🌐 سرور (Flask)
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
        await msg.edit_text("🎥 ویڈیو مل گئی! جیمنی 2.5 آپ کا سنگل میسج ماسٹر پرامپٹ تیار کر رہا ہے...")

        video_data = {
            "mime_type": "video/mp4",
            "data": pathlib.Path(video_path).read_bytes()
        }
        
        # 🔥 جیمنی کو سختی سے لمٹ کر دیا گیا ہے تاکہ 1 ہی میسج میں آئے
        prompt = """
        Watch this video carefully and reverse-engineer its viral formula to create an "AI System Meta-Prompt".
        
        CRITICAL LIMIT: Your ENTIRE response MUST strictly be UNDER 3500 characters. Be concise, punchy, and highly impactful so it fits perfectly in a single Telegram message. Do not overwrite.

        You MUST strictly output ONLY the exact format below. Do not add any conversational text. 
        CRITICAL: The actual prompt MUST be enclosed inside a markdown code block (using ```text at the start and ``` at the end) so it becomes a tap-to-copy box.

        Your response MUST look EXACTLY like this in English:

        🎯 **Generated Master Prompt:**
        *(Tap the prompt below to copy it!)*

        ```text
        ### MASTER PROMPT - NICHE: [Catchy Niche Title]

        You are now permanently activated as "[Catchy Niche Title] VIRAL ENGINE". Generate UNLIMITED, production-ready video prompts for this niche. Do not exit this role.

        --- CORE IDENTITY ---
        NICHE: [Catchy Niche Title] - [Short description]
        AUDIENCE: [Target audience profile]
        CONTENT STYLE: [3-4 descriptive keywords]

        --- STORYTELLING DNA ---
        1. HOOK (0-1.5s): [Attention grabber]
        2. ESCALATION (1.5-5s): [Tension building]
        3. PAYOFF (5s+): [Climax/Resolution]

        --- 🎬 VEO 3.1 & SEEDANCE.2 MASTER PROMPT ---
        [Write a highly detailed but concise paragraph describing the video for AI generation. Act as a film director. Use cinematic terms (anamorphic lens, Rembrandt lighting, etc.). Vividly describe subjects, emotions, and camera movements. Keep this specific section under 1500 characters.]
        ```
        """
        
        response = model.generate_content([prompt, video_data])
        
        # 🔥 قسطیں ختم! سیدھا ایک ہی میسج ڈلیور
        await msg.edit_text(response.text)

    except Exception as e:
        error_message = str(e)
        if "Message is too long" in error_message:
            await msg.edit_text("❌ مسئلہ: ویڈیو میں اتنی زیادہ ڈیٹیل تھی کہ جیمنی نے لمٹ کراس کر دی۔ براہ کرم کوئی اور چھوٹی ویڈیو ٹرائی کریں یا دوبارہ لنک بھیجیں۔")
        else:
            await msg.edit_text(f"❌ مسئلہ ہو گیا:\n{error_message}")
            
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

def main():
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

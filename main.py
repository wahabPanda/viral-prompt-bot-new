import os
import logging
import asyncio
import yt_dlp
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- SETTINGS ----------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# ------------------------------------------

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

logging.basicConfig(level=logging.INFO)

# AI کو ہدایات (ویڈیو کا تجزیہ کر کے پرومٹ بنانے کے لیے)
ANALYSIS_INSTRUCTION = """
You are an expert AI video prompt engineer for Google Veo 3.1 and Seedance 2.0.

Watch this video carefully and analyze:
- The main subject (animal/person/object)
- Actions and movements
- Camera angles and movement
- Lighting and time of day
- Environment and background
- Visual style and mood
- Colors and atmosphere

Then create TWO ready-to-use prompts to RECREATE a similar video:

🎬 **VEO 3.1 PROMPT (with audio):**
[Write a detailed cinematic prompt including subject, action, camera, 
lighting, environment, style, and audio/sound design. 8 seconds.]

🎬 **SEEDANCE 2.0 PROMPT:**
[Write a detailed cinematic prompt for Seedance.]

📱 **FACEBOOK CAPTION + 15 HASHTAGS:**
[Write an engaging caption with emojis and 15 viral hashtags for USA audience.]

Make everything optimized to go VIRAL on Facebook Reels.
"""


# ویڈیو ڈاؤن لوڈ کرنے والا فنکشن
def download_video(url: str, filename: str = "video.mp4") -> str:
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': filename,
        'overwrites': True,
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filename


# /start کمانڈ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 خوش آمدید!\n\n"
        "🎬 مجھے کوئی بھی Facebook / Instagram / TikTok ویڈیو کا لنک بھیجیں\n\n"
        "میں اسے دیکھ کر آپ کے لیے Veo 3.1 اور Seedance 2.0 کے لیے "
        "تیار پرومٹ بنا دوں گا! ✨"
    )


# لنک ہینڈل کرنے والا فنکشن
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("❌ براہِ کرم درست ویڈیو لنک بھیجیں۔")
        return

    status = await update.message.reply_text("⏳ ویڈیو ڈاؤن لوڈ ہو رہی ہے...")

    video_path = None
    try:
        # 1) ویڈیو ڈاؤن لوڈ
        video_path = await asyncio.to_thread(download_video, url)

        await status.edit_text("🧠 AI ویڈیو کا تجزیہ کر رہی ہے...")

        # 2) Gemini پر اپ لوڈ
        video_file = await asyncio.to_thread(genai.upload_file, video_path)

        # پروسیسنگ مکمل ہونے کا انتظار
        while video_file.state.name == "PROCESSING":
            await asyncio.sleep(3)
            video_file = await asyncio.to_thread(genai.get_file, video_file.name)

        # 3) تجزیہ + پرومٹ بنائیں
        response = await asyncio.to_thread(
            model.generate_content, [video_file, ANALYSIS_INSTRUCTION]
        )

        result = response.text

        # 4) جواب بھیجیں (لمبا ہو تو ٹکڑوں میں)
        await status.delete()
        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i + 4000])

        # فائل صاف کریں
        await asyncio.to_thread(genai.delete_file, video_file.name)

    except Exception as e:
        await status.edit_text(f"❌ خرابی: {str(e)}")
    finally:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)


# مین فنکشن
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("✅ بوٹ چل پڑا ہے...")
    app.run_polling()


if __name__ == "__main__":
    main()

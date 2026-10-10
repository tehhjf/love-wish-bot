import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Render-এর জন্য ডামি ওয়েব সার্ভার
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Video Downloader Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

TELEGRAM_TOKEN = "8929398367:AAHQKIX4DRA9jLG4oOqeL-xHx1kdbsoc1uM"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 *ভিডিও ডাউনলোডার বটে স্বাগতম!*\n\n"
        "যেকোনো ভিডিওর লিংক (Facebook, TikTok, Instagram, YouTube Shorts) "
        "এখানে পাঠান, আমি সরাসরি ভিডিও পাঠিয়ে দেব।"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("অনুগ্রহ করে একটি সঠিক ভিডিও লিংক পাঠান!")
        return

    status_msg = await update.message.reply_text("⏳ ভিডিও ডাউনলোড হচ্ছে, একটু অপেক্ষা করুন...")
    
    output_filename = f"video_{update.message.chat_id}.mp4"

    # yt-dlp কনফিগারেশন (টেলিগ্রামের ফ্রি ৫০ মেগাবাইট লিমিট বজায় রাখতে)
    ydl_opts = {
        'format': 'best[ext=mp4][filesize<48M]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_filename):
            await status_msg.edit_text("📤 টেলিগ্রামে ভিডিও আপলোড হচ্ছে...")
            
            with open(output_filename, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="✅ ডাউনলোড সম্পন্ন!")
            
            os.remove(output_filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("ভিডিওটি ডাউনলোড করা সম্ভব হয়নি। লিংকটি আবার চেক করুন।")

    except Exception as e:
        if os.path.exists(output_filename):
            os.remove(output_filename)
        await status_msg.edit_text(f"একটি সমস্যা হয়েছে: {str(e)[:100]}")

def main():
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("ভিডিও ডাউনলোডার বট চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()

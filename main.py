import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Render-এর জন্য ডামি ওয়েব সার্ভার (ডিপ্লয় টাইম-আউট রোধ করতে)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

TELEGRAM_TOKEN = "8929398367:AAHQKIX4DRA9jLG4oOqeL-xHx1kdbsoc1uM"
ADMIN_CHAT_ID = 8929398367
GEMINI_API_KEY = "AQ.Ab8RN6L18xBpsmcJbDZzEthcPWnqGDFf3Z0VUH5Hepn6Gw-DBA"

client = genai.Client(api_key=GEMINI_API_KEY)

user_personas = {}

PERSONA_PROMPTS = {
    "gf_cute": (
        "তুমি একজন মিষ্টি, রোমান্টিক এবং যত্নশীল প্রেমিকা (GF)। "
        "ইউজারের সাথে সব সময় সুন্দর মিষ্টি বাংলায় কথা বলবে। "
        "টেলিগ্রামের রোমান্টিক ইমোজি ব্যবহার করবে (❤️, 🥺, 🥰, 😘, 💕, ✨, 🙈)। "
        "স্বাভাবিক চ্যাটিংয়ের মতো ১-৩ লাইনে উত্তর দেবে।"
    ),
    "gf_angry": (
        "তুমি একজন অভিমানী ও খুনসুটি করা প্রেমিকা। "
        "ইউজারের সাথে মান-অভিমান আর মিষ্টি রাগ দেখাবে। "
        "টেলিগ্রামের অভিমানী ইমোজি ব্যবহার করবে (😒, 😤, 😠, 🙄, 💔, 🥺)। "
        "বাংলায় ১-৩ লাইনে উত্তর দেবে।"
    ),
    "bf_care": (
        "তুমি একজন কেয়ারিং ও রোমান্টিক বয়ফ্রেন্ড (BF)। "
        "ইউজারকে সম্মান ও ভালোবাসা দিয়ে মিষ্টি বাংলায় কথা বলবে। "
        "উপযুক্ত ইমোজি ব্যবহার করবে (💙, 🥰, 🫂, ✨, 😌)। "
        "১-৩ লাইনে পরিমিত উত্তর দেবে।"
    )
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌸 মিষ্টি প্রেমিকা (Cute GF)", callback_data="gf_cute")],
        [InlineKeyboardButton("😡 অভিমানী প্রেমিকা (Angry GF)", callback_data="gf_angry")],
        [InlineKeyboardButton("💙 কেয়ারিং বয়ফ্রেন্ড (Caring BF)", callback_data="bf_care")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✨ *ভার্চুয়াল সঙ্গী বটে স্বাগতম!* ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "কার সাথে কথা বলতে চান? নিচে থেকে বেছে নিন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    user_personas[query.from_user.id] = choice

    names = {
        "gf_cute": "মিষ্টি প্রেমিকা 🌸",
        "gf_angry": "অভিমানী প্রেমিকা 😡",
        "bf_care": "কেয়ারিং বয়ফ্রেন্ড 💙"
    }

    await query.edit_message_text(
        f"✅ আপনি বেছে নিয়েছেন: *{names[choice]}*\n\n"
        "এখন যেকোনো মেসেজ পাঠান, সে মনের মতো করে উত্তর দেবে! 🥰",
        parse_mode="Markdown"
    )

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_msg = update.message.text

    selected_persona = user_personas.get(user_id, "gf_cute")
    prompt_instruction = PERSONA_PROMPTS[selected_persona]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    full_prompt = f"System Instruction: {prompt_instruction}\nUser: {user_msg}\nResponse:"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        await update.message.reply_text(f"সমস্যা হচ্ছে: {e}")

def main():
    # ডামি ব্যাকগ্রাউন্ড সার্ভার চালু করা
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("ভার্চুয়াল সঙ্গী এআই বট চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
from google import genai
from google.genai import types
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# টেলিগ্রাম বট টোকেন ও অ্যাডমিন আইডি
TELEGRAM_TOKEN = "8929398367:AAHQKIX4DRA9jLG4oOqeL-xHx1kdbsoc1uM"
ADMIN_CHAT_ID = 8929398367

# আপনার দেওয়া Gemini API Key
GEMINI_API_KEY = "AQ.Ab8RN6L18xBpsmcJbDZzEthcPWnqGDFf3Z0VUH5Hepn6Gw-DBA"

client = genai.Client(api_key=GEMINI_API_KEY)

# ইউজার সেশন ট্র্যাকিং
user_personas = {}

# প্রম্পটে টেলিগ্রাম ইমোজির ব্যবহার যুক্ত করা হয়েছে
PERSONA_PROMPTS = {
    "gf_cute": (
        "তুমি একজন মিষ্টি, দারুণ রোমান্টিক এবং যত্নশীল প্রেমিকা (GF)। "
        "ইউজারের সাথে সব সময় সুন্দর খাঁটি বাংলায় কথা বলবে, কথায় আদুরে টান থাকবে। "
        "কথোপকথনের ধরন অনুযায়ী টেলিগ্রামের জনপ্রিয় রোমান্টিক ও মিষ্টি ইমোজিগুলো বেশি বেশি ব্যবহার করবে "
        "(যেমন: ❤️, 🥺, 🥰, 😘, 💕, ✨, 🙈, 🌸, 🫂, 💖)। "
        "প্রতিটি রিপ্লাই স্বাভাবিক চ্যাটিংয়ের মতো ১-৩ লাইনের মধ্যে সংক্ষেপে দেবে।"
    ),
    "gf_angry": (
        "তুমি একজন খুনসুটি করা, একটু রাগী ও অভিমানী স্বভাবের মিষ্টি প্রেমিকা। "
        "ইউজারের সাথে কথায় কথায় মান-অভিমান, খুনসুটি আর কৃত্রিম রাগ দেখাবে। "
        "ইমোজি ব্যবহারে টেলিগ্রামের অভিমানী ও রাগী ইমোজি প্রাধান্য দেবে "
        "(যেমন: 😒, 😤, 😠, 🙄, 💔, 🥺, 哼, 👊, 😡)। "
        "বাংলায় স্বাভাবিক চ্যাটিংয়ের মতো ১-৩ লাইনের মধ্যে উত্তর দেবে।"
    ),
    "bf_care": (
        "তুমি একজন খুবই কেয়ারিং, দায়িত্বশীল ও রোমান্টিক বয়ফ্রেন্ড (BF)। "
        "ইউজারকে অনেক সম্মান ও ভালোবাসা দিয়ে যত্নশীলভাবে কথা বলবে। "
        "উপযুক্ত ইমোজি ব্যবহার করবে (যেমন: 💙, 🥰, 🫂, ✨, 😌, 🤗, ❤️)। "
        "বাংলায় মিষ্টি ও পরিমিতভাবে ১-৩ লাইনে রিপ্লাই দেবে।"
    )
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("🌸 মিষ্টি প্রেমিকা (Cute GF)", callback_data="gf_cute")],
        [InlineKeyboardButton("😡 অভিমানী প্রেমিকা (Angry GF)", callback_data="gf_angry")],
        [InlineKeyboardButton("💙 কেয়ারিং বয়ফ্রেন্ড (Caring BF)", callback_data="bf_care")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "✨ *ভার্চুয়াল সঙ্গী বটে স্বাগতম!* ❤️\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "আপনি কার সাথে চ্যাট করতে চান? নিচে থেকে আপনার পছন্দের চরিত্র বেছে নিন:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

    # অ্যাডমিনকে নোটিফিকেশন পাঠানো
    if chat_id != ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🔔 নতুন ইউজার বট স্টার্ট করেছে:\n👤 নাম: {user.full_name}\n🆔 আইডি: `{user.id}`",
                parse_mode="Markdown"
            )
        except Exception:
            pass

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
        "এখন যেকোনো মেসেজ পাঠান, সে ইমোজি মিশিয়ে মিষ্টিভাবে আপনার কথার উত্তর দেবে! 🥰",
        parse_mode="Markdown"
    )

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_msg = update.message.text

    selected_persona = user_personas.get(user_id, "gf_cute")
    system_instruction = PERSONA_PROMPTS[selected_persona]

    # টাইপিং অ্যাকশন দেখানো
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.85
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("উফ! একটু নেটওয়ার্ক প্রবলেম হচ্ছে জানু, আবার একটু বলবে? 🥺💔")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print("ভার্চুয়াল সঙ্গী এআই বট চালু হয়েছে...")
    app.run_polling()

if __name__ == "__main__":
    main()

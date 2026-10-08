import os
import json
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8699587679:AAHes1-nyxuOz7OgW0omcrsQqszqkLpOofE"
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")

app = FastAPI()
DATA_FILE = "data.json"

# টেলিগ্রামের অফিশিয়াল ভেরিফায়েড এনিমেটেড স্টিকার ফাইল আইডি
STICKER_START = "CAACAgIAAxkBAAEClG5lnRzGfXo0Y5tqG9s-AAGwL_W7EwACCAADwZxgDG8e-7e9b0WnNAQ"   # কিউট ওয়েলকাম লাভ
STICKER_PHOTO_WAIT = "CAACAgIAAxkBAAEClHBlnRzq-Bq_02N0t6-fAAGuM_O9FAACBgADwZxgDOe2_6S7x577NAQ" # লাভ ক্যামেরা/ছবি
STICKER_MSG1_WAIT = "CAACAgIAAxkBAAEClHJlnRz1_5M4-Gv2tL6bAAGzN_Q-FgACDQADwZxgDI0vG2P7Y8S8NAQ"  # প্রেমপত্র লেখার স্টিকার
STICKER_AUDIO_WAIT = "CAACAgIAAxkBAAEClHRlnRz7V3eX5N74vb-dAAG3O_T7HgACDwADwZxgDJc83kL9kM9WNAQ" # মিউজিক হার্ট
STICKER_MSG2_WAIT = "CAACAgIAAxkBAAEClHZlnR0BlG795Qz1vf6dAAG5P_U8JwACEwADwZxgDK-Z0L76p0GgNAQ"  # রোমান্টিক মনের কথা
STICKER_DONE = "CAACAgIAAxkBAAEClHhlnR0I4v6_6eP2vv2bAAG7Q_W9LAACGAADwZxgDC5p6g-9kS_INAQ"       # জমকালো হার্ট ব্লাস্ট

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_sessions = {}

async def reply_with_sticker(update: Update, sticker_id: str, text: str):
    """আগে স্টিকার পাঠাবে, তারপর লেখা পাঠাবে"""
    try:
        await update.message.reply_sticker(sticker=sticker_id)
    except Exception:
        pass
    await update.message.reply_text(text, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"step": 1, "data": {}}
    
    msg = (
        "✨ *ভালোবাসার সারপ্রাইজ পেজ মেকারে স্বাগতম!* 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "আপনার বিশেষ মানুষটির মুখে হাসি ফোটাতে নিচের ধাপগুলো পূরণ করুন।\n\n"
        "📸 *ধাপ ১:* প্রথমে আপনার সঙ্গীর একটি সুন্দর *ছবি* পাঠান:"
    )
    await reply_with_sticker(update, STICKER_START, msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = user_sessions.get(chat_id)

    if not session:
        await update.message.reply_text("✨ নতুন করে শুরু করতে দয়া করে /start লিখুন।")
        return

    step = session["step"]

    # ধাপ ১: ছবি পাওয়ার পর ১ম মেসেজ চাওয়া
    if step == 1:
        file = None
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await photo.get_file()
        elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith("image/"):
            file = await update.message.document.get_file()

        if file:
            session["data"]["photo_url"] = file.file_path
            session["step"] = 2
            
            msg = (
                "🌸 *ছবিটি সফলভাবে নেওয়া হয়েছে!* 🥰\n\n"
                "✍️ *ধাপ ২:* এবার খামের ভেতর চিঠি খোলার সময় টাইপরাইটার অ্যানিমেশনে যে ভালোবাসার কথাটি ফুটবে (১ম মেসেজ), সেটি লিখে পাঠান:"
            )
            await reply_with_sticker(update, STICKER_MSG1_WAIT, msg)
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি সঠিক *ছবি* পাঠান।", parse_mode="Markdown")

    # ধাপ ২: ১ম মেসেজ পাওয়ার পর অডিও চাওয়া
    elif step == 2:
        session["data"]["msg1"] = update.message.text
        session["step"] = 3
        
        msg = (
            "💌 *প্রথম রোমান্টিক চিঠি তৈরি হয়ে গেছে!* ✨\n\n"
            "🎧 *ধাপ ৩:* এবার ব্যাকগ্রাউন্ডে প্লে করার মতো যেকোনো একটি মিষ্টি গান, অডিও ফাইল (.mp3/.wav) বা আপনার নিজের *ভয়েস মেসেজ* পাঠান:"
        )
        await reply_with_sticker(update, STICKER_AUDIO_WAIT, msg)

    # ধাপ ৩: অডিও পাওয়ার পর শেষ মেসেজ চাওয়া
    elif step == 3:
        media = None
        if update.message.audio:
            media = update.message.audio
        elif update.message.voice:
            media = update.message.voice
        elif update.message.document:
            mime = update.message.document.mime_type or ""
            fname = (update.message.document.file_name or "").lower()
            if mime.startswith("audio/") or fname.endswith((".mp3", ".wav", ".m4a", ".ogg", ".aac")):
                media = update.message.document

        if media:
            file = await media.get_file()
            session["data"]["audio_url"] = file.file_path
            session["step"] = 4
            
            msg = (
                "🎵 *অডিও গানটি সফলভাবে যুক্ত হয়েছে!* 🎶\n\n"
                "💍 *ধাপ ৪ (শেষ ধাপ):* এবার ৩য় স্ক্রিনে ছবির নিচে মূল যে মনের কথা বা প্রপোজাল বার্তাটি থাকবে (লাস্ট মেসেজ), সেটি লিখে পাঠান:"
            )
            await reply_with_sticker(update, STICKER_MSG2_WAIT, msg)
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি সঠিক *অডিও গান (.mp3)* বা *ভয়েস মেসেজ* পাঠান।", parse_mode="Markdown")

    # ধাপ ৪: শেষ মেসেজ পাওয়া এবং লিংক দেওয়া
    elif step == 4:
        session["data"]["msg2"] = update.message.text
        token = str(uuid.uuid4())[:8]
        
        all_data = load_data()
        all_data[token] = {
            **session["data"],
            "creator_chat_id": chat_id
        }
        save_data(all_data)

        link = f"{BASE_URL}/{token}"
        del user_sessions[chat_id]

        finish_card = (
            "🎉 *অভিনন্দন! আপনার ম্যাজিকাল সারপ্রাইজ পেজ তৈরি!* 💖\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 *আপনার স্পেশাল লিংক:*\n`{link}`\n\n"
            "✨ *নির্দেশনা:*\n"
            "উপরের লিংকটি কপি করে আপনার ভালোবাসার মানুষের কাছে পাঠিয়ে দিন। সে লিংকে প্রবেশ করলেই এখানে স্বয়ংক্রিয় নোটিফিকেশন চলে আসবে! 🔔\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "❤️ *All the best!* 🌹"
        )
        await reply_with_sticker(update, STICKER_DONE, finish_card)

tg_app = Application.builder().token(TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.ALL, handle_message))

@app.on_event("startup")
async def on_startup():
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()

@app.on_event("shutdown")
async def on_shutdown():
    await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()

@app.get("/{token}", response_class=HTMLResponse)
async def serve_page(token: str):
    data = load_data()
    if token in data:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h2 style='text-align:center;margin-top:20%;color:#ff3366;'>💔 Invalid or Expired Link!</h2>", status_code=404)

@app.get("/api/data/{token}")
async def get_data(token: str):
    data = load_data()
    if token in data:
        return JSONResponse(content=data[token])
    return JSONResponse(content={"error": "Not found"}, status_code=404)

@app.post("/api/notify")
async def notify_creator(request: Request):
    req = await request.json()
    token = req.get("token")
    action = req.get("action")
    data = load_data()

    if token in data:
        chat_id = data[token]["creator_chat_id"]
        if action == "opened":
            await tg_app.bot.send_message(
                chat_id=chat_id, 
                text="🔔 *নোটিফিকেশন:* আপনার পাঠানো সারপ্রাইজ পেজটি এইমাত্র সে ওপেন করেছে! 💖👀",
                parse_mode="Markdown"
            )
        elif action == "yes":
            await tg_app.bot.send_message(
                chat_id=chat_id, 
                text="🎉😍 *বিশাল সুখবর!!* ❤️\nসে আপনার ভালোবাসার প্রস্তাবে *'YES'* চাপ দিয়েছে! 💍🌹✨",
                parse_mode="Markdown"
            )
        elif action == "no":
            await tg_app.bot.send_message(
                chat_id=chat_id, 
                text="🥺 সে 'No' চাপার চেষ্টা করেছে, কিন্তু বাটন তো পালিয়েছে! 🙈",
                parse_mode="Markdown"
            )
        return {"status": "ok"}
    return {"error": "Invalid token"}

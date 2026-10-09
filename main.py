import os
import json
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8699587679:AAHes1-nyxuOz7OgW0omcrsQqszqkLpOofE"
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")

DATA_FILE = "data.json"
user_sessions = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

tg_app = Application.builder().token(TOKEN).concurrent_updates(True).build()

async def auto_keepalive_loop():
    await asyncio.sleep(10)
    while True:
        try:
            await tg_app.bot.get_me()
        except Exception:
            pass
        await asyncio.sleep(180)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"step": 1, "data": {}}
    
    welcome_text = (
        "✨💖 *সাইবার ইমন এর লাভ বটে আপনাকে স্বাগতম!* 💖✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✍️ *ধাপ ১:* আপনার নাম বা ব্র্যান্ডের নাম লিখে পাঠান (যেমন: সাইবার ইমন):"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = user_sessions.get(chat_id)

    if not session:
        user_sessions[chat_id] = {"step": 1, "data": {}}
        welcome_text = (
            "✨💖 *সাইবার ইমন এর লাভ বটে আপনাকে স্বাগতম!* 💖✨\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✍️ *ধাপ ১:* আপনার নাম লিখে পাঠান (যেমন: সাইবার ইমন):"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        return

    step = session["step"]

    # ধাপ ১: প্রেরকের নাম
    if step == 1:
        sender_name = update.message.text
        if sender_name:
            session["data"]["sender_name"] = sender_name.strip()
            session["step"] = 2
            await update.message.reply_text(
                "📸 *ধাপ ২:* এবার আপনার সঙ্গীর সুন্দর একটি *ছবি* পাঠান:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি নাম লিখে পাঠান।")

    # ধাপ ২: ছবি
    elif step == 2:
        file_obj = None
        if update.message.photo:
            file_obj = update.message.photo[-1]
        elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith("image/"):
            file_obj = update.message.document

        if file_obj:
            f = await file_obj.get_file()
            session["data"]["photo_url"] = f.file_path
            session["step"] = 3
            await update.message.reply_text(
                "🌸 *ছবি পাওয়া গেছে!* 🥰✨\n\n"
                "✍️ *ধাপ ৩:* চিঠি খোলার সময় যে লেখাটি অক্ষরে অক্ষরে ভেসে উঠবে (১ম বার্তা), সেটি লিখে পাঠান:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি সঠিক ছবি পাঠান।")

    # ধাপ ৩: ১ম চিঠি বার্তা
    elif step == 3:
        session["data"]["msg1"] = update.message.text
        session["step"] = 4
        await update.message.reply_text(
            "💌 *প্রথম বার্তা সংরক্ষিত হয়েছে!* 🌹\n\n"
            "🎧 *ধাপ ৪:* পেজের ব্যাকগ্রাউন্ডে বাজানোর জন্য অডিও গান (.mp3) বা আপনার *ভয়েস* পাঠান:",
            parse_mode="Markdown"
        )

    # ধাপ ৪: গান/ভয়েস
    elif step == 4:
        media = None
        if update.message.audio:
            media = update.message.audio
        elif update.message.voice:
            media = update.message.voice
        elif update.message.document:
            fname = (update.message.document.file_name or "").lower()
            if fname.endswith((".mp3", ".wav", ".m4a", ".ogg", ".aac")):
                media = update.message.document

        if media:
            f = await media.get_file()
            session["data"]["audio_url"] = f.file_path
            session["step"] = 5
            await update.message.reply_text(
                "🎵 *গান সফলভাবে যুক্ত হয়েছে!* 🎶\n\n"
                "💍 *ধাপ ৫ (শেষ ধাপ):* এবার ৩য় স্ক্রিনে ছবির নিচে মূল মনের কথাটি (লাস্ট মেসেজ) লিখে পাঠান:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি অডিও গান (.mp3) বা ভয়েস পাঠান।")

    # ধাপ ৫: শেষ বার্তা ও লিংক প্রদান
    elif step == 5:
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

        finish_text = (
            "🎉 *আপনার সারপ্রাইজ লিংক তৈরি হয়ে গেছে!* 💖\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 *লিংক:* `{link}`\n\n"
            "এই লিংকটি আপনার বিশেষ মানুষটির সাথে শেয়ার করুন। সে পেজটি ওপেন করলেই এখানে সাথে সাথে নোটিফিকেশন পেয়ে যাবেন! 🔔"
        )
        await update.message.reply_text(finish_text, parse_mode="Markdown")

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.ALL, handle_message))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(drop_pending_updates=True)
    asyncio.create_task(auto_keepalive_loop())
    yield
    await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/{token}", response_class=HTMLResponse)
async def serve_page(token: str):
    data = load_data()
    if token in data:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h2 style='text-align:center;margin-top:20%;color:#ff3366;'>💔 Invalid Link!</h2>", status_code=404)

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
            await tg_app.bot.send_message(chat_id=chat_id, text="🔔 সে আপনার সারপ্রাইজ পেজটি ওপেন করেছে! 💖")
        elif action == "yes":
            await tg_app.bot.send_message(chat_id=chat_id, text="🎉 সে ভালোবাসার প্রস্তাবে 'YES' চাপ দিয়েছে! 💍❤️")
        elif action == "no":
            await tg_app.bot.send_message(chat_id=chat_id, text="💔 সে 'No' চাপ দিয়েছে!")
        return {"status": "ok"}
    return {"error": "Invalid token"}

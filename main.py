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

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"step": 1, "data": {}}
    
    welcome_msg = (
        "✨💖 *ভালোবাসার সারপ্রাইজ পেজ মেকারে স্বাগতম!* 💖✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "আপনার মনের মানুষের জন্য চমৎকার একটি পেজ বানাতে নিচের তথ্যগুলো দিন।\n\n"
        "📸 *ধাপ ১:* প্রথমে আপনার সঙ্গীর একটি সুন্দর *ছবি* পাঠান:"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = user_sessions.get(chat_id)

    if not session:
        await update.message.reply_text("✨ নতুন করে শুরু করতে /start চাপুন।")
        return

    step = session["step"]

    # ধাপ ১: ছবি গ্রহণ
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
                "🌸 *ছবিটি পাওয়া গেছে!* 🥰✨\n\n"
                "✍️ *ধাপ ২:* এবার খামের ভেতর চিঠি খোলার সময় যে লেখাটি টাইপ হয়ে উঠবে (১ম বার্তা), সেটি লিখে পাঠান:"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি সঠিক *ছবি* পাঠান।", parse_mode="Markdown")

    # ধাপ ২: ১ম বার্তা গ্রহণ
    elif step == 2:
        session["data"]["msg1"] = update.message.text
        session["step"] = 3
        
        msg = (
            "💌 *প্রথম বার্তা সংরক্ষিত হয়েছে!* 🌹\n\n"
            "🎧 *ধাপ ৩:* এবার পেজের ব্যাকগ্রাউন্ডে বাজানোর জন্য অডিও গান (.mp3) অথবা ভয়েস মেসেজ পাঠান:"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    # ধাপ ৩: অডিও গ্রহণ
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
                "🎵 *অডিও যোগ করা হয়েছে!* 🎶\n\n"
                "💍 *ধাপ ৪ (শেষ ধাপ):* এবার ৩য় স্ক্রিনে ছবির নিচে মূল যে ভালোবাসার বার্তাটি থাকবে (লাস্ট মেসেজ), সেটি লিখে পাঠান:"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ দয়া করে একটি সঠিক *গান (.mp3)* বা *ভয়েস মেসেজ* পাঠান।", parse_mode="Markdown")

    # ধাপ ৪: লিংক তৈরি
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
            "🎉 *অভিনন্দন! আপনার সারপ্রাইজ লিংক তৈরি হয়ে গেছে!* 💖\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 *স্পেশাল লিংক:*\n`{link}`\n\n"
            "✨ *নির্দেশনা:*\n"
            "এই লিংকটি আপনার ভালোবাসার মানুষের সাথে শেয়ার করুন। সে পেজটি ওপেন করলেই এখানে সাথে সাথে নোটিফিকেশন আসবে! 🔔\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "❤️ *Good Luck!* 🌹"
        )
        await update.message.reply_text(finish_card, parse_mode="Markdown")

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
                text="🔔 *নোটিফিকেশন:* আপনার সারপ্রাইজ পেজটি এইমাত্র সে ওপেন করেছে! 💖👀",
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
                text="🥺 সে 'No' চাপার চেষ্টা করেছে, কিন্তু বাটনটি সরে গেছে! 🙈",
                parse_mode="Markdown"
            )
        return {"status": "ok"}
    return {"error": "Invalid token"}

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
    await update.message.reply_text("স্বাগতম! আপনার সঙ্গীর জন্য সারপ্রাইজ পেজ তৈরি করতে নিচের তথ্যগুলো দিন।\n\nপ্রথমে আপনার সঙ্গীর ছবি পাঠান:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    session = user_sessions.get(chat_id)

    if not session:
        await update.message.reply_text("শুরু করতে /start লিখুন।")
        return

    step = session["step"]

    if step == 1:
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await photo.get_file()
            session["data"]["photo_url"] = file.file_path
            session["step"] = 2
            await update.message.reply_text("ছবি পাওয়া গেছে! এবার টাইপরাইটার অ্যানিমেশনের জন্য প্রথম মেসেজটি লিখুন:")
        else:
            await update.message.reply_text("দয়া করে একটি ছবি পাঠান।")

    elif step == 2:
        session["data"]["msg1"] = update.message.text
        session["step"] = 3
        await update.message.reply_text("প্রথম মেসেজ সংরক্ষিত হয়েছে! এবার অডিও/ভয়েস মেসেজ পাঠান:")

    elif step == 3:
        if update.message.audio or update.message.voice:
            media = update.message.audio or update.message.voice
            file = await media.get_file()
            session["data"]["audio_url"] = file.file_path
            session["step"] = 4
            await update.message.reply_text("অডিও পাওয়া গেছে! এবার খামের ভেতরের মূল লাভ মেসেজটি লিখুন:")
        else:
            await update.message.reply_text("দয়া করে একটি অডিও ফাইল বা ভয়েস মেসেজ পাঠান।")

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
        await update.message.reply_text(f"আপনার স্পেশাল লিংক তৈরি হয়ে গেছে! ❤️\n\n{link}\n\nএই লিংকটি আপনার ভালোবাসার মানুষের সাথে শেয়ার করুন।")

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
    return HTMLResponse(content="<h3>Invalid or Expired Link!</h3>", status_code=404)

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
            await tg_app.bot.send_message(chat_id=chat_id, text="🔔 আপনার পাঠানো সারপ্রাইজ পেজটি খোলা হয়েছে!")
        elif action == "yes":
            await tg_app.bot.send_message(chat_id=chat_id, text="❤️ সুখবর! সে 'Yes' চাপ দিয়েছে!")
        elif action == "no":
            await tg_app.bot.send_message(chat_id=chat_id, text="🥺 সে 'No' চাপ দিয়েছে।")
        return {"status": "ok"}
    return {"error": "Invalid token"}

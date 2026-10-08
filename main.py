import os
import secrets
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# কনফিগারেশন
BOT_TOKEN = "8699587679:AAHes1-nyxuOz7OgW0omcrsQqszqkLpOofE"
ADMIN_CHAT_ID = 8699587679
BASE_URL = "https://your-domain.onrender.com"

# আপলোড ফোল্ডার
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ডেটাবেস
db: Dict[str, Dict[str, Any]] = {}

# স্টেট
STEP_MSG1, STEP_AUDIO, STEP_PHOTO, STEP_MSG2 = range(4)

# বট হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("দুঃখিত, এই বটটি ব্যক্তিগত ব্যবহারের জন্য।")
        return ConversationHandler.END

    context.user_data.clear()
    await update.message.reply_text("আপনার বার্তা লিখুন:")
    return STEP_MSG1

async def get_msg1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["msg1"] = update.message.text
    await update.message.reply_text("অডিও গান সিলেক্ট করুন:")
    return STEP_AUDIO

async def get_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    audio_file = update.message.audio or update.message.voice
    if not audio_file:
        await update.message.reply_text("দয়া করে অডিও ফাইল পাঠান।")
        return STEP_AUDIO

    file_obj = await audio_file.get_file()
    fname = f"audio_{update.effective_chat.id}_{secrets.token_hex(4)}.mp3"
    fpath = os.path.join(UPLOAD_DIR, fname)
    await file_obj.download_to_drive(fpath)

    context.user_data["audio_url"] = f"{BASE_URL}/uploads/{fname}"
    await update.message.reply_text("আপনার পিক দিন:")
    return STEP_PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("দয়া করে একটি ছবি পাঠান।")
        return STEP_PHOTO

    photo = update.message.photo[-1]
    file_obj = await photo.get_file()
    fname = f"pic_{update.effective_chat.id}_{secrets.token_hex(4)}.jpg"
    fpath = os.path.join(UPLOAD_DIR, fname)
    await file_obj.download_to_drive(fpath)

    context.user_data["photo_url"] = f"{BASE_URL}/uploads/{fname}"
    await update.message.reply_text("আপনার লাস্ট বার্তা লিখুন:")
    return STEP_MSG2

async def get_msg2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["msg2"] = update.message.text
    chat_id = update.effective_chat.id

    token = "love" + secrets.token_urlsafe(5).replace("-", "").replace("_", "")
    
    db[token] = {
        "chat_id": chat_id,
        "msg1": context.user_data["msg1"],
        "audio_url": context.user_data["audio_url"],
        "photo_url": context.user_data["photo_url"],
        "msg2": context.user_data["msg2"],
        "opened": False
    }

    unique_link = f"{BASE_URL}/{token}"
    msg = f"আপনার লিংক তৈরি সম্পন্ন:\n{unique_link}"
    await update.message.reply_text(msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("বাতিল করা হয়েছে।")
    return ConversationHandler.END

ptb_app = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        STEP_MSG1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_msg1)],
        STEP_AUDIO: [MessageHandler(filters.AUDIO | filters.VOICE, get_audio)],
        STEP_PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        STEP_MSG2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_msg2)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
ptb_app.add_handler(conv_handler)

# FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.on_event("startup")
async def on_startup

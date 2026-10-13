import os
import json
import uuid
import threading
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import telebot

PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
if not RENDER_URL:
    RENDER_URL = "https://love-wish-bot.onrender.com"

# আপনার নতুন টেলিগ্রাম বট টোকেন
TELEGRAM_TOKEN = "8699587679:AAGvW12Wg-nsvolT9O4VSFQyVPoOI_BxFoU"

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown", threaded=True)
user_data = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_FILE = os.path.join(BASE_DIR, "wishes.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ডাটাবেজ হ্যান্ডলিং
def load_wishes():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_wish_entry(wish_id, data):
    wishes = load_wishes()
    wishes[wish_id] = data
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(wishes, f, ensure_ascii=False)

def get_wish_entry(wish_id):
    wishes = load_wishes()
    return wishes.get(wish_id)

# --- এইচটিটিপি সার্ভার ও ফ্রন্টএন্ড ---
class CustomHTTPHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        if parsed.path.startswith("/uploads/"):
            filename = parsed.path.replace("/uploads/", "")
            return os.path.join(UPLOAD_DIR, filename)
        return super().translate_path(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # YES / NO রেসপন্স
        if parsed.path == "/api/response":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                wish_id = data.get("wish_id")
                choice = data.get("choice", "YES")
                
                wish_info = get_wish_entry(wish_id)
                if wish_info and wish_info.get("creator_chat_id"):
                    target_chat_id = wish_info.get("creator_chat_id")
                    s_name = wish_info.get("from", "Emon")
                    r_name = wish_info.get("to", "Partner")
                    emoji = "💖 [YES চাপ দিয়েছে! 🥰]" if choice == "YES" else "💔 [NO চাপ দিয়েছে... 🥺]"
                    
                    msg_text = (
                        f"🔔 *উইশ পেজ থেকে নতুন রেসপন্স!*\n\n"
                        f"👤 *প্রেরক:* {s_name}\n"
                        f"🎯 *প্রাপক:* {r_name}\n"
                        f"👉 *উত্তর:* *{choice}* {emoji}"
                    )
                    bot.send_message(target_chat_id, msg_text)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                return
            except Exception:
                self.send_response(500)
                self.end_headers()
                return

        # ইউজার থেকে কাস্টম মেসেজ পাঠানো
        if parsed.path == "/api/custom_message":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(post_data)
                wish_id = data.get("wish_id")
                user_msg = data.get("message", "").strip()
                choice = data.get("choice", "")
                
                wish_info = get_wish_entry(wish_id)
                if wish_info and wish_info.get("creator_chat_id") and user_msg:
                    target_chat_id = wish_info.get("creator_chat_id")
                    r_name = wish_info.get("to", "Partner")
                    
                    alert_text = (
                        f"💌 *উইশ পেজ থেকে {r_name} আপনাকে মেসেজ পাঠিয়েছে!*\n\n"
                        f"📝 *মেসেজ:* \"{user_msg}\"\n\n"
                        f"👉 *পছন্দ ছিল:* {choice}"
                    )
                    bot.send_message(target_chat_id, alert_text)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                return
            except Exception:
                self.send_response(500)
                self.end_headers()
                return

        super().do_POST()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path in ["/ping", "/healthz"]:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if parsed.path.startswith("/uploads/"):
            return super().do_GET()

        if parsed.path in ["/wish", "/"]:
            query = urllib.parse.parse_qs(parsed.query)
            wish_id = query.get("id", [""])[0]
            
            data = get_wish_entry(wish_id) if wish_id else None
            if not data:
                data = {
                    "from": query.get("from", ["Emon"])[0],
                    "to": query.get("to", ["Tamanna"])[0],
                    "msg": query.get("msg", ["গুছিয়ে বলতে পারিনা কোন কিছু..!😅\nতবে যতোটুকু পেরেছি\nমনের অন্তরাল থেকে লিখেছি..🤕\nতুমি আমার মস্তিষ্কে থাকা..!\nএক নীরব অনুভূতি,🙂\nভালো লাগা নাকি ভালোবাসা\nতা আমি বলতে পারবো না..!\nতবে এটুকু বলতে পারি\nআমাকে ভালোবেসে\nতুমি কখনো ঠকবে না..!💖"])[0],
                    "pnote": query.get("pnote", ["মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈"])[0],
                    "avatar": "",
                    "wa": "",
                    "tg": "",
                    "audio": ""
                }

            sender_name = data.get("from", "Emon")
            receiver_name = data.get("to", "Tamanna")
            raw_msg = data.get("msg", "")
            proposal_note = data.get("pnote", "মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈")
            avatar_file = data.get("avatar", "")
            wa_num = data.get("wa", "")
            tg_user = data.get("tg", "")
            audio_file = data.get("audio", "")

            # মেসেজের লাইনগুলোকে JSON অ্যারে আকারে পাঠানো
            lines_list = [line.strip() for line in raw_msg.replace("\r\n", "\n").split("\n") if line.strip()]
            lines_json = json.dumps(lines_list, ensure_ascii=False)

            avatar_src = f"/uploads/{avatar_file}" if avatar_file else "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=300&auto=format&fit=crop"
            music_src = f"/uploads/{audio_file}" if audio_file else "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=romantic-love-story-112197.mp3"

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>💖 Special Surprise For You</title>
<link href="https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;600;700&family=Dancing+Script:wght@700&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}}
html,body{{height:100%;width:100%;overflow:hidden;font-family:'Anek Bangla',sans-serif;background:#0d0015;color:#fff;}}

#customBg{{
  position:fixed;inset:0;z-index:0;
  background: radial-gradient(circle at 50% 30%, #46002c 0%, #170024 60%, #07000e 100%);
}}

/* ব্যাকগ্রাউন্ডে বড় স্পন্দিত লাল লাভ */
.giant-heart-bg{{
  position:fixed;top:50%;left:50%;
  transform:translate(-50%,-50%);
  z-index:1;font-size:360px;
  color:rgba(255,45,117,0.22);
  filter:drop-shadow(0 0 80px rgba(255,45,117,0.55));
  animation:heartPulse 2.2s ease-in-out infinite;
  pointer-events:none;user-select:none;
}}
@keyframes heartPulse{{
  0%,100%{{transform:translate(-50%,-50%) scale(1);}}
  50%{{transform:translate(-50%,-50%) scale(1.15);}}
}}

#heartsCanvas{{position:fixed;inset:0;z-index:2;pointer-events:none;}}

/* Step 1: ক্লিন গিফট স্ক্রিন (অপ্রয়োজনীয় লেখা ছাড়া) */
#giftScreen{{
  position:fixed;inset:0;z-index:10;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:25px;text-align:center;transition:opacity 0.8s ease;cursor:pointer;
}}
#giftScreen.hide{{opacity:0;pointer-events:none;}}

.gift-box{{
  position:relative;width:155px;height:155px;cursor:pointer;
  animation:boxShake 1.4s ease-in-out infinite;
  filter:drop-shadow(0 20px 40px rgba(255,45,117,0.85));
  transition:transform 0.3s ease;
}}
.gift-box:hover{{transform:scale(1.08);}}
@keyframes boxShake{{
  0%,100%{{transform:rotate(0) scale(1);}}
  15%{{transform:rotate(-6deg) scale(1.03);}}
  30%{{transform:rotate(6deg) scale(1.05);}}
  45%{{transform:rotate(-4deg) scale(1.03);}}
  60%{{transform:rotate(4deg) scale(1.05);}}
  75%{{transform:rotate(0) scale(1);}}
}}

.gift-lid{{
  position:absolute;top:-12px;left:-10px;width:175px;height:42px;
  background:linear-gradient(135deg,#ff2d75,#ff6b9d);
  border-radius:8px;box-shadow:0 4px 20px rgba(255,45,117,0.7);
  transition:all 0.9s ease;
}}
.gift-lid::before{{
  content:"";position:absolute;top:-22px;left:50%;transform:translateX(-50%);
  width:50px;height:45px;background:linear-gradient(135deg,#ffb3d1,#ff2d75);
  clip-path:polygon(50% 0%, 0% 100%, 50% 75%, 100% 100%);border-radius:0 0 20px 20px;
}}
.gift-box.open .gift-lid{{transform:translateY(-180px) rotate(-45deg);opacity:0;}}

.gift-body{{
  position:absolute;top:30px;left:5px;width:145px;height:125px;
  background:linear-gradient(135deg,#d81b60,#ff4081);border-radius:10px;
  box-shadow:inset 0 0 30px rgba(0,0,0,0.35),0 10px 30px rgba(255,45,117,0.5);overflow:hidden;
}}
.gift-body::before{{
  content:"";position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:22px;height:100%;background:linear-gradient(180deg,#ffe082,#ffb3d1);
}}
.gift-body::after{{
  content:"";position:absolute;top:50%;left:0;transform:translateY(-50%);
  width:100%;height:22px;background:linear-gradient(90deg,#ffe082,#ffb3d1);
}}

/* শুধু এই লেখাটি থাকবে */
.tap-hint{{
  margin-top:40px;font-size:1.15rem;color:#ffe082;
  font-family: 'Anek Bangla', sans-serif;font-weight: 700;
  animation:pulseGlow 2s ease-in-out infinite;
  text-shadow: 0 0 15px rgba(255, 224, 130, 0.7);
}}
@keyframes pulseGlow{{
  0%,100%{{opacity:0.8;transform:scale(1);}}
  50%{{opacity:1;transform:scale(1.05);text-shadow:0 0 25px #ff3d7f;}}
}}

/* Step 2: চিঠি স্ক্রিন */
#wishScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:16px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;overflow-y:auto;
}}
#wishScreen.show{{display:flex;opacity:1;}}

.names-container{{
  display:flex;align-items:center;justify-content:center;gap:16px;
  margin-bottom:14px;width:100%;max-width:380px;
}}
.name-item{{display:flex;flex-direction:column;align-items:center;}}
.from-to{{
  font-family:'Poppins',sans-serif;
  font-size:0.8rem;color:#ffb3d1;letter-spacing:3px;font-weight:700;margin-bottom:2px;
}}
.sender-name, .receiver-name{{
  font-family:'Dancing Script',cursive;font-size:2.5rem;line-height:1.1;
  background:linear-gradient(135deg,#ffffff,#ffb3d1,#ff548e);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 10px rgba(255,45,117,0.4));
}}
.heart-divider{{
  font-size:1.8rem;color:#ff2d75;margin-top:14px;
  filter:drop-shadow(0 0 12px rgba(255,45,117,0.9));
  animation:pulseGlow 1.6s infinite;
}}

/* স্ক্রিনের মাঝে একদম স্থির ফ্রস্টেড গ্লাস বক্স */
.message-box{{
  position:relative;
  max-width:360px;width:92%;
  height: 380px; /* স্থায়ী ফিক্সড উচ্চতা */
  background: rgba(22, 0, 32, 0.45);
  border: 1.8px solid rgba(255, 65, 130, 0.65);
  border-radius: 28px;
  padding: 24px 20px;
  margin-bottom: 18px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 0 35px rgba(255, 45, 117, 0.45), inset 0 0 20px rgba(255, 45, 117, 0.2);
  display: flex;align-items: center;justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}}

.box-heart-bg {{
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 250px; height: 230px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.65;
  filter: drop-shadow(0 0 30px #ff0044) blur(1px);
  animation: heartPulse 2.4s ease-in-out infinite;
}}

/* কালার কম্বিনেশনসহ লাইনের কন্টেইনার */
.typed-text{{
  position: relative;
  z-index: 2;
  font-family: 'Anek Bangla', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.95;
  text-align: center;
  width: 100%;
  max-height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
}}
.typed-text::-webkit-scrollbar{{display:none;}}

.line-gold {{
  color: #ffe082;
  text-shadow: 0 1px 8px rgba(0,0,0,0.9), 0 0 12px rgba(255, 224, 130, 0.6);
  display: block;
  margin-bottom: 2px;
}}
.line-pink {{
  color: #ffffff;
  text-shadow: 0 1px 8px rgba(0,0,0,0.9), 0 0 10px rgba(255, 107, 157, 0.7);
  display: block;
  margin-bottom: 2px;
}}

.next-step-btn{{
  display:none;padding:13px 40px;
  background: linear-gradient(135deg, #ff4081, #ff2d75);
  color: #fff;border: none;border-radius: 50px;
  font-size: 1.05rem;font-weight: 800;
  cursor: pointer;
  box-shadow: 0 8px 30px rgba(255, 45, 117, 0.7);
  animation: pulseGlow 1.8s infinite;
  font-family: 'Poppins', sans-serif;
  letter-spacing: 1.2px;
}}

/* Step 3: Proposal Screen */
#proposalScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:20px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;overflow-y:auto;
}}
#proposalScreen.show{{display:flex;opacity:1;}}

.question-box{{
  max-width:390px;width:100%;
  background: rgba(22, 0, 32, 0.45);
  border: 1.8px solid rgba(255, 65, 130, 0.65);
  border-radius: 28px;padding: 30px 20px;
  backdrop-filter: blur(20px);-webkit-backdrop-filter: blur(20px);
  box-shadow: 0 0 35px rgba(255, 45, 117, 0.45);
  transition: all 0.5s ease;
}}

.profile-avatar-wrap{{
  width:130px;height:130px;margin:0 auto 16px auto;
  border-radius:50%;padding:4px;
  background:linear-gradient(135deg,#ff2d75,#ffe082,#ff6b9d);
  box-shadow:0 0 25px rgba(255,45,117,0.8);
  animation:avatarGlow 2.5s infinite alternate;
}}
@keyframes avatarGlow{{
  0%{{transform:scale(1);box-shadow:0 0 20px rgba(255,45,117,0.6);}}
  100%{{transform:scale(1.04);box-shadow:0 0 35px rgba(255,107,157,0.95);}}
}}

.profile-avatar{{
  width:100%;height:100%;border-radius:50%;object-fit:cover;
  background:#1e002e;display:block;
}}

#topTextsWrap{{transition:all 0.4s ease;}}
.proposal-top-text{{
  font-family: 'Anek Bangla', sans-serif;
  font-size:1.1rem;color:#ffe082;margin-bottom:8px;font-weight:600;
  text-shadow:0 0 10px rgba(255,224,130,0.5);
}}
.question-title{{
  font-family:'Poppins',sans-serif;
  font-size:1.65rem;font-weight:700;color:#ffb3d1;margin-bottom:8px;
}}
.question-sub{{
  font-family: 'Anek Bangla', sans-serif;
  font-size:1rem;color:#f0f0f0;margin-bottom:24px;
}}

.yn-btn-group{{display:flex;justify-content:center;gap:15px;}}
.yn-btn{{
  flex:1;padding:14px;border:none;border-radius:50px;font-size:1.15rem;
  font-weight:bold;cursor:pointer;transition:transform 0.2s;font-family:'Poppins',sans-serif;
}}
.btn-yes{{background:linear-gradient(135deg,#ff2d75,#ff6b9d);color:#fff;box-shadow:0 8px 25px rgba(255,45,117,0.6);}}
.btn-yes:hover{{transform:scale(1.05);}}
.btn-no{{background:rgba(255,255,255,0.15);color:#eee;border:1px solid rgba(255,255,255,0.25);}}

#yesResult{{
  display:none;margin-top:16px;padding:18px 16px;
  background:rgba(255,45,117,0.25);border-radius:20px;border:1.5px solid rgba(255,45,117,0.55);
  animation:fadeInUp 0.6s ease;
}}
#noResult{{
  display:none;margin-top:16px;padding:18px 16px;
  background:rgba(0,0,0,0.6);border-radius:20px;border:1.5px solid rgba(255,255,255,0.25);
  animation:fadeInUp 0.6s ease;
}}

.share-btn-wrap{{display:flex;flex-direction:column;gap:10px;margin-top:15px;}}
.share-btn{{
  padding:12px;border-radius:50px;border:none;color:#fff;font-size:0.95rem;
  font-weight:600;cursor:pointer;display:inline-flex;align-items:center;
  justify-content:center;gap:8px;text-decoration:none;font-family:'Poppins',sans-serif;
}}
.wa-btn{{background:#25D366;box-shadow:0 5px 15px rgba(37,211,102,0.4);}}
.tg-btn{{background:#0088cc;box-shadow:0 5px 15px rgba(0,136,204,0.4);}}

/* কিছু বলতে চাইলে বাটন */
.open-reply-btn{{
  margin-top:15px;width:100%;padding:13px;
  background: linear-gradient(135deg, #ffe082, #ffb3d1);
  color:#150024;border:none;border-radius:50px;font-size:0.98rem;font-weight:700;
  cursor:pointer;font-family:'Anek Bangla',sans-serif;box-shadow:0 4px 20px rgba(255,224,130,0.5);
  animation:pulseGlow 2s infinite;display:flex;align-items:center;justify-content:center;gap:6px;
}}

/* Step 4: নতুন পেজ - মেসেজ লেখার পেজ */
#feedbackPage{{
  position:fixed;inset:0;z-index:20;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:22px;text-align:center;
  background: radial-gradient(circle at 50% 30%, #46002c 0%, #170024 75%, #07000e 100%);
  animation:fadeInUp 0.5s ease;
}}
#feedbackPage.show{{display:flex;}}

.feedback-card{{
  max-width:390px;width:100%;
  background: rgba(22, 0, 32, 0.6);
  border: 1.8px solid rgba(255, 65, 130, 0.65);
  border-radius: 28px;padding: 28px 20px;
  backdrop-filter: blur(25px);-webkit-backdrop-filter: blur(25px);
  box-shadow: 0 0 35px rgba(255, 45, 117, 0.45);
}}

.feedback-card h3{{
  font-family: 'Anek Bangla', sans-serif;font-size:1.35rem;color:#ffe082;margin-bottom:10px;
}}
.feedback-card p{{
  font-family: 'Anek Bangla', sans-serif;font-size:0.95rem;color:#ddd;margin-bottom:20px;line-height:1.6;
}}

.reply-textarea{{
  width:100%;height:120px;border-radius:18px;
  background:rgba(255,255,255,0.08);border:1.5px solid rgba(255,179,209,0.4);
  color:#fff;padding:14px;font-family:'Anek Bangla',sans-serif;font-size:1rem;
  resize:none;outline:none;box-sizing:border-box;margin-bottom:18px;
}}
.reply-textarea:focus{{
  border-color:#ff2d75;box-shadow:0 0 15px rgba(255,45,117,0.5);
}}

.send-reply-btn{{
  width:100%;padding:14px;background:linear-gradient(135deg,#ff2d75,#ff6b9d);
  color:#fff;border:none;border-radius:50px;font-size:1.05rem;font-weight:700;
  cursor:pointer;font-family:'Poppins',sans-serif;box-shadow:0 8px 25px rgba(255,45,117,0.6);
}}
.send-reply-btn:disabled{{opacity:0.6;cursor:not-allowed;}}

#replySuccessAlert{{
  display:none;margin-top:15px;color:#85ffb9;font-weight:700;font-size:1rem;
  font-family:'Anek Bangla',sans-serif;
}}

@keyframes fadeInUp{{
  from{{opacity:0;transform:translateY(30px);}}
  to{{opacity:1;transform:translateY(0);}}
}}
</style>
</head>
<body>

<audio id="bgMusic" src="{music_src}" preload="auto" loop></audio>

<div id="customBg"></div>
<div class="giant-heart-bg" id="giantHeart">❤️</div>
<canvas id="heartsCanvas"></canvas>

<!-- Step 1: ক্লিন গিফট স্ক্রিন -->
<div id="giftScreen">
  <div class="gift-box" id="giftBox">
    <div class="gift-lid"></div>
    <div class="gift-body"></div>
  </div>
  <div class="tap-hint">👆 গিফটটি দেখতে ট্যাপ করুন 🎁</div>
</div>

<!-- Step 2: চিঠি স্ক্রিন -->
<div id="wishScreen">
  <div class="names-container">
    <div class="name-item">
      <div class="from-to">FROM</div>
      <div class="sender-name">{sender_name}</div>
    </div>
    <div class="heart-divider">❤️</div>
    <div class="name-item">
      <div class="from-to">TO</div>
      <div class="receiver-name">{receiver_name}</div>
    </div>
  </div>

  <div class="message-box">
    <svg class="box-heart-bg" viewBox="0 0 100 90">
      <defs>
        <radialGradient id="heartGrad" cx="50%" cy="40%" r="60%">
          <stop offset="0%" stop-color="#ff1a66" stop-opacity="0.95"/>
          <stop offset="60%" stop-color="#e6004c" stop-opacity="0.75"/>
          <stop offset="100%" stop-color="#b3003b" stop-opacity="0.2"/>
        </radialGradient>
      </defs>
      <path fill="url(#heartGrad)" d="M50,85 C50,85 10,55 10,28 C10,12 22,2 35,2 C43,2 48,7 50,12 C52,7 57,2 65,2 C78,2 90,12 90,28 C90,55 50,85 50,85 Z" />
    </svg>

    <div class="typed-text" id="typedText"></div>
  </div>

  <button class="next-step-btn" id="nextStepBtn">NEXT STEP 👉</button>
</div>

<!-- Step 3: Proposal Screen -->
<div id="proposalScreen">
  <div class="question-box">
    <!-- শুধুমাত্র প্রোফাইল ছবি থাকবে -->
    <div class="profile-avatar-wrap">
      <img src="{avatar_src}" alt="Profile" class="profile-avatar">
    </div>
    
    <!-- YES / NO চাপার পর এগুলো গায়েব হয়ে যাবে -->
    <div id="topTextsWrap">
      <div class="proposal-top-text">{proposal_note}</div>
      <div class="question-title">💖 Do you love me? 💖</div>
      <div class="question-sub">মনের সব কথা আজ খুলে বলো... 🙈</div>
      <div class="yn-btn-group" id="btnGroup">
        <button class="yn-btn btn-yes" id="btnYes">YES 🥰</button>
        <button class="yn-btn btn-no" id="btnNo">NO 🥺</button>
      </div>
    </div>

    <!-- YES রেসপন্স কার্ড -->
    <div id="yesResult">
      <h3 style="color:#ffb3d1;font-family:'Anek Bangla',sans-serif;margin-bottom:8px;">Yay! I Love You So Much! ❤️🥰</h3>
      <p style="font-size:0.95rem;color:#fff;margin-bottom:12px;font-family:'Anek Bangla',sans-serif;">তোমার হ্যাঁ বলাটাই আমার জীবনের সেরা অনুভূতি! সারাজীবন পাশে থেকো। 🌸✨</p>
      <div class="share-btn-wrap">
        <a class="share-btn wa-btn" id="waShare" href="#" target="_blank">💬 WhatsApp</a>
        <a class="share-btn tg-btn" id="tgShare" href="#" target="_blank">✈️ Telegram</a>
      </div>
      <button class="open-reply-btn" onclick="openNewPage('YES')">💌 কিছু বলতে চাইলে নিচে ট্যাপ করুন 👉</button>
    </div>

    <!-- NO রেসপন্স কার্ড (কোনো গোলাপের ইমোজি ছাড়া) -->
    <div id="noResult">
      <p style="font-size:1.05rem;line-height:1.8;color:#ffb3d1;font-family:'Anek Bangla',sans-serif;font-weight:600;margin-bottom:12px;">
        তোমার মূল্যবান সময় দিয়ে পড়ার জন্য ধন্যবাদ  যাক ব্যাপার না তুমি হয়তো আমার ভাগ্যে ছিল না🥺
      </p>
      <button class="open-reply-btn" onclick="openNewPage('NO')">💌 কিছু বলতে চাইলে নিচে ট্যাপ করুন 👉</button>
    </div>
  </div>
</div>

<!-- Step 4: মেসেজ লেখার পেজ -->
<div id="feedbackPage">
  <div class="feedback-card">
    <div style="font-size:45px;margin-bottom:10px;">✍️💌</div>
    <h3>মনের কথাটি লিখে পাঠান</h3>
    <p>আপনি যা লিখতে চান তা লিখে নিচে সেন্ড করুন, এটি সরাসরি তার কাছে পৌঁছে যাবে...</p>
    <textarea class="reply-textarea" id="customInputMsg" placeholder="আপনার মনের কথা এখানে লিখুন..."></textarea>
    <button class="send-reply-btn" id="sendCustomBtn" onclick="submitCustomMessage()">SEND MESSAGE 🚀</button>
    <div id="replySuccessAlert">✅ আপনার মেসেজটি সফলভাবে পাঠানো হয়েছে! 💖</div>
  </div>
</div>

<script>
(function(){{
"use strict";

var CURRENT_WISH_ID = "{wish_id}";
var waNumber        = "{wa_num}".replace(/[^0-9]/g, '');
var tgUsername      = "{tg_user}".replace('@', '').trim();
var userLastChoice  = "";

function sendResponseToServer(choice) {{
  if (!CURRENT_WISH_ID) return;
  fetch("/api/response", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify({{ wish_id: CURRENT_WISH_ID, choice: choice }})
  }}).catch(function(){{}});
}}

window.openNewPage = function(choice) {{
  userLastChoice = choice;
  document.getElementById("proposalScreen").style.display = "none";
  document.getElementById("feedbackPage").classList.add("show");
}};

window.submitCustomMessage = function() {{
  var msgText = document.getElementById("customInputMsg").value.trim();
  if(!msgText) {{
    alert("দয়া করে কিছু লিখে তারপর সেন্ড করুন!");
    return;
  }}
  
  var btn = document.getElementById("sendCustomBtn");
  btn.disabled = true;
  btn.textContent = "পাঠানো হচ্ছে...";

  fetch("/api/custom_message", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify({{
      wish_id: CURRENT_WISH_ID,
      choice: userLastChoice,
      message: msgText
    }})
  }})
  .then(function(){{
    btn.style.display = "none";
    document.getElementById("customInputMsg").style.display = "none";
    document.getElementById("replySuccessAlert").style.display = "block";
  }})
  .catch(function(){{
    btn.disabled = false;
    btn.textContent = "SEND MESSAGE 🚀";
  }});
}};

var canvas = document.getElementById("heartsCanvas");
var ctx = canvas.getContext("2d");
var W = canvas.width = window.innerWidth;
var H = canvas.height = window.innerHeight;
var hearts = [];
var heartEmojis = ["❤️","💖","💕","🌸","✨"];

function Heart() {{
  this.x = Math.random() * W;
  this.y = H + 20;
  this.size = 14 + Math.random() * 24;
  this.speedY = 1 + Math.random() * 2;
  this.emoji = heartEmojis[Math.floor(Math.random() * heartEmojis.length)];
}}
Heart.prototype.update = function() {{
  this.y -= this.speedY;
  if(this.y < -30) {{ this.y = H + 20; this.x = Math.random() * W; }}
}};
Heart.prototype.draw = function() {{
  ctx.font = this.size + "px serif";
  ctx.fillText(this.emoji, this.x, this.y);
}};
function loop() {{
  ctx.clearRect(0,0,W,H);
  for(var i=0; i<hearts.length; i++){{ hearts[i].update(); hearts[i].draw(); }}
  requestAnimationFrame(loop);
}}

// লাইন বাই লাইন আলাদা কালারে টাইপিং
var linesData = {lines_json};

function typeLines(lines, callback) {{
  var container = document.getElementById("typedText");
  var lineIdx = 0;

  function processNextLine() {{
    if(lineIdx >= lines.length) {{
      if(callback) callback();
      return;
    }}

    var lineSpan = document.createElement("span");
    // অল্টারনেট কালার (এক লাইন গোল্ডেন, পরের লাইন পিংকিশ-হোয়াইট)
    lineSpan.className = (lineIdx % 2 === 0) ? "line-gold" : "line-pink";
    container.appendChild(lineSpan);

    var text = lines[lineIdx];
    var charIdx = 0;

    function stepChar() {{
      if(charIdx < text.length) {{
        lineSpan.textContent += text.charAt(charIdx);
        charIdx++;
        setTimeout(stepChar, 65);
      }} else {{
        lineIdx++;
        setTimeout(processNextLine, 250);
      }}
    }}
    stepChar();
  }}

  processNextLine();
}}

function openGift() {{
  var giftBox = document.getElementById("giftBox");
  if(giftBox.classList.contains("open")) return;
  giftBox.classList.add("open");

  try {{
    var audio = document.getElementById("bgMusic");
    if(audio) {{ audio.play().catch(function(){{}}); }}
  }} catch(e) {{}}

  for(var i=0; i<25; i++) hearts.push(new Heart());
  loop();

  setTimeout(function(){{
    document.getElementById("giftScreen").classList.add("hide");
    document.getElementById("wishScreen").classList.add("show");
    typeLines(linesData, function(){{
      document.getElementById("nextStepBtn").style.display = "inline-block";
    }});
  }}, 650);
}}

document.getElementById("giftScreen").addEventListener("click", openGift);
document.getElementById("giftBox").addEventListener("click", function(e){{
  e.stopPropagation();
  openGift();
}});

document.getElementById("nextStepBtn").addEventListener("click", function(){{
  document.getElementById("wishScreen").classList.remove("show");
  document.getElementById("proposalScreen").classList.add("show");
}});

// YES ক্লিক ইভেন্ট
document.getElementById("btnYes").addEventListener("click", function(){{
  document.getElementById("topTextsWrap").style.display = "none";
  document.getElementById("yesResult").style.display = "block";
  sendResponseToServer("YES");

  var replyTxt = encodeURIComponent("হ্যাঁ {sender_name}! আমিও তোমাকে ভালোবাসি! ❤️🥰");
  if (waNumber) {{
    document.getElementById("waShare").href = "https://wa.me/" + waNumber + "?text=" + replyTxt;
  }} else {{
    document.getElementById("waShare").href = "https://api.whatsapp.com/send?text=" + replyTxt;
  }}

  if (tgUsername) {{
    document.getElementById("tgShare").href = "https://t.me/" + tgUsername;
  }} else {{
    document.getElementById("tgShare").href = "https://t.me/share/url?url=" + encodeURIComponent(window.location.href) + "&text=" + replyTxt;
  }}
}});

// NO ক্লিক ইভেন্ট
document.getElementById("btnNo").addEventListener("click", function(){{
  document.getElementById("topTextsWrap").style.display = "none";
  document.getElementById("noResult").style.display = "block";
  sendResponseToServer("NO");
}});

}})();
</script>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        else:
            super().do_GET()

def start_server():
    server = HTTPServer(("0.0.0.0", PORT), CustomHTTPHandler)
    server.serve_forever()

# --- বট হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'step': 'SENDER', 'creator_chat_id': chat_id}
    bot.send_message(chat_id, "✨ *উইশ পেজ ক্রিয়েটরে স্বাগতম!* ❤️\n\n১️⃣ প্রথমে *আপনার নাম* লিখে পাঠান:")

@bot.message_handler(content_types=['text', 'photo', 'audio', 'voice', 'document'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_data.get(chat_id, {})
    step = state.get('step')
    text = message.text.strip() if message.text else ""

    if text == "/start":
        user_data[chat_id] = {'step': 'SENDER', 'creator_chat_id': chat_id}
        bot.send_message(chat_id, "✨ *উইশ পেজ ক্রিয়েটরে স্বাগতম!* ❤️\n\n১️⃣ প্রথমে *আপনার নাম* লিখে পাঠান:")
        return

    # ১. আপনার নাম
    if step == 'SENDER' and text:
        user_data[chat_id]['sender'] = text
        user_data[chat_id]['step'] = 'RECEIVER'
        bot.send_message(chat_id, "২️⃣ এবার আপনার *GF এর নাম* লিখে পাঠান:")
        return

    # ২. GF এর নাম
    if step == 'RECEIVER' and text:
        user_data[chat_id]['receiver'] = text
        user_data[chat_id]['step'] = 'CUSTOM_MSG'
        bot.send_message(chat_id, "৩️⃣ উইশ পেজের চিঠির ভেতর *কী লিখতে চান (মেসেজ)* লিখে পাঠান:\n\n_(ডিফল্ট রোমান্টিক টেক্সট রাখতে চাইলে /skip লিখুন)_")
        return

    # ৩. মেসেজ
    if step == 'CUSTOM_MSG' and text:
        if text != "/skip":
            user_data[chat_id]['msg'] = text
        user_data[chat_id]['step'] = 'PROFILE_PIC'
        bot.send_message(chat_id, "৪️⃣ এবার 'Do you love me?' পেজের গোল ফ্রেমের জন্য তার *প্রোফাইল পিক পাঠান (Photo)*:\n\n_(ছবি না দিতে চাইলে /skip লিখুন)_")
        return

    # ৪. প্রোফাইল ফটো
    if step == 'PROFILE_PIC':
        if text == "/skip":
            user_data[chat_id]['avatar'] = ""
            user_data[chat_id]['step'] = 'PROPOSAL_NOTE'
            bot.send_message(chat_id, "৫️⃣ এবার 'Do you love me?' এর ওপরে *কী লিখতে চান* (যেমন কোনো রোমান্টিক কথা) লিখে পাঠান:\n\n_(ডিফল্ট টেক্সট রাখতে চাইলে /skip লিখুন)_")
            return
        elif message.photo:
            file_id = message.photo[-1].file_id
            f_info = bot.get_file(file_id)
            img_bytes = bot.download_file(f_info.file_path)
            avatar_name = f"avatar_{chat_id}.jpg"
            with open(os.path.join(UPLOAD_DIR, avatar_name), "wb") as f:
                f.write(img_bytes)
            user_data[chat_id]['avatar'] = avatar_name
            user_data[chat_id]['step'] = 'PROPOSAL_NOTE'
            bot.send_message(chat_id, "৫️⃣ এবার 'Do you love me?' এর ওপরে *কী লিখতে চান* (যেমন কোনো রোমান্টিক কথা) লিখে পাঠান:\n\n_(ডিফল্ট টেক্সট রাখতে চাইলে /skip লিখুন)_")
            return

    # ৫. 'Do you love me' এর ওপরের লেখা
    if step == 'PROPOSAL_NOTE' and text:
        if text != "/skip":
            user_data[chat_id]['pnote'] = text
        user_data[chat_id]['step'] = 'WHATSAPP'
        bot.send_message(chat_id, "৬️⃣ এবার আপনার *WhatsApp নাম্বার* দিন (যেমন: 017xxxxxxxx):\n\n_(না দিতে চাইলে /skip লিখুন)_")
        return

    # ৬. WhatsApp নাম্বার
    if step == 'WHATSAPP' and text:
        if text != "/skip":
            user_data[chat_id]['wa'] = text
        user_data[chat_id]['step'] = 'TELEGRAM'
        bot.send_message(chat_id, "৭️⃣ এবার আপনার *Telegram ইউজারনেম* পাঠান (যেমন: @yourusername):\n\n_(না দিতে চাইলে /skip লিখুন)_")
        return

    # ৭. Telegram ইউজারনেম
    if step == 'TELEGRAM' and text:
        if text != "/skip":
            user_data[chat_id]['tg'] = text
        user_data[chat_id]['step'] = 'BG_MUSIC'
        bot.send_message(chat_id, "৮️⃣ এবার ব্যাকগ্রাউন্ড মিউজিকের জন্য একটি *অডিও বা MP3 ফাইল পাঠান*:\n\n_(ডিফল্ট রোমান্টিক টিউন রাখতে চাইলে /skip লিখুন)_")
        return

    # ৮. ব্যাকগ্রাউন্ড মিউজিক এবং লিংক তৈরি
    if step == 'BG_MUSIC':
        audio_name = ""
        audio_obj = message.audio or message.voice or (message.document if message.document and "audio" in (message.document.mime_type or "") else None)
        
        if audio_obj:
            bot.send_message(chat_id, "⏳ গানটি প্রসেস করা হচ্ছে এবং শর্ট লিংক তৈরি হচ্ছে...")
            f_info = bot.get_file(audio_obj.file_id)
            audio_bytes = bot.download_file(f_info.file_path)
            audio_name = f"audio_{chat_id}.mp3"
            with open(os.path.join(UPLOAD_DIR, audio_name), "wb") as f:
                f.write(audio_bytes)
        elif text != "/skip":
            bot.send_message(chat_id, "⚠️ দয়া করে একটি সঠিক Audio/MP3 ফাইল পাঠান অথবা বাদ দিতে /skip লিখুন:")
            return

        wish_id = uuid.uuid4().hex[:8]
        wish_entry = {
            "creator_chat_id": chat_id,
            "from": user_data[chat_id].get('sender', 'Emon'),
            "to": user_data[chat_id].get('receiver', 'Tamanna'),
            "msg": user_data[chat_id].get('msg', 'সবসময় তোমার পাশে থাকতে চাই... 💖✨'),
            "avatar": user_data[chat_id].get('avatar', ''),
            "pnote": user_data[chat_id].get('pnote', 'মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈'),
            "wa": user_data[chat_id].get('wa', ''),
            "tg": user_data[chat_id].get('tg', ''),
            "audio": audio_name
        }
        save_wish_entry(wish_id, wish_entry)

        short_link = f"{RENDER_URL}/wish?id={wish_id}"

        bot.send_message(
            chat_id, 
            f"🎉 *আপনার স্পেশাল উইশ পেজ সফলভাবে তৈরি হয়েছে!*\n\n"
            f"🔗 *লিংক:* {short_link}\n\n"
            f"✅ সব নতুন ডিজাইন ও কাস্টমাইজেশন কার্যকর করা হয়েছে।"
        )
        user_data.pop(chat_id, None)
        return

def main():
    threading.Thread(target=start_server, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    main()

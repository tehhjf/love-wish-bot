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

TELEGRAM_TOKEN = "8699587679:AAFVFVjQrP-21R_CxMWS1cxqeQzaBCDjpyc"
ADMIN_CHAT_ID = "8699587679"

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
                    "from": query.get("from", ["ইমন"])[0],
                    "to": query.get("to", ["প্রিয় মানুষ"])[0],
                    "msg": query.get("msg", ["পৃথিবীর সমস্ত সুখ যেন তোমার পদচুম্বন করে। সবসময় তোমার পাশে থাকতে চাই... 💖✨"])[0],
                    "pnote": query.get("pnote", ["মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈"])[0],
                    "avatar": "",
                    "wa": "",
                    "tg": "",
                    "audio": ""
                }

            sender_name = data.get("from", "ইমন")
            receiver_name = data.get("to", "প্রিয় মানুষ")
            custom_msg = data.get("msg", "সবসময় তোমার পাশে থাকতে চাই... 💖✨").replace("\n", "\\n")
            proposal_note = data.get("pnote", "মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈")
            avatar_file = data.get("avatar", "")
            wa_num = data.get("wa", "")
            tg_user = data.get("tg", "")
            audio_file = data.get("audio", "")

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
<!-- প্রিমিয়াম স্টাইলিশ বাংলা ও হ্যান্ডরাইটিং ফন্ট -->
<link href="https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;600;700&family=Galada&family=Dancing+Script:wght@700&family=Poppins:wght@600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}}
html,body{{height:100%;width:100%;overflow:hidden;font-family:'Anek Bangla',sans-serif;background:#0d0015;color:#fff;}}

#customBg{{
  position:fixed;inset:0;z-index:0;
  background: radial-gradient(circle at 50% 30%, #4a0033 0%, #150024 60%, #080010 100%);
}}

.giant-heart-bg{{
  position:fixed;top:50%;left:50%;
  transform:translate(-50%,-50%);
  z-index:1;font-size:360px;
  color:rgba(255,45,117,0.18);
  filter:drop-shadow(0 0 80px rgba(255,45,117,0.5));
  animation:heartPulse 2s ease-in-out infinite;
  pointer-events:none;user-select:none;
}}
@keyframes heartPulse{{
  0%,100%{{transform:translate(-50%,-50%) scale(1);}}
  50%{{transform:translate(-50%,-50%) scale(1.15);}}
}}

#heartsCanvas{{position:fixed;inset:0;z-index:2;pointer-events:none;}}

/* Step 1: Gift Screen */
#giftScreen{{
  position:fixed;inset:0;z-index:10;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:20px;text-align:center;transition:opacity 0.8s ease;cursor:pointer;
}}
#giftScreen.hide{{opacity:0;pointer-events:none;}}

/* প্রিমিয়াম স্টাইলিশ ফন্ট ও সফট গ্লো */
.gift-title{{
  font-family: 'Anek Bangla', sans-serif;
  font-size:1.25rem;
  line-height:1.8;
  color:#fff;
  max-width:360px;
  margin-bottom:30px;
  font-weight:600;
  text-shadow:0 2px 15px rgba(255,45,117,0.95), 0 0 30px rgba(255,107,157,0.5);
  letter-spacing: 0.3px;
}}
.gift-title .first-line {{
  font-family: 'Galada', cursive;
  font-size: 1.45rem;
  color: #ffe082;
  display: block;
  margin-bottom: 6px;
  text-shadow: 0 0 12px rgba(255, 224, 130, 0.7);
}}

.gift-box{{
  position:relative;width:150px;height:150px;cursor:pointer;
  animation:boxShake 1.4s ease-in-out infinite;
  filter:drop-shadow(0 20px 40px rgba(255,45,117,0.8));
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
  position:absolute;top:-12px;left:-10px;width:170px;height:40px;
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
  position:absolute;top:28px;left:5px;width:140px;height:120px;
  background:linear-gradient(135deg,#d81b60,#ff4081);border-radius:10px;
  box-shadow:inset 0 0 30px rgba(0,0,0,0.35),0 10px 30px rgba(255,45,117,0.5);overflow:hidden;
}}
.gift-body::before{{
  content:"";position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:20px;height:100%;background:linear-gradient(180deg,#ffe082,#ffb3d1);
}}
.gift-body::after{{
  content:"";position:absolute;top:50%;left:0;transform:translateY(-50%);
  width:100%;height:20px;background:linear-gradient(90deg,#ffe082,#ffb3d1);
}}

.tap-hint{{
  margin-top:30px;font-size:1.05rem;color:#ffb3d1;
  font-family: 'Anek Bangla', sans-serif;
  font-weight: 600;
  animation:pulseGlow 2s ease-in-out infinite;
}}
@keyframes pulseGlow{{
  0%,100%{{opacity:0.6;transform:scale(1);}}
  50%{{opacity:1;transform:scale(1.05);text-shadow:0 0 20px #ff3d7f;}}
}}

/* Step 2: Wish Letter Screen */
#wishScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:20px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;overflow-y:auto;
}}
#wishScreen.show{{display:flex;opacity:1;}}

.names-container{{margin-bottom:12px;}}
.from-to{{
  font-family:'Poppins',sans-serif;
  font-size:0.85rem;color:#ffb3d1;letter-spacing:3px;text-transform:uppercase;font-weight:600;
}}
.sender-name, .receiver-name{{
  font-family:'Dancing Script',cursive;font-size:2.8rem;
  background:linear-gradient(135deg,#fff,#ffb3d1,#ff2d75);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
}}
.heart-divider{{font-size:1.6rem;margin:3px 0;animation:pulseGlow 1.5s infinite;}}

/* মাঝের নির্বাচিত ফ্রস্টেড গ্লাস বক্স */
.message-box{{
  max-width:480px;width:100%;min-height:140px;
  background: radial-gradient(circle at 50% 50%, rgba(255, 45, 117, 0.25) 0%, rgba(20, 0, 30, 0.75) 85%);
  border: 1.5px solid rgba(255, 45, 117, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius:24px;padding:24px;margin-bottom:20px;
  box-shadow: 0 0 30px rgba(255, 45, 117, 0.35), inset 0 0 15px rgba(255, 45, 117, 0.15);
  position: relative;
  overflow: hidden;
}}

.message-box::before {{
  content: "❤️";
  position: absolute;
  font-size: 140px;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.11;
  pointer-events: none;
  filter: blur(2px);
}}

.typed-text{{
  font-family: 'Anek Bangla', sans-serif;
  font-size:1.1rem;
  line-height:2;
  color:#fff;
  text-align:left;
  word-wrap:break-word;
  white-space:pre-wrap;
  z-index: 2;
  position: relative;
  letter-spacing: 0.2px;
}}

.next-step-btn{{
  display:none;padding:12px 35px;background:linear-gradient(135deg,#ff2d75,#ff6b9d);
  color:#fff;border:none;border-radius:50px;font-size:1.05rem;font-weight:700;
  cursor:pointer;box-shadow:0 8px 30px rgba(255,45,117,0.6);
  animation:pulseGlow 1.8s infinite;font-family:'Poppins',sans-serif;letter-spacing:1px;
}}

/* Step 3: Do you love me + Profile Frame */
#proposalScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:20px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;
}}
#proposalScreen.show{{display:flex;opacity:1;}}

.question-box{{
  max-width:400px;width:100%;
  background: radial-gradient(circle at 50% 50%, rgba(255, 45, 117, 0.22) 0%, rgba(20, 0, 30, 0.75) 85%);
  border: 1.5px solid rgba(255, 45, 117, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius:24px;padding:30px 20px;
  box-shadow: 0 0 30px rgba(255, 45, 117, 0.35);
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

#yesResult{{display:none;margin-top:18px;padding:16px;background:rgba(255,45,117,0.25);border-radius:16px;border:1px solid rgba(255,45,117,0.5);}}
#noResult{{display:none;margin-top:18px;padding:16px;background:rgba(0,0,0,0.5);border-radius:16px;border:1px solid rgba(255,255,255,0.2);}}

.share-btn-wrap{{display:flex;flex-direction:column;gap:10px;margin-top:15px;}}
.share-btn{{
  padding:12px;border-radius:50px;border:none;color:#fff;font-size:0.95rem;
  font-weight:600;cursor:pointer;display:inline-flex;align-items:center;
  justify-content:center;gap:8px;text-decoration:none;font-family:'Poppins',sans-serif;
}}
.wa-btn{{background:#25D366;box-shadow:0 5px 15px rgba(37,211,102,0.4);}}
.tg-btn{{background:#0088cc;box-shadow:0 5px 15px rgba(0,136,204,0.4);}}
</style>
</head>
<body>

<audio id="bgMusic" src="{music_src}" preload="auto" loop></audio>

<div id="customBg"></div>
<div class="giant-heart-bg">❤️</div>
<canvas id="heartsCanvas"></canvas>

<!-- Step 1: স্টাইলিশ ফন্টে শুরুর স্ক্রিন -->
<div id="giftScreen">
  <div class="gift-title">
    <span class="first-line">💌 আপনাকে কেউ একটি স্পেশাল চিঠি পাঠিয়েছে</span>
    তা দেখতে লাভের ওপর ট্যাপ করুন...<br>আশা করি আপনার ভালো লাগবে! 💖✨
  </div>
  <div class="gift-box" id="giftBox">
    <div class="gift-lid"></div>
    <div class="gift-body"></div>
  </div>
  <div class="tap-hint">👆 গিফট বক্সে ট্যাপ করুন 🎁</div>
</div>

<!-- Step 2 -->
<div id="wishScreen">
  <div class="names-container">
    <div class="from-to">FROM</div>
    <div class="sender-name">{sender_name}</div>
    <div class="heart-divider">❤️</div>
    <div class="from-to">TO</div>
    <div class="receiver-name">{receiver_name}</div>
  </div>
  <div class="message-box">
    <div class="typed-text" id="typedText"></div>
  </div>
  <button class="next-step-btn" id="nextStepBtn">NEXT STEP 👉</button>
</div>

<!-- Step 3 -->
<div id="proposalScreen">
  <div class="question-box">
    <div class="profile-avatar-wrap">
      <img src="{avatar_src}" alt="Profile" class="profile-avatar">
    </div>
    
    <div class="proposal-top-text">{proposal_note}</div>
    <div class="question-title">💖 Do you love me? 💖</div>
    <div class="question-sub">মনের সব কথা আজ খুলে বলো... 🙈</div>
    <div class="yn-btn-group" id="btnGroup">
      <button class="yn-btn btn-yes" id="btnYes">YES 🥰</button>
      <button class="yn-btn btn-no" id="btnNo">NO 🥺</button>
    </div>
    <div id="yesResult">
      <h3 style="color:#ffb3d1;font-family:'Anek Bangla',sans-serif;margin-bottom:8px;">Yay! I Love You So Much! ❤️🥰</h3>
      <p style="font-size:0.95rem;color:#fff;margin-bottom:12px;font-family:'Anek Bangla',sans-serif;">তোমার হ্যাঁ বলাটাই আমার জীবনের সেরা অনুভূতি! সারাজীবন পাশে থেকো। 🌸✨</p>
      <div class="share-btn-wrap">
        <a class="share-btn wa-btn" id="waShare" href="#" target="_blank">💬 WhatsApp</a>
        <a class="share-btn tg-btn" id="tgShare" href="#" target="_blank">✈️ Telegram</a>
      </div>
    </div>
    <div id="noResult">
      <h3 style="color:#ff8585;font-family:'Anek Bangla',sans-serif;margin-bottom:8px;">মনটা ভেঙে গেল... 🥺💔😭</h3>
      <p style="font-size:0.95rem;color:#ddd;font-family:'Anek Bangla',sans-serif;">"যাকে আপন ভেবেছিলাম সে-ই না বলে দিল... যাই হোক, ভালো থেকো।" 🥀🌧️</p>
    </div>
  </div>
</div>

<script>
(function(){{
"use strict";

var TG_BOT_TOKEN = "{TELEGRAM_TOKEN}";
var TG_CHAT_ID   = "{ADMIN_CHAT_ID}";
var waNumber     = "{wa_num}".replace(/[^0-9]/g, '');
var tgUsername   = "{tg_user}".replace('@', '').trim();

function sendToTelegramBot(choice) {{
  var emoji = choice === "YES" ? "💖 [YES চাপ দিয়েছে!]" : "💔 [NO চাপ দিয়েছে...]";
  var text = "🔔 *Wish Page Response!*\\n\\n👤 Sender: {sender_name}\\n🎯 Receiver: {receiver_name}\\n👉 Answer: *" + choice + "* " + emoji;
  fetch("https://api.telegram.org/bot" + TG_BOT_TOKEN + "/sendMessage?chat_id=" + TG_CHAT_ID + "&text=" + encodeURIComponent(text) + "&parse_mode=Markdown").catch(function(){{}});
}}

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

var wishMsg = "{custom_msg}";

function typeMsg(text, callback) {{
  var container = document.getElementById("typedText");
  var i = 0;
  function step() {{
    if(i < text.length) {{ 
      container.textContent += text.charAt(i); 
      i++; 
      setTimeout(step, 75); 
    }} else if(callback) {{
      callback();
    }}
  }}
  step();
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
    typeMsg(wishMsg, function(){{
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

document.getElementById("btnYes").addEventListener("click", function(){{
  document.getElementById("btnGroup").style.display = "none";
  document.getElementById("yesResult").style.display = "block";
  sendToTelegramBot("YES");

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

document.getElementById("btnNo").addEventListener("click", function(){{
  document.getElementById("btnGroup").style.display = "none";
  document.getElementById("noResult").style.display = "block";
  sendToTelegramBot("NO");
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
    user_data[chat_id] = {'step': 'SENDER'}
    bot.send_message(chat_id, "✨ *উইশ পেজ ক্রিয়েটরে স্বাগতম!* ❤️\n\n১️⃣ প্রথমে *আপনার নাম* লিখে পাঠান:")

@bot.message_handler(content_types=['text', 'photo', 'audio', 'voice', 'document'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_data.get(chat_id, {})
    step = state.get('step')
    text = message.text.strip() if message.text else ""

    if text == "/start":
        user_data[chat_id] = {'step': 'SENDER'}
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

    # ৩. উইশ মেসেজ
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
            "from": user_data[chat_id].get('sender', 'ইমন'),
            "to": user_data[chat_id].get('receiver', 'প্রিয় মানুষ'),
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
            f"✅ চমৎকার স্টাইলিশ বাংলা ফন্ট সেট করা হয়েছে।"
        )
        user_data.pop(chat_id, None)
        return

def main():
    threading.Thread(target=start_server, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    main()

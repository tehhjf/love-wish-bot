import os
import time
import threading
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import requests

PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
if not RENDER_URL:
    RENDER_URL = "https://love-wish-bot.onrender.com"

TELEGRAM_TOKEN = "8699587679:AAHes1-nyxuOz7OgW0omcrsQqszqkLpOofE"
ADMIN_CHAT_ID = "8699587679"
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

user_states = {}

# --- WEB SERVER ---
class CustomHTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/ping" or parsed.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if parsed.path == "/wish" or parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            query = urllib.parse.parse_qs(parsed.query)
            sender_name = query.get("from", ["EMON"])[0]
            receiver_name = query.get("to", ["MIM"])[0]

            html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<title>💖 Special Surprise For You</title>
<link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&family=Dancing+Script:wght@700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}}
html,body{{height:100%;width:100%;overflow:hidden;font-family:'Hind Siliguri',sans-serif;background:#0d0015;color:#fff;}}

/* রোমান্টিক ডার্ক গ্রেডিয়েন্ট ব্যাকগ্রাউন্ড */
#customBg{{
  position:fixed;inset:0;z-index:0;
  background: radial-gradient(circle at 50% 30%, #4a0033 0%, #150024 60%, #080010 100%);
}}

/* ব্যাকগ্রাউন্ডে বড় উজ্জ্বল স্পন্দিত হার্ট */
.giant-heart-bg{{
  position:fixed;top:50%;left:50%;
  transform:translate(-50%,-50%);
  z-index:1;
  font-size:380px;
  color:rgba(255,45,117,0.18);
  filter:drop-shadow(0 0 80px rgba(255,45,117,0.45));
  animation:heartPulse 2.2s ease-in-out infinite;
  pointer-events:none;
  user-select:none;
}}
@keyframes heartPulse{{
  0%,100%{{transform:translate(-50%,-50%) scale(1);}}
  50%{{transform:translate(-50%,-50%) scale(1.18);}}
}}

#heartsCanvas{{position:fixed;inset:0;z-index:2;pointer-events:none;}}

/* ধাপ ১: গিফট বক্স স্ক্রিন */
#giftScreen{{
  position:fixed;inset:0;z-index:10;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:20px;text-align:center;transition:opacity 0.8s ease;
}}
#giftScreen.hide{{opacity:0;pointer-events:none;}}

.gift-title{{
  font-size:1.15rem;line-height:1.7;color:#fff;
  max-width:340px;margin-bottom:35px;font-weight:400;
  text-shadow:0 0 15px rgba(255,45,117,0.9);
}}
.gift-title b{{color:#ffb3d1;font-weight:700;}}

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

.tap-hint{{margin-top:35px;font-size:0.95rem;color:#ffb3d1;animation:pulseGlow 2s ease-in-out infinite;}}
@keyframes pulseGlow{{
  0%,100%{{opacity:0.6;transform:scale(1);}}
  50%{{opacity:1;transform:scale(1.05);text-shadow:0 0 20px #ff3d7f;}}
}}

/* ধাপ ২: উইশ লেটার স্ক্রিন */
#wishScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:20px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;overflow-y:auto;
}}
#wishScreen.show{{display:flex;opacity:1;}}

.names-container{{margin-bottom:12px;}}
.from-to{{font-size:0.8rem;color:#ffb3d1;letter-spacing:3px;text-transform:uppercase;}}
.sender-name, .receiver-name{{
  font-family:'Dancing Script',cursive;font-size:2.5rem;
  background:linear-gradient(135deg,#fff,#ffb3d1,#ff2d75);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
}}
.heart-divider{{font-size:1.6rem;margin:3px 0;animation:pulseGlow 1.5s infinite;}}

.message-box{{
  max-width:480px;width:100%;min-height:130px;
  background:rgba(255,255,255,0.08);border:1px solid rgba(255,179,209,0.3);
  backdrop-filter:blur(15px);-webkit-backdrop-filter:blur(15px);
  border-radius:20px;padding:22px;margin-bottom:20px;
  box-shadow:0 15px 45px rgba(0,0,0,0.6);
}}
.typed-text{{font-size:1.05rem;line-height:1.8;color:#fff;text-align:left;word-wrap:break-word;white-space:pre-wrap;}}

.next-step-btn{{
  display:none;padding:12px 35px;background:linear-gradient(135deg,#ff2d75,#ff6b9d);
  color:#fff;border:none;border-radius:50px;font-size:1.05rem;font-weight:600;
  cursor:pointer;box-shadow:0 8px 30px rgba(255,45,117,0.6);
  animation:pulseGlow 1.8s infinite;font-family:'Hind Siliguri',sans-serif;
}}

/* ধাপ ৩: ডু ইউ লাভ মি + গোল প্রোফাইল ফ্রেম */
#proposalScreen{{
  position:fixed;inset:0;z-index:9;display:none;flex-direction:column;
  align-items:center;justify-content:center;padding:20px;text-align:center;
  opacity:0;transition:opacity 0.8s ease;
}}
#proposalScreen.show{{display:flex;opacity:1;}}

.question-box{{
  max-width:400px;width:100%;background:rgba(255,255,255,0.08);
  border-radius:24px;padding:30px 20px;border:1px solid rgba(255,179,209,0.35);
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  box-shadow:0 20px 50px rgba(0,0,0,0.65);
}}

/* গোল প্রোফাইল ছবি ফ্রেম */
.profile-avatar-wrap{{
  width:125px;height:125px;margin:0 auto 16px auto;
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

.question-title{{font-size:1.65rem;font-weight:700;color:#ffb3d1;margin-bottom:8px;}}
.question-sub{{font-size:0.95rem;color:#f0f0f0;margin-bottom:24px;}}
.yn-btn-group{{display:flex;justify-content:center;gap:15px;}}
.yn-btn{{
  flex:1;padding:14px;border:none;border-radius:50px;font-size:1.1rem;
  font-weight:bold;cursor:pointer;transition:transform 0.2s;font-family:'Hind Siliguri',sans-serif;
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
  justify-content:center;gap:8px;text-decoration:none;
}}
.wa-btn{{background:#25D366;box-shadow:0 5px 15px rgba(37,211,102,0.4);}}
.tg-btn{{background:#0088cc;box-shadow:0 5px 15px rgba(0,136,204,0.4);}}
</style>
</head>
<body>

<div id="customBg"></div>
<div class="giant-heart-bg">❤️</div>
<canvas id="heartsCanvas"></canvas>

<!-- ধাপ ১: গিফট স্ক্রিন -->
<div id="giftScreen">
  <div class="gift-title">
    💌 তোমাকে চমকে দিতে <b>{sender_name}</b> একটি স্পেশাল চিঠি পাঠিয়েছে...<br><br>খুলতে গিফট বক্সে চাপ দাও 🎁
  </div>
  <div class="gift-box" id="giftBox">
    <div class="gift-lid"></div>
    <div class="gift-body"></div>
  </div>
  <div class="tap-hint">👆 গিফট বক্সে ট্যাপ করুন</div>
</div>

<!-- ধাপ ২: উইশ লেটার -->
<div id="wishScreen">
  <div class="names-container">
    <div class="from-to">From</div>
    <div class="sender-name">{sender_name}</div>
    <div class="heart-divider">❤️</div>
    <div class="from-to">To</div>
    <div class="receiver-name">{receiver_name}</div>
  </div>
  <div class="message-box">
    <div class="typed-text" id="typedText"></div>
  </div>
  <button class="next-step-btn" id="nextStepBtn">পরের ধাপ দেখুন 👉</button>
</div>

<!-- ধাপ ৩: ডু ইউ লাভ মি + গোল ফ্রেম -->
<div id="proposalScreen">
  <div class="question-box">
    
    <!-- গোল ফটো ফ্রেম (প্রয়োজনে যে কেউ নিজের পিক বসাতে পারবে) -->
    <div class="profile-avatar-wrap">
      <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=300&auto=format&fit=crop" alt="Profile" class="profile-avatar" id="partnerAvatar">
    </div>

    <div class="question-title">💖 Do you love me? 💖</div>
    <div class="question-sub">মনের গোপন কথাটি আজ সত্যি করে বলে দাও... 🙈</div>
    
    <div class="yn-btn-group" id="btnGroup">
      <button class="yn-btn btn-yes" id="btnYes">YES 🥰</button>
      <button class="yn-btn btn-no" id="btnNo">NO 🥺</button>
    </div>

    <div id="yesResult">
      <h3 style="color:#ffb3d1;margin-bottom:8px;">Yay! আই লাভ ইউ সো মাচ! ❤️🥰</h3>
      <p style="font-size:0.92rem;color:#fff;margin-bottom:12px;">তোমার হ্যাঁ বলাটাই আমার জীবনের সেরা অনুভূতি! সারাজীবন পাশে থেকো। 🌸✨</p>
      <div class="share-btn-wrap">
        <button class="share-btn wa-btn" id="waShare">💬 WhatsApp-এ বলো</button>
        <button class="share-btn tg-btn" id="tgShare">✈️ Telegram-এ বলো</button>
      </div>
    </div>

    <div id="noResult">
      <h3 style="color:#ff8585;margin-bottom:8px;">মনটা ভেঙে গেল... 🥺💔😭</h3>
      <p style="font-size:0.92rem;color:#ddd;">"যাকে আপন ভেবেছিলাম সে-ই না বলে দিল... যাই হোক, ভালো থেকো।" 🥀🌧️</p>
    </div>
  </div>
</div>

<script>
(function(){{
"use strict";

var TG_BOT_TOKEN = "{TELEGRAM_TOKEN}";
var TG_CHAT_ID   = "{ADMIN_CHAT_ID}";

function sendToTelegramBot(choice) {{
  var emoji = choice === "YES" ? "💖 [YES চাপ দিয়েছে!]" : "💔 [NO চাপ দিয়েছে...]";
  var text = "🔔 *উইশ পেজ রেসপন্স!*\\n\\n👤 প্রেরক: {sender_name}\\n🎯 প্রাপক: {receiver_name}\\n👉 উত্তর: *" + choice + "* " + emoji;
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

var wishMsg = "প্রিয় {receiver_name},\\n\\nপৃথিবীর সমস্ত সুখ যেন তোমার পদচুম্বন করে। তোমার হাসিটাই আমার সবচেয়ে প্রিয় দৃশ্য। তোমার সাথে প্রতিটি মুহূর্ত যেন স্বপ্নের মতো। সবসময় তোমার পাশে থাকতে চাই... 💖✨";

function typeMsg(text, callback) {{
  var container = document.getElementById("typedText");
  var i = 0;
  function step() {{
    if(i < text.length) {{ container.textContent += text.charAt(i); i++; setTimeout(step, 40); }}
    else if(callback) callback();
  }}
  step();
}}

document.getElementById("giftBox").addEventListener("click", function(){{
  this.classList.add("open");
  for(var i=0; i<25; i++) hearts.push(new Heart());
  loop();
  setTimeout(function(){{
    document.getElementById("giftScreen").classList.add("hide");
    document.getElementById("wishScreen").classList.add("show");
    typeMsg(wishMsg, function(){{
      document.getElementById("nextStepBtn").style.display = "inline-block";
    }});
  }}, 700);
}});

document.getElementById("nextStepBtn").addEventListener("click", function(){{
  document.getElementById("wishScreen").classList.remove("show");
  document.getElementById("proposalScreen").classList.add("show");
}});

document.getElementById("btnYes").addEventListener("click", function(){{
  document.getElementById("btnGroup").style.display = "none";
  document.getElementById("yesResult").style.display = "block";
  sendToTelegramBot("YES");
}});

document.getElementById("btnNo").addEventListener("click", function(){{
  document.getElementById("btnGroup").style.display = "none";
  document.getElementById("noResult").style.display = "block";
  sendToTelegramBot("NO");
}});

document.getElementById("waShare").addEventListener("click", function(){{
  window.open("https://api.whatsapp.com/send?text=" + encodeURIComponent("হ্যাঁ {sender_name}! আমিও তোমাকে ভালোবাসি! ❤️🥰"), "_blank");
}});

document.getElementById("tgShare").addEventListener("click", function(){{
  window.open("https://t.me/share/url?url=" + encodeURIComponent(window.location.href) + "&text=" + encodeURIComponent("হ্যাঁ {sender_name}! আমিও তোমাকে ভালোবাসি! ❤️🥰"), "_blank");
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

def send_msg(chat_id, text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=8)
    except Exception:
        pass

# --- বট হ্যান্ডলিং (ছবি ছাড়া মাত্র ২ স্টেপে সরাসরি লিংক দেবে) ---
def bot_loop():
    offset = 0
    while True:
        try:
            res = requests.get(f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25).json()
            if not res.get("ok"):
                time.sleep(1)
                continue
                
            for item in res.get("result", []):
                offset = item["update_id"] + 1
                msg = item.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()
                
                if not chat_id:
                    continue

                if text == "/start":
                    user_states[chat_id] = {"step": "SENDER"}
                    send_msg(chat_id, "✨ *উইশ পেজ ক্রিয়েটরে স্বাগতম!* ❤️\n\nপ্রথমে *আপনার নাম* লিখে পাঠান:")
                    continue

                state = user_states.get(chat_id)
                if not state:
                    continue
                
                step = state.get("step")

                # ধাপ ১: আপনার নাম
                if step == "SENDER" and text:
                    user_states[chat_id]["sender"] = text
                    user_states[chat_id]["step"] = "RECEIVER"
                    send_msg(chat_id, "এবার *যার জন্য উইশ তৈরি করছেন তার নাম* লিখে পাঠান:")
                    continue

                # ধাপ ২: প্রাপকের নাম (নাম লেখা মাত্রই ১ সেকেন্ডে লিংক তৈরি)
                if step == "RECEIVER" and text:
                    sender = state.get("sender", "EMON")
                    receiver = text
                    
                    encoded_s = urllib.parse.quote(sender)
                    encoded_r = urllib.parse.quote(receiver)
                    wish_link = f"{RENDER_URL}/wish?from={encoded_s}&to={encoded_r}"

                    send_msg(chat_id, f"🎉 *আপনার উইশ পেজ সফলভাবে তৈরি হয়েছে!*\n\n🔗 *লিংক:* {wish_link}\n\n💖 লিংকে ঢুকলে চমৎকার হার্ট অ্যানিমেশন এবং প্রপোজাল পেজ দেখতে পাবেন!")
                    user_states.pop(chat_id, None)
                    continue

        except Exception:
            time.sleep(1)

def main():
    threading.Thread(target=start_server, daemon=True).start()
    bot_loop()

if __name__ == "__main__":
    main()

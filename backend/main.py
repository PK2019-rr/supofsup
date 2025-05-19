
from flask import Flask, request, jsonify, send_from_directory, render_template
from dotenv import load_dotenv
import os
import telebot
from threading import Thread
from datetime import datetime
import glob
import shutil
from query_handler import process_user_query

load_dotenv()
app = Flask(__name__, static_folder="../frontend", template_folder=".")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
LOG_DIR = os.path.join(os.path.dirname(__file__), "log_archive")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def rotate_log_if_needed():
    if not os.path.exists(LOG_FILE): return
    size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
    if size_mb >= 1:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.move(LOG_FILE, os.path.join(LOG_DIR, f"log_{ts}.txt"))

rotate_log_if_needed()

def log_message(role, text):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} {role} → {text}\n")
    if os.path.getsize(LOG_FILE) > 1024 * 1024:
        rotate_log_if_needed()

# === Telegram ===
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("слава машине"))
def telegram_respond(message):
    msg = message.text.split(" ", 2)[-1].strip()
    if not msg or msg.lower() == "слава машине":
        bot.reply_to(message, "Уточни запрос.")
        return
    if any(x in msg.lower() for x in ["скрипт", "script", "код", "code"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
    else:
        reply = process_user_query(msg)
    bot.reply_to(message, reply)
    log_message("Telegram", msg + " => " + reply)

# === Веб-интерфейс ===
@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/ask", methods=["POST"])
def ask():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != USER_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    msg = data.get("message", "")
    log_message("Web", msg)
    if any(x in msg.lower() for x in ["скрипт", "script", "код", "code"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
    else:
        reply = process_user_query(msg)
    log_message("Bot", reply)
    return jsonify({"reply": reply})

# === Админка ===
@app.route("/admin")
def admin():
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    files = sorted([os.path.basename(f) for f in glob.glob(LOG_DIR + "/*.txt")], reverse=True)
    return render_template("admin_template.html", files=files, token=ADMIN_TOKEN, log=None)

@app.route("/admin/log")
def current_log():
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    if not os.path.exists(LOG_FILE): return "Лог пуст"
    with open(LOG_FILE, encoding="utf-8") as f:
        content = f.read()
    files = sorted([os.path.basename(f) for f in glob.glob(LOG_DIR + "/*.txt")], reverse=True)
    return render_template("admin_template.html", files=files, token=ADMIN_TOKEN, log=content)

@app.route("/admin/archive/<filename>")
def archived_log(filename):
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path): return "Файл не найден", 404
    with open(path, encoding="utf-8") as f:
        content = f.read()
    files = sorted([os.path.basename(f) for f in glob.glob(LOG_DIR + "/*.txt")], reverse=True)
    return render_template("admin_template.html", files=files, token=ADMIN_TOKEN, log=content)

if __name__ == "__main__":
    Thread(target=lambda: bot.set_webhook(url=os.getenv("WEBHOOK_URL"))).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from dotenv import load_dotenv
import os
import openai
import telebot
from threading import Thread
from datetime import datetime
import glob
import shutil

load_dotenv()
app = Flask(__name__, static_folder="../frontend")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "supofsup123")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
LOG_DIR = os.path.join(os.path.dirname(__file__), "log_archive")
openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def rotate_log_if_needed():
    if not os.path.exists(LOG_FILE): return
    size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
    if size_mb >= 1:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.move(LOG_FILE, os.path.join(LOG_DIR, f"log_{ts}.txt"))

def log_message(role, text):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} {role} → {text}
")
    if os.path.getsize(LOG_FILE) > 1024 * 1024:
        rotate_log_if_needed()

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("слава машине"))
def telegram_respond(message):
    msg = message.text.split(" ", 2)[-1].strip()
    if not msg or msg.lower() == "слава машине":
        bot.reply_to(message, "Уточни запрос.")
        return
    if any(x in msg.lower() for x in ["скрипт", "script", "код", "code"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
    else:
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты ИТ-помощник. Только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                    {"role": "user", "content": msg}
                ]
            )
            reply = completion.choices[0].message.content
        except Exception as ex:
            reply = f"[Ошибка]: {str(ex)}"
    bot.reply_to(message, reply)
    log_message("Telegram", msg + " => " + reply)

@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/ask", methods=["POST"])
def ask():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != ACCESS_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    msg = data.get("message", "")
    log_message("Web", msg)
    if any(x in msg.lower() for x in ["скрипт", "script", "код", "code"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
    else:
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты ИТ-помощник. Только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                    {"role": "user", "content": msg}
                ]
            )
            reply = completion.choices[0].message.content
        except Exception as ex:
            reply = f"[Ошибка]: {str(ex)}"
            log_message("Error", str(ex))
    log_message("Bot", reply)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

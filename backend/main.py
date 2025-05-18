from flask import Flask, request, jsonify, send_from_directory, render_template_string
from dotenv import load_dotenv
import os
import openai
import telebot
from threading import Thread
from datetime import datetime
import glob
import shutil

# === Настройка ===
load_dotenv()
app = Flask(__name__, static_folder="../frontend")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "supofsup123")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
LOG_DIR = os.path.join(os.path.dirname(__file__), "log_archive")
openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === Автоархивация логов ===
def rotate_log_if_needed():
    if not os.path.exists(LOG_FILE): return
    size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
    if size_mb >= 1:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.move(LOG_FILE, os.path.join(LOG_DIR, f"log_{ts}.txt"))
rotate_log_if_needed()

# === Telegram уведомления ===
def notify_telegram(text):
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": 1421610910, "text": text}
        )
    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Error → Ошибка отправки в Telegram: {e}\n")

# === Логирование ===
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
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты ИТ-помощник. Только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                    {"role": "user", "content": msg}
                ]
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"[Ошибка]: {str(e)}"
    if "quota" in str(e).lower() or "$4.5" in str(e):
        notify_telegram("⚠️ Превышение квоты OpenAI: возможны перебои!")
    else:
        notify_telegram(reply)
    log_message("Error", reply)
    bot.reply_to(message, reply)
    log_message("Telegram", msg + " => " + reply)

# === Веб-интерфейс ===
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
        except Exception as e:
            reply = f"[Ошибка]: {str(e)}"
    if "quota" in str(e).lower() or "$4.5" in str(e):
        notify_telegram("⚠️ Превышение квоты OpenAI: возможны перебои!")
    else:
        notify_telegram(reply)
    log_message("Error", reply)
    log_message("Bot", reply)
    return jsonify({"reply": reply})

# === Админка ===
HTML_TEMPLATE = """
<!DOCTYPE html><html><head><meta charset=utf-8><title>SUPofSUP — Админка</title><style>body{font-family:sans-serif;background:#111;color:#eee;padding:20px}pre{background:#222;padding:10px;border-radius:5px;white-space:pre-wrap}a{color:#8cf}</style></head><body><h1>SUPofSUP — Логи</h1><p><a href='/admin/log?token={{token}}'>Текущий лог</a></p><ul>{% for f in files %}<li><a href='/admin/archive/{{f}}?token={{token}}'>{{f}}</a></li>{% endfor %}</ul></body></html>
"""

@app.route("/admin")
def admin():
    if request.args.get("token") != ACCESS_TOKEN:
        return "Access denied", 403
    files = sorted([os.path.basename(f) for f in glob.glob(LOG_DIR + "/*.txt")], reverse=True)
    return render_template_string(HTML_TEMPLATE, files=files, token=ACCESS_TOKEN)

@app.route("/admin/log")
def current_log():
    if request.args.get("token") != ACCESS_TOKEN:
        return "Access denied", 403
    if not os.path.exists(LOG_FILE): return "Лог пуст"
    with open(LOG_FILE, encoding="utf-8") as f:
        return f"<pre>{f.read()}</pre>"

@app.route("/admin/archive/<filename>")
def archived_log(filename):
    if request.args.get("token") != ACCESS_TOKEN:
        return "Access denied", 403
    return send_from_directory(LOG_DIR, filename)

# === Webhook обработка ===
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid request', 403

# === Запуск с установкой webhook ===
if __name__ == "__main__":
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # должен быть задан в .env
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        log_message("System", f"Webhook установлен: {WEBHOOK_URL}")
        notify_telegram(f"🔧 Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        log_message("Error", f"Ошибка установки webhook: {e}")
        notify_telegram(f"❌ Ошибка установки webhook: {e}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
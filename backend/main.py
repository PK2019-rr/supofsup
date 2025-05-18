from flask import Flask, request, jsonify, send_from_directory, render_template_string
from dotenv import load_dotenv
import os
import openai
import telebot
from threading import Thread
from datetime import datetime
import glob
import shutil
import requests
from bs4 import BeautifulSoup


load_dotenv()
app = Flask(__name__, static_folder="../frontend")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
yandex_api_key = os.getenv("yandex_api_key")
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
LOG_DIR = os.path.join(os.path.dirname(__file__), "log_archive")
openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === Поиск в Яндексе ===
def search_in_yandex(query):
    url = "https://xml.yandex.ru/xml?"
    params = {
        "user": os.getenv("YANDEX_API_KEY"),
        "query": query,
        "l10n": "ru",
        "groupby": "none",
        "filter": "none",
        "sortby": "rlv",
        "maxpassages": "5",
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.text  # Возвращаем текст для дальнейшей обработки
    return None

# === Извлечение информации с сайта ===
def scrape_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text()
    return text[:500]  # Берем первые 500 символов для обработки

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
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты ИТ-помощник. Только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                    {"role": "user", "content": msg}
                ]
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"[Ошибка]: {str(e)}"
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
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты ИТ-помощник. Только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                    {"role": "user", "content": msg}
                ]
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = f"[Ошибка]: {str(e)}"
    log_message("Bot", reply)
    return jsonify({"reply": reply})

# === Админка ===
HTML_TEMPLATE = """
<!DOCTYPE html><html><head><meta charset=utf-8><title>SUPofSUP - Админка</title>
<style>body{font-family:sans-serif;background:#111;color:#eee;padding:20px}pre{background:#222;padding:10px;border-radius:5px;white-space:pre-wrap}a{color:#8cf}</style></head><body><h1>SUPofSUP - Логи</h1><p><a href='/admin/log?token={{token}}'>Текущий лог</a></p><ul>{% for f in files %}<li><a href='/admin/archive/{{f}}?token={{token}}'>{{f}}</a></li>{% endfor %}</ul></body></html>
"""

@app.route("/admin")
def admin():
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    files = sorted([os.path.basename(f) for f in glob.glob(LOG_DIR + "/*.txt")], reverse=True)
    return render_template_string(HTML_TEMPLATE, files=files, token=ADMIN_TOKEN)

@app.route("/admin/log")
def current_log():
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    if not os.path.exists(LOG_FILE): return "Лог пуст"
    with open(LOG_FILE, encoding="utf-8") as f:
        return f"<pre>{f.read()}</pre>"

@app.route("/admin/archive/<filename>")
def archived_log(filename):
    if request.args.get("token") != ADMIN_TOKEN:
        return "Access denied", 403
    return send_from_directory(LOG_DIR, filename)

if __name__ == "__main__":
    Thread(target=lambda: bot.set_webhook(url=os.getenv("WEBHOOK_URL"))).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

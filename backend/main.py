from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import openai
import logging
from datetime import datetime
from threading import Thread
import telebot

# Загрузка переменных окружения
load_dotenv()
app = Flask(__name__, static_folder="../frontend")

openai.api_key = os.getenv("OPENAI_API_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Настройка Telegram-бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda msg: msg.text and msg.text.lower().startswith("слава машине"))
def handle_message(message):
    user_input = message.text.split(" ", 2)[-1].strip()
    if not user_input or user_input.lower() == "слава машине":
        bot.reply_to(message, "Молюсь к Cogitator-у. Уточни запрос.")
        return
    if any(x in user_input.lower() for x in ["скрипт", "script", "код", "code", "powershell", "bash", "python"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
        bot.reply_to(message, reply)
        return
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты ИТ-помощник. Отвечай кратко, чётко, только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        reply = f"[Ошибка]: {str(e)}"
    bot.reply_to(message, reply)

# Логирование
log_file = "chat.log"
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 MB

def log_message(role, text):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{now} {role} → {text}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)
    if os.path.getsize(log_file) > MAX_LOG_SIZE:
        os.rename(log_file, log_file.replace(".log", f"_{int(datetime.now().timestamp())}.log"))

# API-запрос
@app.route("/api/ask", methods=["POST"])
def ask():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ")[1] != ACCESS_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    msg = data.get("message", "")

    log_message("User", msg)

    if any(x in msg.lower() for x in ["скрипт", "script", "код", "code", "powershell", "bash", "python"]):
        reply = "Создание и анализ скриптов запрещено согласно декрету Praefecto Ordinis."
        log_message("Bot", reply)
        return jsonify({"reply": reply})

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты ИТ-помощник. Отвечай кратко, чётко, только по теме Windows, Exchange, Outlook, AD. Скрипты запрещены."},
                {"role": "user", "content": msg}
            ]
        )
        reply = completion.choices[0].message.content
        log_message("Bot", reply)
        return jsonify({"reply": reply})
    except Exception as e:
        err = f"[Ошибка]: {str(e)}"
        log_message("Error", err)
        return jsonify({"reply": err}), 500

# Веб-интерфейс
@app.route("/")
def root():
    return send_from_directory(app.static_folder, "index.html")

# Запуск Flask + Telegram
if __name__ == "__main__":
    def run_bot():
        print("Telegram bot запущен...")
        bot.infinity_polling()

    Thread(target=run_bot).start()
    print("Flask-сервер запущен...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

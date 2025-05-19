
import os
import requests
import re
from datetime import datetime

YANDEX_USER = os.getenv("YANDEX_USER")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDERID = os.getenv("YANDEX_FOLDERID")
YANDEX_URL = "https://yandex.ru/search/xml"
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")

MAX_TOKENS = 512

def log_error(message):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} Yandex API Error → {message}\n")

def get_search_summary(query):
    if not YANDEX_USER or not YANDEX_API_KEY or not YANDEX_FOLDERID:
        msg = "YANDEX API ключ, user или folderid не указан."
        log_error(msg)
        return msg

    params = {
        "user": YANDEX_USER,
        "key": YANDEX_API_KEY,
        "query": query,
        "folderid": YANDEX_FOLDERID,
        "l10n": "ru",
        "groupby": "attr=d.mode.flat.groups-on-page=5.docs-in-group=1",
        "sortby": "tm.order=descending",
        "filter": "none",
        "maxpassages": "4"
    }

    try:
        response = requests.get(YANDEX_URL, params=params)
        if response.status_code != 200:
            msg = f"Ошибка Yandex XML API: {response.status_code}"
            log_error(msg)
            return msg

        text = response.text
        snippets = re.findall(r"<passage>(.*?)</passage>", text, re.DOTALL)
        cleaned = [re.sub("<.*?>", "", s).strip() for s in snippets if s.strip()]
        if cleaned:
            return "\n\n".join([f"🔹 {s}" for s in cleaned])
        else:
            msg = "Нет результатов по запросу в Яндексе."
            log_error(msg)
            return msg

    except Exception as e:
        msg = f"Ошибка при обращении к Яндекс API: {str(e)}"
        log_error(msg)
        return msg

def trim_tokens(text, max_tokens=MAX_TOKENS):
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens]) + "..."

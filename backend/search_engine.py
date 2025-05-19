
import requests
from datetime import datetime
import os

API_URL = "https://duckduckgo-search-api.p.rapidapi.com/htmlSearch"
API_HOST = "duckduckgo-search-api.p.rapidapi.com"
API_KEY = "a69dc9ff3bmsh46bf57b8bbea8b6p1ed8dfjsn84ae671d48e7"

LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
MAX_TOKENS = 512

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

def log_debug(prefix, message):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} {prefix} → {message}\n")

def get_search_summary(query):
    try:
        params = {"q": query, "df": "d", "kl": "ru-ru"}
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)

        log_debug("RapidAPI Icons Response", f"Status {response.status_code}")
        log_debug("RapidAPI Icons Raw", response.text[:1000])

        if response.status_code != 200:
            msg = f"Ошибка RapidAPI Icons: {response.status_code}"
            log_debug("RapidAPI Icons Error", msg)
            return msg

        data = response.json()
        results = data.get("results", [])

        if not results:
            msg = "Нет результатов (RapidAPI Icons)"
            log_debug("RapidAPI Icons Empty", msg)
            return msg

        snippets = []
        for res in results[:5]:
            title = res.get("title", "Без заголовка").strip()
            snippet = res.get("description", "Без описания").strip()
            link = res.get("url", "без ссылки")
            icon = res.get("icon", "")
            icon_str = f"[иконка: {icon}]" if icon else ""
            snippets.append(f"🔹 {title} {icon_str}\n{snippet}\nИсточник: {link}")

        return "\n\n".join(snippets)

    except Exception as e:
        msg = f"Ошибка при обращении к RapidAPI Icons: {str(e)}"
        log_debug("RapidAPI Icons Exception", msg)
        return msg

def trim_tokens(text, max_tokens=MAX_TOKENS):
    words = text.split()
    return text if len(words) <= max_tokens else " ".join(words[:max_tokens]) + "..."

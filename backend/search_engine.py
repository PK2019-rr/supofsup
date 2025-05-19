
import requests
import json
from datetime import datetime
import os

API_URL = "https://all-serp.p.rapidapi.com/all-serp-website"
API_HOST = "all-serp.p.rapidapi.com"
API_KEY = "a69dc9ff3bmsh46bf57b8bbea8b6p1ed8dfjsn84ae671d48e7"

LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
MAX_TOKENS = 512

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST,
    "Content-Type": "application/json"
}

def log_debug(prefix, message):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} {prefix} → {message}\n")

def get_search_summary(query):
    try:
        params = {
            "keyword": query,
            "location": "us",
            "language": "en",
            "search_engine": "google",
            "page_limit": 1,
            "search_type": "All"
        }

        response = requests.post(API_URL, headers=HEADERS, params=params, data=json.dumps({"dummy": "value"}), timeout=20)

        log_debug("AllSerp API Response", f"Status {response.status_code}")
        log_debug("AllSerp API Raw", response.text[:1000])

        if response.status_code != 200:
            msg = f"Ошибка AllSerp API: {response.status_code}"
            log_debug("AllSerp API Error", msg)
            return msg

        data = response.json()
        results = data.get("data", {}).get("organic", [])

        if not results:
            msg = "Нет результатов по запросу (AllSerp)"
            log_debug("AllSerp Empty", msg)
            return msg

        snippets = []
        for item in results[:5]:
            title = item.get("title", "Без заголовка").strip()
            snippet = item.get("description", "Без описания").strip()
            link = item.get("url", "без ссылки")
            snippets.append(f"🔹 {title}\n{snippet}\nИсточник: {link}")

        return "\n\n".join(snippets)

    except Exception as e:
        msg = f"Ошибка при обращении к AllSerp: {str(e)}"
        log_debug("AllSerp Exception", msg)
        return msg

def trim_tokens(text, max_tokens=MAX_TOKENS):
    words = text.split()
    return text if len(words) <= max_tokens else " ".join(words[:max_tokens]) + "..."

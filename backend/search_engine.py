
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

DDG_URL = "https://html.duckduckgo.com/html/"
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")

MAX_TOKENS = 512
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def log_debug(prefix, message):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now} {prefix} → {message}\n")

def get_search_summary(query):
    try:
        response = requests.post(DDG_URL, data={"q": query}, headers=HEADERS, timeout=10)
        log_debug("DuckDuckGo HTML Response", f"Status {response.status_code}")
        log_debug("DuckDuckGo HTML Raw", response.text[:1000])

        if response.status_code != 200:
            msg = f"Ошибка DuckDuckGo запроса: {response.status_code}"
            log_debug("DuckDuckGo HTML Error", msg)
            return msg

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.result")

        snippets = []
        for item in results[:5]:
            title_tag = item.select_one("a.result__a")
            snippet_tag = item.select_one("a.result__snippet")
            title = title_tag.text.strip() if title_tag else "Без заголовка"
            snippet = snippet_tag.text.strip() if snippet_tag else "Без описания"
            link = title_tag.get("href") if title_tag and title_tag.has_attr("href") else "без ссылки"
            snippets.append(f"🔹 {title}\n{snippet}\nИсточник: {link}")

        if not snippets:
            msg = "Нет результатов по запросу (DuckDuckGo)."
            log_debug("DuckDuckGo HTML Empty", msg)
            return msg

        return "\n\n".join(snippets)

    except Exception as e:
        msg = f"Ошибка при HTML-парсинге DDG: {str(e)}"
        log_debug("DuckDuckGo HTML Exception", msg)
        return msg

def trim_tokens(text, max_tokens=MAX_TOKENS):
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens]) + "..."

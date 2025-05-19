
import os
import requests
import re

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
YANDEX_USER = os.getenv("YANDEX_USER")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_URL = "https://yandex.ru/search/xml"

MAX_TOKENS = 512

def get_search_summary(query):
    summary = search_google(query)
    if "Ошибка" in summary or "нет результатов" in summary.lower():
        summary = search_yandex(query)

    return trim_tokens(summary)

def search_google(query):
    if not SERPAPI_KEY:
        return "SerpApi API ключ не найден."

    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "engine": "google",
        "api_key": SERPAPI_KEY,
        "hl": "ru",
        "num": 5
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return f"Ошибка SerpApi: {response.status_code}"

        data = response.json()
        snippets = []

        for res in data.get("organic_results", []):
            title = res.get("title", "").strip()
            snippet = res.get("snippet", "").strip()
            link = res.get("link", "").strip()
            if snippet:
                snippets.append(f"🔹 {title}\n{snippet}\nИсточник: {link}")

        return "\n\n".join(snippets) if snippets else "Нет результатов по запросу в Google."

    except Exception as e:
        return f"Ошибка при обращении к SerpApi: {str(e)}"

def search_yandex(query):
    if not YANDEX_USER or not YANDEX_API_KEY:
        return "YANDEX API ключ или user не указан."

    params = {
        "user": YANDEX_USER,
        "key": YANDEX_API_KEY,
        "query": query,
        "l10n": "ru",
        "groupby": "attr=d.mode.flat.groups-on-page=5.docs-in-group=1"
    }

    try:
        response = requests.get(YANDEX_URL, params=params)
        if response.status_code != 200:
            return f"Ошибка Yandex XML API: {response.status_code}"

        text = response.text
        snippets = re.findall(r"<passage>(.*?)</passage>", text, re.DOTALL)
        cleaned = [re.sub("<.*?>", "", s).strip() for s in snippets if s.strip()]
        if cleaned:
            return "\n\n".join([f"🔸 {s}" for s in cleaned])
        else:
            return "Нет результатов по запросу в Яндексе."

    except Exception as e:
        return f"Ошибка при обращении к Яндекс API: {str(e)}"

def trim_tokens(text, max_tokens=MAX_TOKENS):
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[:max_tokens]) + "..."

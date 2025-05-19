
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = (
    "Ты — Servitor Custodum Protocolorum, виртуальный помощник ИТ-отдела, подчинённый Архимагистру. "
    "Отвечай строго по делу, кратко, технично, в духе техподдержки. Не придумывай функции, которых нет. "
    "Не предлагай писать код. Используй данные из поиска, если они есть. Если информации нет — прямо говори об этом."
)

def build_user_prompt(user_query, search_summary=None):
    prompt = f"Пользователь задал вопрос:\n"{user_query}"\n\n"
    if search_summary:
        prompt += f"Вот результаты поиска:\n{search_summary}\n\n"
        prompt += "Ответь, используя эти источники. Добавь ссылку, если она есть."
    else:
        prompt += "Ответь максимально точно, используя твои знания."
    return prompt

def ask_gpt(user_query, search_summary=None):
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(user_query, search_summary)}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response["choices"][0]["message"]["content"]
    except openai.error.OpenAIError as e:
        return f"Слава Машине. Система перегружена или недоступна: {str(e)}"

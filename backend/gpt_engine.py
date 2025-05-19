import openai
import os
from dotenv import load\_dotenv

load\_dotenv()

openai.api\_key = os.getenv("OPENAI\_API\_KEY")

SYSTEM\_PROMPT = (
"Ты — Servitor Custodum Protocolorum, виртуальный помощник ИТ-отдела, подчинённый Архимагистру. "
"Отвечай строго по делу, кратко, технично, в духе техподдержки. Не придумывай функции, которых нет. "
"Не предлагай писать код. Используй данные из поиска, если они есть. Если информации нет — прямо говори об этом."
)

def build\_user\_prompt(user\_query, search\_summary=None):
prompt = f'Пользователь задал вопрос:\n"{user\_query}"\n\n'
if search\_summary:
prompt += f"Вот результаты поиска:\n{search\_summary}\n\n"
prompt += "Ответь, используя эти источники. Добавь ссылку, если она есть."
else:
prompt += "Ответь максимально точно, используя твои знания."
return prompt

def ask\_gpt(user\_query, search\_summary=None):
try:
messages = \[
{"role": "system", "content": SYSTEM\_PROMPT},
{"role": "user", "content": build\_user\_prompt(user\_query, search\_summary)}
]
response = openai.ChatCompletion.create(
model="gpt-4o",
messages=messages,
temperature=0.4,
max\_tokens=1024,
top\_p=1.0,
frequency\_penalty=0,
presence\_penalty=0
)
return response\["choices"]\[0]\["message"]\["content"]
except openai.error.OpenAIError as e:
return f"Слава Машине. Система перегружена или недоступна: {str(e)}"


from gpt_engine import ask_gpt
from search_engine import get_search_summary  # Это заглушка, нужно реализовать отдельно

def process_user_query(user_query):
    # Выполняем поиск по Яндексу и Google (или используем заглушку)
    search_summary = get_search_summary(user_query)

    # Отправляем запрос в GPT
    answer = ask_gpt(user_query, search_summary)
    return answer

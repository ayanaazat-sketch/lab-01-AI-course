"""Parallel test corpus for Lab 01, including the three core extensions.

Each item is in English, Russian and Kazakh. Parallel meaning is the
point: any difference in token count is a property of the tokenizer, not of
what is being said.

Instructors: the Kazakh and Russian wordings are a starting point. Substitute
your own if you prefer -- but keep the three versions semantically parallel,
otherwise the comparison measures translation length instead of tokenization.
"""

from __future__ import annotations

import json
from typing import Dict

LANGUAGES = ("en", "ru", "kk")

#: One sentence. Short enough to inspect token by token.
SENTENCE: Dict[str, str] = {
    "en": "The bank raised interest rates by two percentage points last quarter.",
    "ru": "Банк повысил процентные ставки на два процентных пункта в прошлом квартале.",
    "kk": "Банк өткен тоқсанда пайыздық мөлшерлемені екі пайыздық тармаққа көтерді.",
}

#: A realistic support request -- the kind of text a production system pays for
#: thousands of times a day.
COMPLAINT: Dict[str, str] = {
    "en": (
        "Good afternoon. I opened a deposit at your branch in March and was told "
        "the rate was fixed for twelve months. In August the rate on my account "
        "dropped without any notice. I have attached the contract and the "
        "statement. Please explain on what basis the rate was changed and "
        "restore the original terms."
    ),
    "ru": (
        "Добрый день. Я открыл депозит в вашем отделении в марте, и мне сказали, "
        "что ставка зафиксирована на двенадцать месяцев. В августе ставка по "
        "моему счёту снизилась без какого-либо уведомления. Прилагаю договор и "
        "выписку. Прошу объяснить, на каком основании была изменена ставка, и "
        "восстановить первоначальные условия."
    ),
    "kk": (
        "Қайырлы күн. Мен наурыз айында сіздің бөлімшеңізде депозит аштым, маған "
        "мөлшерлеме он екі айға бекітілген деп айтылды. Тамыз айында менің "
        "шотымдағы мөлшерлеме ешқандай хабарламасыз төмендеді. Шартты және "
        "үзінді көшірмені қоса тіркеп отырмын. Мөлшерлеме қандай негізде "
        "өзгертілгенін түсіндіріп, бастапқы шарттарды қалпына келтіруіңізді "
        "сұраймын."
    ),
}


# Моё дополнение: поздравление клиента с днём рождения.
CLIENT_CONGRATULATIONS: Dict[str, str] = {
    "en": "Dear [Last Name] [First Name] [Patronymic], happy birthday to you!",
    "ru": "Уважаемый(ая) [Фамилия] [Имя] [Отчество], поздравляем вас с днем рождения!",
    "kk": "Құрметті [Тегі] [Аты] [Әкесінің аты], сізді туған күніңізбен құттықтаймыз!",
}

# В первой казахской фразе нет ә ғ қ ң ө ұ ү һ і.
KK_SHARED_LETTERS: Dict[str, str] = {
    "en": "The mother bought apples for her child, and the child played ball outside.",
    "ru": "Мама купила ребёнку яблоки, а ребёнок играл с мячом на улице.",
    "kk": "Ана баласына алма алды, ал бала далада доппен ойнады.",
}

# Фразы близки по длине. Смысл внутри каждой тройки EN/RU/KK одинаковый,
# но между двумя тройками разный: это небольшой пример, а не строгий эксперимент.
KK_SPECIFIC_LETTERS: Dict[str, str] = {
    "en": "The grandmother told a story near the house, and the girl watered the flowers.",
    "ru": "Бабушка рассказывала историю возле дома, а девочка поливала цветы.",
    "kk": "Әже үйдің қасында әңгіме айтты, қыз гүлдерді суарды.",
}

#: A system prompt -- the part you resend on every single request.
SYSTEM_PROMPT: Dict[str, str] = {
    "en": (
        "You are a support assistant for a retail bank. Answer only from the "
        "documents provided. If the answer is not in them, say so. Never invent "
        "an account number, a rate or a date."
    ),
    "ru": (
        "Вы — ассистент поддержки розничного банка. Отвечайте только по "
        "предоставленным документам. Если ответа в них нет, так и скажите. "
        "Никогда не выдумывайте номер счёта, ставку или дату."
    ),
    "kk": (
        "Сіз — бөлшек банктің қолдау көрсету ассистентісіз. Тек берілген "
        "құжаттар бойынша жауап беріңіз. Егер жауап оларда болмаса, солай деп "
        "айтыңыз. Шот нөмірін, мөлшерлемені немесе күнді ешқашан ойдан "
        "шығармаңыз."
    ),
}


# Те же пять предложений, но каждое лежит в своём поле JSON.
# Ключи и формат JSON одинаковые для всех языков; смысл жалобы сохранён целиком.
def complaint_to_json(text: str) -> str:
    fields = ("greeting", "deposit", "rate_change", "attachments", "request")
    sentences = [part + "." for part in text.removesuffix(".").split(". ")]
    if len(sentences) != len(fields):
        raise ValueError("В исходной жалобе должно быть ровно пять предложений.")
    return json.dumps(
        dict(zip(fields, sentences)), ensure_ascii=False, separators=(",", ":")
    )


COMPLAINT_JSON: Dict[str, str] = {
    lang: complaint_to_json(COMPLAINT[lang]) for lang in LANGUAGES
}

CORPUS: Dict[str, Dict[str, str]] = {
    "sentence": SENTENCE,
    "complaint": COMPLAINT,
    "system_prompt": SYSTEM_PROMPT,
    "client_congratulations": CLIENT_CONGRATULATIONS,
    "kk_shared_letters": KK_SHARED_LETTERS,
    "kk_specific_letters": KK_SPECIFIC_LETTERS,
    "complaint_json": COMPLAINT_JSON,
}

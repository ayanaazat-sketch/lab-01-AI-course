"""Проверка core tasks 1–3: python core_tasks.py.

Это локальные измерения tiktoken, а не токены Claude или Gemini.
При первом запуске tiktoken может скачать словари. API-ключ не нужен.
"""

import argparse
import json
from importlib.metadata import version
from pathlib import Path

import tiktoken

from texts import CORPUS, LANGUAGES


KAZAKH_LETTERS = set("әғқңөұүһі")
TOKENIZERS = ("o200k_base", "cl100k_base")


def token_counts(item, encoding):
    return {lang: len(encoding.encode(item[lang])) for lang in LANGUAGES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).parent / "results" / "core_metrics.json",
    )
    args = parser.parse_args()
    encodings = {name: tiktoken.get_encoding(name) for name in TOKENIZERS}
    results = {
        "tiktoken_version": version("tiktoken"),
        "task3_prediction_note": "Для сравнения prose/JSON прогноз до измерений не найден; здесь только результаты.",
        "task1": {}, "task2": {}, "task3": {},
    }

    print("TASK 1 — поздравление клиента")
    print("Токенизатор        EN   RU   KK    RU/EN    KK/EN")
    for name, encoding in encodings.items():
        counts = token_counts(CORPUS["client_congratulations"], encoding)
        ru_ratio = counts["ru"] / counts["en"]
        kk_ratio = counts["kk"] / counts["en"]
        results["task1"][name] = {
            "tokens": counts, "ru_en_ratio": ru_ratio, "kk_en_ratio": kk_ratio,
        }
        print(f"{name:<17} {counts['en']:>3} {counts['ru']:>4} {counts['kk']:>4}"
              f" {ru_ratio:>8.3f} {kk_ratio:>8.3f}")

    print("\nTASK 2 — две казахские фразы")
    for item_id in ("kk_shared_letters", "kk_specific_letters"):
        text = CORPUS[item_id]["kk"]
        specific_count = sum(letter in KAZAKH_LETTERS for letter in text.lower())
        if item_id == "kk_shared_letters" and specific_count:
            raise ValueError("В первой фразе обнаружены казахские специальные буквы.")
        stats = {
            "text": text,
            "chars": len(text),
            "bytes": len(text.encode("utf-8")),
            "bytes_per_char": len(text.encode("utf-8")) / len(text),
            "kazakh_specific_letters": specific_count,
            "tokens": {
                name: len(encoding.encode(text)) for name, encoding in encodings.items()
            },
        }
        results["task2"][item_id] = stats
        print(f"{item_id}: {text}")
        print(f"  chars={stats['chars']}, bytes={stats['bytes']}, "
              f"bytes/char={stats['bytes_per_char']:.3f}, "
              f"казахских специальных букв={specific_count}")
        print("  " + ", ".join(f"{name}={count}" for name, count in stats["tokens"].items()))
    print("Байты не заменяют токены. Фразы имеют разный смысл, поэтому результат")
    print("показывает пример работы токенизаторов, а не отдельную цену каждой буквы.")

    print("\nTASK 3 — жалоба: prose → JSON")
    print("Для prose/JSON прогноз до измерений не найден. Здесь показан результат.")
    print("Токенизатор       Язык  Prose  JSON  Разница")
    for name, encoding in encodings.items():
        prose = token_counts(CORPUS["complaint"], encoding)
        structured = token_counts(CORPUS["complaint_json"], encoding)
        results["task3"][name] = {}
        for lang in LANGUAGES:
            # Проверяем, что JSON не потерял ни одного слова исходной жалобы.
            restored = " ".join(json.loads(CORPUS["complaint_json"][lang]).values())
            if restored != CORPUS["complaint"][lang]:
                raise ValueError(f"JSON изменил содержание жалобы: {lang}")
            delta = structured[lang] - prose[lang]
            results["task3"][name][lang] = {
                "prose_tokens": prose[lang], "json_tokens": structured[lang],
                "delta_tokens": delta,
            }
            print(f"{name:<17} {lang:>4} {prose[lang]:>6} {structured[lang]:>5} {delta:>+8}")
        deltas = [row["delta_tokens"] for row in results["task3"][name].values()]
        if all(delta > 0 for delta in deltas):
            print("  В этой записи JSON требует больше токенов во всех трёх языках.")
        else:
            print("  Не во всех языках есть увеличение. Знак разницы оставлен как измерен.")
    print("Сравниваем абсолютные токены. Результат зависит от полей и записи JSON.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nСохранено: {args.output}")


if __name__ == "__main__":
    main()

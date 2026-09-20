"""годовая стоимость gemini. цены в USD за миллион токенов, выход включает thinking."""

import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlparse

from part2_gemini import OUTPUT_PATH, SCHEMA_VERSION, billed_tokens
from texts import LANGUAGES


def validate_measurements(data):
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("нужен новый файл measurements.gemini.json из part2_gemini.py.")
    if data.get("provider") != "gemini" or data.get("kind") != "actual_api":
        raise ValueError("нужен реальный запуск gemini с --call, а не только подсчёт токенов.")
    if not isinstance(data.get("model_id"), str) or not data["model_id"].strip():
        raise ValueError("не записана модель измерения.")
    try:
        datetime.fromisoformat(data["started_at_utc"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("не записана дата измерения.") from None
    settings = data.get("request_settings", {})
    if settings.get("tools") is not False or settings.get("cached_content") is not None:
        raise ValueError("эта формула не учитывает кэш и инструменты.")
    if settings.get("candidate_count") != 1:
        raise ValueError("нужен один ответ на каждый запрос.")
    responses = data.get("responses", {})
    result = {}
    for lang in LANGUAGES:
        row = responses.get(lang, {})
        if row.get("status") != "complete" or row.get("finish_reason") != "STOP" or row.get("truncated") is not False:
            raise ValueError(f"{lang.upper()}: нужен полный, завершённый ответ.")
        if not isinstance(row.get("answer"), str) or not row["answer"].strip():
            raise ValueError(f"{lang.upper()}: нет текста ответа.")
        counts = billed_tokens(row.get("usage_metadata"))
        if any(row.get(field) != value for field, value in counts.items()):
            raise ValueError(f"{lang.upper()}: итоговые счётчики не совпадают с usage_metadata.")
        result[lang] = counts
    return result


def request_cost(counts, input_price, output_price):
    return (counts["input_tokens"] * input_price + counts["output_tokens"] * output_price) / 1_000_000


def ratio(numerator, denominator):
    return f"{numerator / denominator:.3f}×" if denominator else "не определено (деление на 0)"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--input-price", type=float, required=True)
    parser.add_argument("--output-price", type=float, required=True)
    parser.add_argument("--price-source", required=True, help="URL официального тарифа для этой модели")
    parser.add_argument("--price-date", required=True, help="дата проверки цены: YYYY-MM-DD")
    parser.add_argument("--requests-per-day", type=int, default=2000)
    args = parser.parse_args(argv)
    if any(not math.isfinite(price) or price < 0 for price in (args.input_price, args.output_price)):
        parser.error("цены должны быть конечными неотрицательными числами.")
    if args.requests_per_day <= 0:
        parser.error("--requests-per-day должен быть положительным.")
    source = urlparse(args.price_source)
    if source.scheme != "https" or not source.netloc:
        parser.error("--price-source должен быть HTTPS-ссылкой на тариф.")
    try:
        date.fromisoformat(args.price_date)
    except ValueError:
        parser.error("--price-date: ожидается дата YYYY-MM-DD.")
    try:
        data = json.loads(args.measurements.read_text(encoding="utf-8"))
        counts = validate_measurements(data)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError):
            print(f"расчёт невозможен: {exc}", file=sys.stderr)
        else:
            print("не удалось прочитать корректный файл измерений.", file=sys.stderr)
        return 1

    costs = {lang: request_cost(counts[lang], args.input_price, args.output_price) for lang in LANGUAGES}
    print(f"модель: {data['model_id']}; измерение: {data['started_at_utc']}")
    print(f"цена: вход ${args.input_price:g}, выход ${args.output_price:g} за 1 млн токенов.")
    print(f"источник: {args.price_source}; проверено {args.price_date}")
    print(f"объём: {args.requests_per_day:,} запросов/день × 365 дней.")
    print("язык  вход  выход+thinking   USD/запрос   USD/год")
    for lang in LANGUAGES:
        row = counts[lang]
        annual = costs[lang] * args.requests_per_day * 365
        print(f"{lang.upper():<5} {row['input_tokens']:>5} {row['output_tokens']:>14} {costs[lang]:>12.6f} {annual:>10.2f}")
    print("каждая строка — отдельный сценарий одного и того же объёма; строки не суммируются.")
    for lang, base in (("ru", "en"), ("kk", "en"), ("kk", "ru")):
        print(f"{lang.upper()}/{base.upper()}: входные токены = {ratio(counts[lang]['input_tokens'], counts[base]['input_tokens'])}; "
              f"полная стоимость = {ratio(costs[lang], costs[base])}")
    print("это оценка по одному ответу на язык, без налогов, бесплатных квот и скидок.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

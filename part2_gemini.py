"""измерения gemini. без --call считаются только входные токены."""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

from texts import CORPUS, LANGUAGES


OUTPUT_PATH = Path(__file__).with_name("measurements.gemini.json")
SCHEMA_VERSION = 1


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def token_number(value):
    return type(value) is int and value >= 0


def billed_tokens(usage):
    """токены из usage, включая thinking."""
    if not isinstance(usage, dict):
        raise ValueError("Нет usage_metadata.")
    for field in ("cached_content_token_count", "tool_use_prompt_token_count"):
        if usage.get(field) not in (None, 0):
            raise ValueError("Для кэша и инструментов нужна отдельная формула цены.")
    prompt = usage.get("prompt_token_count")
    candidates = usage.get("candidates_token_count")
    total = usage.get("total_token_count")
    if not all(token_number(n) for n in (prompt, candidates, total)) or prompt == 0:
        raise ValueError("В usage_metadata не хватает счётчиков токенов.")
    thoughts = usage.get("thoughts_token_count")
    # проверяю пропущенное поле thinking по общему счётчику.
    if thoughts is None and total == prompt + candidates:
        thoughts = 0
    if not token_number(thoughts) or total != prompt + candidates + thoughts:
        raise ValueError("Счётчики usage_metadata не согласуются.")
    return {"input_tokens": prompt, "output_tokens": candidates + thoughts,
            "candidate_tokens": candidates, "thought_tokens": thoughts}


def request_parts(lang, max_output_tokens):
    contents = [types.Content(role="user", parts=[types.Part(text=CORPUS["complaint"][lang])])]
    config = types.GenerateContentConfig(
        system_instruction=CORPUS["system_prompt"][lang],
        max_output_tokens=max_output_tokens,
        temperature=1.0,
        candidate_count=1,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    return contents, config


def count_request(client, model, lang, max_output_tokens):
    contents, config = request_parts(lang, max_output_tokens)
    # system_instruction при подсчёте в Developer API требует extra_body.
    request = {
        "model": model if model.startswith("models/") else f"models/{model}",
        "contents": [content.model_dump(mode="json", by_alias=True, exclude_none=True) for content in contents],
        "systemInstruction": {"parts": [{"text": config.system_instruction}]},
        "generationConfig": {"maxOutputTokens": max_output_tokens,
                             "temperature": config.temperature, "candidateCount": 1},
    }
    result = client.models.count_tokens(
        model=model,
        contents=None,  # весь запрос передаётся ниже.
        config=types.CountTokensConfig(http_options=types.HttpOptions(
            extra_body={"generateContentRequest": request}
        )),
    )
    if not token_number(result.total_tokens):
        raise ValueError("API не вернул число входных токенов.")
    return result.total_tokens


def response_record(response):
    candidates = response.candidates or []
    candidate = candidates[0] if len(candidates) == 1 else None
    finish = candidate.finish_reason.value if candidate and candidate.finish_reason else None
    parts = candidate.content.parts or [] if candidate and candidate.content else []
    answer = "".join(part.text for part in parts if part.text and not part.thought)
    usage = response.usage_metadata.model_dump(mode="json", exclude_none=True) if response.usage_metadata else None
    record = {
        "measured_at_utc": timestamp(), "status": "complete", "finish_reason": finish,
        "truncated": finish == "MAX_TOKENS", "answer": answer,
        "response_id": response.response_id, "model_version": response.model_version,
        "usage_metadata": usage,
    }
    try:
        record.update(billed_tokens(usage))
    except ValueError as exc:
        record["status"] = "invalid_usage"
        record["usage_error"] = str(exc)
    if len(candidates) != 1:
        record["status"] = "no_single_candidate"
    elif finish == "MAX_TOKENS":
        record["status"] = "truncated"
    elif finish != "STOP":
        record["status"] = "not_completed"
    elif not answer.strip():
        record["status"] = "empty_answer"
    if any(part.function_call or part.inline_data or part.executable_code for part in parts):
        record["status"] = "non_text_response"
    return record


def collect(client, model, make_calls, max_output_tokens, save):
    payload = {
        "schema_version": SCHEMA_VERSION, "provider": "gemini",
        "kind": "actual_api" if make_calls else "count_only",
        "started_at_utc": timestamp(), "model_id": model,
        "sdk_version": version("google-genai"),
        "request_settings": {"max_output_tokens": max_output_tokens,
                             "temperature": 1.0, "candidate_count": 1,
                             "thinking": "model_default", "tools": False,
                             "cached_content": None},
        "request_texts": {lang: {"system_instruction": CORPUS["system_prompt"][lang],
                                 "user": CORPUS["complaint"][lang]} for lang in LANGUAGES},
        "token_counts": {}, "request_tokens": {}, "responses": {},
    }
    save(payload)
    for item, versions in CORPUS.items():
        payload["token_counts"][item] = {}
        for lang in LANGUAGES:
            result = client.models.count_tokens(model=model, contents=versions[lang])
            if not token_number(result.total_tokens):
                raise ValueError("API не вернул число токенов.")
            payload["token_counts"][item][lang] = result.total_tokens
        save(payload)
    for lang in LANGUAGES:
        payload["request_tokens"][lang] = count_request(client, model, lang, max_output_tokens)
        save(payload)
    if make_calls:
        for lang in LANGUAGES:
            contents, config = request_parts(lang, max_output_tokens)
            try:
                response = client.models.generate_content(model=model, contents=contents, config=config)
                payload["responses"][lang] = response_record(response)
            except Exception as exc:
                # текст ошибки может содержать ключ, поэтому его не сохраняю.
                payload["responses"][lang] = {"status": "api_error", "error_type": type(exc).__name__}
                save(payload)
                raise
            save(payload)
            print(f"{lang.upper()}: {payload['responses'][lang]['status']}")
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Точный ID доступной вам Gemini-модели")
    parser.add_argument("--call", action="store_true", help="Сделать 3 реальных запроса генерации")
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.max_output_tokens <= 0:
        parser.error("--max-output-tokens должен быть положительным")
    if args.output.exists() and not args.overwrite:
        parser.error("Файл уже существует. Укажите другой --output или --overwrite.")
    load_dotenv(Path(__file__).with_name(".env"), override=False)
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("Добавьте GEMINI_API_KEY в .env или в окружение.", file=sys.stderr)
        return 1

    def save(payload):
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        with genai.Client(api_key=key, vertexai=False, http_options=types.HttpOptions(
            timeout=120_000, retry_options=types.HttpRetryOptions(attempts=1)
        )) as client:
            payload = collect(client, args.model, args.call, args.max_output_tokens, save)
    except Exception as exc:
        print(f"Измерение остановлено ({type(exc).__name__}). Проверьте модель, ключ и доступ к API.", file=sys.stderr)
        print("Автоматический повтор не выполняется; уже полученные результаты сохранены, если запись была возможна.", file=sys.stderr)
        return 1
    print(f"Сохранено: {args.output}")
    if not args.call:
        print("Ответы не генерировались. Для Part 3 нужны реальные usage-данные: запуск с --call.")
    elif any(row["status"] != "complete" for row in payload["responses"].values()):
        print("Есть незавершённые ответы. Для сравнения цены нужны три полных ответа.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

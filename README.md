# lab 01 — ayana azat

the main report is in `submission.md` and `submission.pdf`.
the extension tasks are in `extensions.md`.
a separate explanation of the original issues is included in the personal notes supplied with this project.

## setup and commands

python 3.10 or later is required. run these commands from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python part0_tokenizers.py
python part1_offline.py
python core_tasks.py
python part3_cost.py --requests-per-day 2000
```

`part0` counts tokens, while `part1` counts characters and bytes. `core_tasks` collects the three required extension tasks. tiktoken downloads its vocabularies on the first run. `part3_cost` uses the instructor's measurements from `measurements.example.json`; the original texts and course prices are preserved.

## gemini

the key is stored in `.env` next to the script. replace `your_key_here` in the example with your key:

```dotenv
GEMINI_API_KEY=your_key_here
```

the archive does not contain an api key. before making api calls from this folder, create a local `.env` file with your key. do not upload it to github.

to make a new run and save it in a separate file:

```bash
python part2_gemini.py --model gemini-3.6-flash --call --max-output-tokens 4096 --output measurements.new.json
python part3_gemini.py --measurements measurements.new.json --input-price 0.75 --output-price 3.75 --price-source https://ai.google.dev/gemini-api/docs/pricing --price-date 2026-09-20 --requests-per-day 2000
```

without `--call`, no answers are generated. the three generation calls may use quota or incur charges, depending on the project. the listed prices are the standard paid tier prices for gemini 3.6 flash through 31 december 2026. the annual estimate assumes that these prices stay the same; it is not a free tier bill.

## the basic formula

```text
request cost = (input tokens × input price + output tokens × output price) / 1 000 000
annual cost = request cost × requests per day × 365
```

for gemini pricing, output tokens include visible tokens and thinking tokens. the input count comes from the response usage. the complaint-only count is used separately to compare languages.

## files

- `texts.py` — the original texts, greeting, and extensions;
- `part2_gemini.py` — sends requests and saves usage;
- `part3_gemini.py` — calculates costs from actual usage;
- `results/` — local calculations and verification logs;
- `ASSIGNMENT.md` — the original course requirements;
- `AI_USE.md` — a record of the assistance used to prepare this work.

to check the code:

```bash
python -m unittest discover -s tests -v
```

to run the additional caching scenario:

```bash
python part3_cost.py --cache-scenario
```

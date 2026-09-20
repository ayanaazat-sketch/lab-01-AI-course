# lab 01 — the price of one request

ayana azat · 20 september 2026

## 1. prediction and measurement

my estimates were kk/en ≈ 3.0 and kk/ru ≈ 1.5, which imply ru/en ≈ 2.0. gemini counted 60 tokens for the english complaint, 79 for russian, and 149 for kazakh. the measured ratios were ru/en = 1.32, kk/en = 2.48, and kk/ru = 1.89. kazakh used more tokens than english, but the difference was smaller than my estimate. these counts cover the complaint alone, without the system instruction.

## 2. annual cost

my assumed volume is 2,000 requests per day: 200 requests per hour over a ten-hour support day. this is an example workload, not a figure reported by a real bank.

this experiment used gemini-3.6-flash. the input includes the system instruction. the output includes both the visible response and thinking tokens. all three responses finished with `finish_reason=STOP`.

| language | input | response + thinking | cost per request | annual cost |
|---|---:|---:|---:|---:|
| en | 101 | 63 + 398 = 461 | $0.00180450 | $1,317.29 |
| ru | 131 | 120 + 568 = 688 | $0.00267825 | $1,955.12 |
| kk | 237 | 201 + 665 = 866 | $0.00342525 | $2,500.43 |

annual cost = `(input tokens × 0.75 + output tokens × 3.75) / 1,000,000 × 2,000 × 365`.

the standard paid-tier rates are $0.75 per million input tokens and $3.75 per million output tokens. the table assumes these rates remain constant; it does not show an actual payment. each language is a separate scenario at the same volume. kk/en is 2.35 for input tokens and 1.90 for the total cost, because response length also affects the bill.

for the four course models, the table below applies the prices in `prices.py` to the instructor's reference measurements in `measurements.example.json`:

| model | en, $/year | ru, $/year | kk, $/year |
|---|---:|---:|---:|
| haiku-4.5 | 3,591.60 | 4,627.47 | 5,111.46 |
| sonnet-5 | 7,183.20 | 9,254.94 | 10,222.92 |
| opus-5 | 17,958.00 | 23,137.35 | 25,557.30 |
| fable-5.1 | 35,916.00 | 46,274.70 | 51,114.60 |

these are four prices applied to one set of token counts, rather than four separate model runs. this table and the gemini results cannot directly rank the models, since they use different response lengths.

## 3. model choice

my choice for a kazakh-language support pilot would be gemini-3.6-flash. in this experiment, it requested the missing documents, avoided inventing a reason for the rate change, and suggested a next step. the estimated kazakh-language cost is about $2,500 per year. one response per language is not enough to justify a full rollout: a larger set of support cases and human review would be needed. haiku and opus were not tested for response quality.

## 4. reducing the cost

one option is to request answers of no more than two sentences, then measure the full output again, including thinking tokens: a shorter visible answer does not necessarily mean a lower bill.

sources: `measurements.gemini.json`, the instructor's `measurements.example.json`, and [google's pricing page](https://ai.google.dev/gemini-api/docs/pricing), checked on 20 september 2026. the gemini rates above apply through 31 december 2026; the annual estimate assumes a fixed price.

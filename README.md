# Lebanese-Franco-Factory

Config-driven **factory** that generates, validates, cleans, and exports Lebanese Franco (Arabizi) datasets.

Part of [Lebanese Language Lab](https://github.com/JulianoSaad/Lebanese-Language-Lab).  
Dataset releases: [Lebanese-Franco-Datasets](https://github.com/JulianoSaad/Lebanese-Franco-Datasets).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest -q

python scripts/generate.py --dataset arabic_to_franco --size 100 --seed 42
python scripts/generate.py --dataset chat_sft --language lebanese_franco --size 100
python scripts/generate.py --dataset typos --size 50
python scripts/generate.py --dataset explain --size 50
```

Export a run into the Datasets repo layout:

```bash
python scripts/export.py --run output/conversion/arabic_to_franco/<stamp> --version v0.1
```

## Families

| Family | Examples |
|---|---|
| `chat_sft` | casual chat |
| `conversion` | arabic_to_franco, franco_to_arabic, english_to_franco, franco_to_english |
| `spelling` | typos, variants, abbreviations |
| `instruction` | explain, summarize, rewrite |

## Training / eval

```bash
python scripts/train.py --smoke
python scripts/evaluate.py
```

## Dashboard / Review (optional)

```bash
pip install -e ".[dashboard]"
python scripts/dashboard.py   # http://127.0.0.1:8080
python scripts/review.py      # http://127.0.0.1:8081
```

## License

Apache-2.0

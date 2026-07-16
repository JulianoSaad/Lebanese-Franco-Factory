# Lebanese-Franco-Factory

Config-driven **factory** that generates, validates, cleans, and exports Lebanese Franco (Arabizi) datasets.

Part of [Lebanese Language Lab](https://github.com/JulianoSaad/Lebanese-Language-Lab).  
Dataset releases: [Lebanese-Franco-Datasets](https://github.com/JulianoSaad/Lebanese-Franco-Datasets).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Golden tests (CI gate)
pytest -q

# Generate a small conversion set
python scripts/generate.py --dataset arabic_to_franco --size 100 --seed 42
```

## Build order

```
Dictionary → Templates → Generator → Validator → Exporter → Dataset
```

Dashboard / Human Review / Benchmarks come **later** (see Lab roadmap).

## License

Apache-2.0

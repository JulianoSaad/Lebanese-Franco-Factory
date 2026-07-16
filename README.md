# Lebanese-Franco-Factory

Config-driven **factory** that generates, validates, cleans, and exports Lebanese Franco (Arabizi) datasets.

Part of [Lebanese Language Lab](https://github.com/JulianoSaad/Lebanese-Language-Lab).  
Dataset releases: [Lebanese-Franco-Datasets](https://github.com/JulianoSaad/Lebanese-Franco-Datasets).

## Layout

```text
src/lebanese_franco_factory/   # package (CLI, factory, providers, training, …)
plugins/                       # independent dataset plugins
dictionary/                    # modular packs (food, sports, …)
configs/                       # YAML dataset + training configs
tests/                         # unit · integration · plugins · performance · golden
docs/api/                      # auto-generated API docs (pdoc)
scripts/                       # thin wrappers only — prefer `lff`
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest -q

# Preferred package CLI
lff generate --dataset arabic_to_franco --size 100 --seed 42
lff generate --dataset chat_sft --language lebanese_franco --size 100
lff generate --dataset augmentation --size 50

# API docs (from day 1 — regenerate anytime)
lff docs
lff apply-feedback   # merge human reviews into lexicon
lff review           # http://127.0.0.1:8081

```

`scripts/*.py` remain as thin wrappers for convenience.

## Providers

```python
from lebanese_franco_factory.providers import get_provider
p = get_provider("ollama", model="qwen2.5")
```

All of OpenAI / Ollama / LiteLLM / vLLM / Hugging Face share the same `Provider` ABC. See [`docs/providers.md`](docs/providers.md).

## Families / plugins

| Plugin | Datasets |
|---|---|
| `chat` | chat_sft, casual_chat |
| `conversion` | arabic↔franco, english↔franco |
| `spelling` | typos, variants, abbreviations |
| `instruction` | explain, summarize, rewrite |
| `augmentation` | digit_noise / augmentation |

## Training / eval / UI

```bash
lff train --smoke
lff evaluate
pip install -e ".[dashboard]"
lff dashboard   # :8080
lff review      # :8081
```

## License

Apache-2.0

# Providers

All backends implement the same ABC:

```text
Provider
├── OpenAIProvider
├── OllamaProvider
├── LiteLLMProvider
├── VLLMProvider
└── HuggingFaceProvider
```

```python
from lebanese_franco_factory.providers import get_provider

p = get_provider("ollama", model="qwen2.5")
text = p.chat([{"role": "user", "content": "kifak?"}])
```

Rule-based generation does **not** require a provider. Providers are for model-assisted expansion and evaluation.

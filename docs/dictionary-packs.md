# Dictionary packs

Packs live in `dictionary/*.json` (not one monolithic file).

Plugins/configs declare which packs to load:

```yaml
dictionary_packs: [sports, emotions, greetings]
```

```python
from lebanese_franco_factory.dictionary.loader import load_packs
packs = load_packs(["sports", "greetings"])
```

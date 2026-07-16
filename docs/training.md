# Training

Prepare + optional LoRA train on Qwen (or any HF causal LM):

```bash
# Prepare tiny mix (no GPU / no heavy deps)
python scripts/train.py --smoke

# Full train (requires train extras + GPU recommended)
pip install -e ".[train]"
python scripts/train.py --config configs/training/qwen_lora_default.yaml
```

Evaluate frozen benchmarks:

```bash
python scripts/evaluate.py
```

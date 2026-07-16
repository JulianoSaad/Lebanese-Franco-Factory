# Tiny CPU LoRA run (v0.2)

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Device: CPU (no GPU on this host)
- Samples: 48 SFT rows from v0.2 chat + conversion mix
- Runtime: ~10 minutes
- Adapter: `output/training/qwen_lora_v0.2/adapter/`
- Train loss dropped from ~14.3 → ~0.74 across the epoch

This proves the pipeline end-to-end. For a useful Lebanese Franco model, retrain on GPU with far more reviewed data.

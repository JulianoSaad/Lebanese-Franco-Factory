# Gold export v0.2 (recommended path)

Built from `feedback/human_feedback.jsonl` after AI first-pass review.

## Tiers

| Tier | Meaning | Count (approx) |
|---|---|---|
| **Gold** | Curated seed + edits + high-trust accepts | ~29 conversion + 11 chat |
| **Silver** | AI first-pass accepts (medium confidence) | ~91 conversion |
| **needs_human** | Slang/naturalness items for native check | 30 |

## Where it lives

- Factory: `output/gold/reviewed_v0.2/<stamp>/`
- Datasets: `Lebanese-Franco-Datasets/v0.2-gold/` (full + samples)
- Native queue: `data/review/needs_human_v0.2.jsonl`

## How to use for training

Prefer **gold** for evaluation/few-shot quality checks.  
Use **gold + silver** as a clean supervised starter set.  
Do **not** treat raw 100k synthetic dumps as equal quality.

```bash
lff review          # opens needs_human queue first
lff apply-feedback  # after you click through
```

Then regenerate gold export (re-run the gold builder) before the next LoRA train.

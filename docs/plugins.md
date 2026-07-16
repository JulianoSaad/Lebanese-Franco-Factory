# Plugins

1. Copy `plugins/_template` → `plugins/medical`
2. Implement `PLUGIN` + `generate` + `register`
3. Add configs under `configs/datasets/...`
4. Add tests under `tests/plugins/`

Core code should not import domain plugins directly.

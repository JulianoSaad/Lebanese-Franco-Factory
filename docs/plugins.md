# Plugins

Each plugin is independent under `plugins/<name>/`:

```text
plugins/
  chat/
  conversion/
  instruction/
  spelling/
  augmentation/
  _template/          # copy-me for medical / legal / finance
```

## Add a plugin

1. Copy `plugins/_template` → `plugins/medical`
2. Implement `PLUGIN` + `generate` + `register`
3. Add configs under `configs/datasets/...`
4. Add tests under `tests/plugins/`

Core code must not import domain plugins directly — discovery is via `plugin_loader`.

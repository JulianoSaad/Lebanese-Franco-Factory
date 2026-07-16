"""Discover and register plugins from the plugins/ directory."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from lebanese_franco_factory.core.paths import plugins_dir


@dataclass
class PluginRegistry:
    generators: dict[str, Callable[..., Any]] = field(default_factory=dict)
    plugins: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_generator(self, name: str, fn: Callable[..., Any]) -> None:
        self.generators[name] = fn

    def add_plugin_meta(self, name: str, meta: dict[str, Any]) -> None:
        self.plugins[name] = meta


def _load_module(path: Path):
    module_name = f"lff_plugin_{path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_plugins(base: Path | None = None) -> PluginRegistry:
    root = base or plugins_dir()
    registry = PluginRegistry()
    for plugin_py in sorted(root.glob("*/plugin.py")):
        if plugin_py.parent.name.startswith("_"):
            continue
        module = _load_module(plugin_py)
        meta = getattr(module, "PLUGIN", {"name": plugin_py.parent.name})
        registry.add_plugin_meta(meta.get("name", plugin_py.parent.name), meta)
        register = getattr(module, "register", None)
        if callable(register):
            register(registry)
    return registry

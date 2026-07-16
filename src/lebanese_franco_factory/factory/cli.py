"""Back-compat shim — prefer `lebanese_franco_factory.cli.main` / `lff`."""

from __future__ import annotations

from lebanese_franco_factory.cli.main import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())

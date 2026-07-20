"""Allow ``python -m dre`` to work (delegates to cli.main)."""

from dre.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

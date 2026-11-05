"""Allow ``python -m gif2grid`` to behave like the ``gif2grid`` command."""

from gif2grid.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

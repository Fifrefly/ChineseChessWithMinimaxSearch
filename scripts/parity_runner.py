"""Parity-check entry point for comparing Python rules with xiangqi.js."""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Run parity checks.

    The Node.js bridge and comparison logic will be implemented after the
    Python rules layer has legal move generation.
    """
    _ = argv
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


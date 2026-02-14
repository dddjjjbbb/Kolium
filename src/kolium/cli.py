"""Command-line interface for Kolium."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from kolium.generator import generate_document
from kolium.parser import read_md_file, remove_nbsp

DATE_PREFIX_RE = re.compile(r"^\d{4}(-\d{2}){5}-")


def derive_output_name(input_path: Path) -> Path:
    """Strip the KOReader date-time prefix and prepend 'Highlights_'."""
    stem = input_path.stem
    stripped = DATE_PREFIX_RE.sub("", stem)
    return input_path.parent / f"Highlights_{stripped}{input_path.suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kolium",
        description="Process KOReader highlight exports into sorted Markdown.",
    )
    parser.add_argument("input", type=Path, help="Path to the KOReader Markdown export")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: derives from input, e.g. Highlights_Title.md)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = read_md_file(args.input)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    text = remove_nbsp(text)
    output = generate_document(text)

    output_path = args.output or derive_output_name(args.input)
    output_path.write_text(output, encoding="utf-8")
    print(f"Processed highlights written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

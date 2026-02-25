"""Command-line interface for Kolium."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from kolium.finder import (
    DATE_PREFIX_RE,
    KOBO_CLIPBOARD_DIR,
    KOBO_LIBRARY_DIR,
    BookMatch,
    find_epubs,
    find_highlights,
    list_all_books,
)
from kolium.generator import generate_document
from kolium.parser import read_md_file, remove_nbsp


def _format_book(book: BookMatch) -> str:
    """Format a book for display: Title by Author."""
    if book.author:
        return f"{book.title} by {book.author}"
    return book.title


def derive_output_name(input_path: Path) -> Path:
    """Strip the KOReader date-time prefix and prepend 'Highlights_'."""
    stem = input_path.stem
    stripped = DATE_PREFIX_RE.sub("", stem)
    return input_path.parent / f"Highlights_{stripped}{input_path.suffix}"


def derive_search_output_name(title: str) -> Path:
    """Build a dated output filename from a book title."""
    clean_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "-")
    today = date.today().isoformat()
    return Path(f"{today}-{clean_title}-Highlights.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kolium",
        description="Process KOReader highlight exports into sorted Markdown.",
    )
    parser.add_argument(
        "input",
        nargs="*",
        help="Path to a KOReader Markdown export, or a search query to find one on your Kobo",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all highlight files on your Kobo",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: derives from input)",
    )
    parser.add_argument(
        "--clipboard-dir",
        type=Path,
        default=KOBO_CLIPBOARD_DIR,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--library-dir",
        type=Path,
        default=KOBO_LIBRARY_DIR,
        help=argparse.SUPPRESS,
    )
    return parser


def _print_book_list(books: list[BookMatch]) -> None:
    """Print a formatted list of available books."""
    if not books:
        print("No highlight files found on Kobo.")
        return
    print(f"\nAvailable books ({len(books)}):\n")
    for book in books:
        print(f"  {_format_book(book)}")
    print()


def _select_book_interactive(
    books: list[BookMatch],
    title: str = "Multiple highlights found:",
) -> BookMatch | None:
    """Use an arrow-key terminal menu for selection."""
    from simple_term_menu import TerminalMenu

    items = [_format_book(m) for m in books]
    menu = TerminalMenu(items, title=title)
    index = menu.show()
    if index is None:
        return None
    return books[index]


def _select_book_plain(
    books: list[BookMatch],
    title: str = "Multiple highlights found:",
) -> BookMatch | None:
    """Numbered list fallback for non-interactive terminals."""
    print(f"{title}\n")
    for i, book in enumerate(books, 1):
        print(f"  {i}. {_format_book(book)}")
    print()

    try:
        choice = input("Select a number (or q to quit): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None

    if choice.lower() == "q":
        return None

    try:
        index = int(choice) - 1
        if 0 <= index < len(books):
            return books[index]
    except ValueError:
        pass

    print("Invalid selection.", file=sys.stderr)
    return None


def _select_book(
    books: list[BookMatch],
    title: str = "Multiple highlights found:",
) -> BookMatch | None:
    """Select from books, using interactive menu when available."""
    if sys.stdin.isatty():
        return _select_book_interactive(books, title)
    return _select_book_plain(books, title)


def _process_file(input_path: Path, output_path: Path | None) -> int:
    """Read, process, and write highlights from a file."""
    try:
        text = read_md_file(input_path)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    text = remove_nbsp(text)
    output = generate_document(text)

    resolved_output = output_path or derive_output_name(input_path)
    resolved_output.write_text(output, encoding="utf-8")
    print(f"Processed highlights written to {resolved_output}")
    return 0


def _check_kobo_mounted(clipboard_dir: Path) -> bool:
    """Check if the Kobo clipboard directory exists and print an error if not."""
    if clipboard_dir.is_dir():
        return True
    print(
        f"Kobo clipboard directory not found: {clipboard_dir}\n"
        "Is your Kobo e-reader connected and mounted?",
        file=sys.stderr,
    )
    return False


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    clipboard_dir = args.clipboard_dir

    if args.list:
        if not _check_kobo_mounted(clipboard_dir):
            return 1
        _print_book_list(list_all_books(clipboard_dir))
        return 0

    if not args.input:
        if not _check_kobo_mounted(clipboard_dir):
            return 1
        all_books = list_all_books(clipboard_dir)
        if not all_books:
            print("No highlight files found on Kobo.", file=sys.stderr)
            return 1
        selected = _select_book(
            all_books,
            title=f"Select a book ({len(all_books)} available):",
        )
        if selected is None:
            return 1
        output_path = args.output or derive_search_output_name(selected.title)
        return _process_file(selected.path, output_path)

    raw_input = " ".join(args.input)
    input_path = Path(raw_input)

    if input_path.is_file():
        return _process_file(input_path, args.output)

    query = raw_input

    if not _check_kobo_mounted(clipboard_dir):
        return 1

    print(f'Searching Kobo highlights for "{query}"...', file=sys.stderr)
    matches = find_highlights(query, clipboard_dir)

    if not matches:
        print(f'No highlights found matching "{query}".\n', file=sys.stderr)

        epub_matches = find_epubs(query, args.library_dir)
        if epub_matches:
            print("Found on your Kobo but no exported highlights:\n", file=sys.stderr)
            for epub in epub_matches:
                print(f"  {epub}", file=sys.stderr)
            print(
                "\nTo export highlights from KOReader:\n"
                "  1. Open the book on your Kobo\n"
                '  2. Tap the tools menu (spanner icon)\n'
                '  3. Select "Export highlights"\n'
                '  4. Select "Export all notes in current book"\n',
                file=sys.stderr,
            )
        else:
            all_books = list_all_books(clipboard_dir)
            if all_books:
                _print_book_list(all_books)
        return 1

    if len(matches) == 1:
        selected = matches[0]
    else:
        selected = _select_book(matches)
        if selected is None:
            return 1

    output_path = args.output or derive_search_output_name(selected.title)
    return _process_file(selected.path, output_path)


if __name__ == "__main__":
    raise SystemExit(main())

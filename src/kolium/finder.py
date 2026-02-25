"""Discover KOReader highlight files on a mounted Kobo by fuzzy search."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KOBO_CLIPBOARD_DIR = Path("/Volumes/KOBOeReader/.adds/koreader/clipboard")
KOBO_LIBRARY_DIR = Path("/Volumes/KOBOeReader/Calibre")

DATE_PREFIX_RE = re.compile(r"^\d{4}(-\d{2}){5}-")


@dataclass(frozen=True)
class BookMatch:
    path: Path
    title: str
    author: str


def list_all_books(clipboard_dir: Path = KOBO_CLIPBOARD_DIR) -> list[BookMatch]:
    """Return all highlight files from the clipboard directory."""
    if not clipboard_dir.is_dir():
        return []

    books: list[BookMatch] = []
    for md_file in clipboard_dir.glob("*.md"):
        title, author = _parse_header(md_file)
        if title:
            books.append(BookMatch(path=md_file, title=title, author=author))
    return sorted(books, key=lambda b: b.title.lower())


def find_highlights(query: str, clipboard_dir: Path = KOBO_CLIPBOARD_DIR) -> list[BookMatch]:
    """Search clipboard directory for highlight files matching a fuzzy query.

    Matches case-insensitively against the filename stem (date prefix stripped),
    the title line (# Title), and the author line (##### Author).
    """
    if not clipboard_dir.is_dir():
        return []

    query_lower = query.lower()
    matches: list[BookMatch] = []

    for md_file in clipboard_dir.glob("*.md"):
        title, author = _parse_header(md_file)
        stem = DATE_PREFIX_RE.sub("", md_file.stem)

        searchable = f"{stem} {title} {author}".lower()
        if query_lower in searchable:
            matches.append(BookMatch(path=md_file, title=title, author=author))

    return sorted(matches, key=lambda b: b.title.lower())


def find_epubs(query: str, library_dir: Path = KOBO_LIBRARY_DIR) -> list[str]:
    """Search the Kobo library for epubs matching a query by filename.

    Returns a list of 'Title by Author' strings for matching books.
    """
    if not library_dir.is_dir():
        return []

    query_lower = query.lower()
    matches: list[str] = []

    for epub in library_dir.glob("*.epub"):
        if query_lower in epub.stem.lower():
            parts = epub.stem.split(" - ", maxsplit=1)
            title = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else ""
            label = f"{title} by {author}" if author else title
            matches.append(label)

    return sorted(matches, key=str.lower)


def _parse_header(path: Path) -> tuple[str, str]:
    """Extract title and author from the first two lines of a highlight file."""
    title = ""
    author = ""
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("# ") and not stripped.startswith("## "):
                    title = stripped.removeprefix("# ")
                elif stripped.startswith("##### "):
                    author = stripped.removeprefix("##### ")
                    break
    except OSError:
        pass
    return title, author

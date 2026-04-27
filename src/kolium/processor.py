"""Clean and normalise individual highlight strings."""

from __future__ import annotations

import re

QUOTE_CHARS = ('"', "\u201c", "\u201d", "'", "\u2018", "\u2019")


def process_highlight(highlight: str) -> str:
    """Clean a single *-wrapped highlight through a normalisation pipeline."""
    highlight = highlight.strip()
    if not _is_wrapped(highlight):
        return highlight

    text = highlight[1:-1].strip()
    if not text:
        return ""

    text = _strip_trailing_commas(text)
    text = _normalise_quotes(text)
    text = _balance_symbols(text)
    text = _capitalise_first(text)
    text = _ensure_ending_punctuation(text)
    return text


def _is_wrapped(text: str) -> bool:
    return text.startswith("*") and text.endswith("*") and len(text) > 2


def _strip_trailing_commas(text: str) -> str:
    # Comma immediately before a closing quote: "some text," → "some text"
    text = re.sub(r",(?=[" + re.escape("".join(QUOTE_CHARS)) + r"]$)", "", text)
    return re.sub(r"[,\s]+$", "", text)


def _normalise_quotes(text: str) -> str:
    # Collapse duplicate leading quotes: ""hello" → "hello"
    while len(text) > 1 and text[0] in QUOTE_CHARS and text[1] in QUOTE_CHARS:
        text = text[1:]

    has_leading_quote = text[0] in QUOTE_CHARS if text else False
    has_trailing_quote = text[-1] in QUOTE_CHARS if text else False

    # Mirror a trailing quote at the front if missing
    if has_trailing_quote and not has_leading_quote:
        text = text[-1] + text

    return text


def _balance_symbols(text: str) -> str:
    """Close unclosed quotes and parentheses at end of text."""
    # For quotes where open == close char, check if odd count
    if text.count('"') % 2 == 1:
        text += '"'

    # For paired symbols with different open/close chars
    pairs = [("(", ")"), ("[", "]")]
    for open_char, close_char in pairs:
        open_count = text.count(open_char)
        close_count = text.count(close_char)
        if open_count > close_count:
            text += close_char * (open_count - close_count)

    return text


def _capitalise_first(text: str) -> str:
    first = 1 if text and text[0] in QUOTE_CHARS else 0
    if len(text) > first and not text[first].isupper():
        return text[:first] + text[first].upper() + text[first + 1 :]
    return text


def _ensure_ending_punctuation(text: str) -> str:
    end_marks = (".", "?", "!")
    if text.endswith(QUOTE_CHARS):
        if len(text) > 1 and text[-2] not in end_marks:
            return text[:-1] + "." + text[-1]
    elif not text.endswith(end_marks):
        return text + "."
    return text

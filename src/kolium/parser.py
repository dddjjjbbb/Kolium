"""Read and extract structured data from KOReader highlight exports."""

from __future__ import annotations

from pathlib import Path

import spacy


def read_md_file(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def remove_nbsp(text: str) -> str:
    return text.replace("\xa0", " ")


def extract_people(text: str, nlp: spacy.language.Language) -> list[str]:
    """Extract person names from highlight contents via spaCy NER.

    Filters out false positives using heuristics: entities must be
    at least two words, possessive forms are excluded, and entities
    from highlights containing exclamatory/interrogative punctuation
    are excluded (likely quotes/dialogue). Relies on spaCy NER for
    person detection.
    """
    people: set[str] = set()
    for content in _highlight_contents(text):
        if len(content.split()) < 2:
            continue

        # Skip highlights with exclamatory/interrogative punctuation (quotes/dialogue)
        if any(p in content for p in ["!", "?"]):
            continue

        doc = nlp(content)
        for ent in doc.ents:
            name = ent.text.strip()
            if (
                ent.label_ == "PERSON"
                and len(name.split()) >= 2
                and not name.endswith("'s")
                and "'s " not in name
            ):
                people.add(name)
    return sorted(people)


def extract_words(text: str, nlp: spacy.language.Language) -> list[str]:
    """Extract single-word vocabulary highlights (excluding people)."""
    people = set(extract_people(text, nlp))
    words = {
        content.title()
        for content in _single_word_highlights(text)
        if content not in people
    }
    return sorted(words)


def extract_notes(text: str) -> list[str]:
    """Extract multi-word highlights, processing each through highlight cleanup."""
    from kolium.processor import process_highlight

    return [
        note
        for line in _multi_word_highlights(text)
        if (note := process_highlight(line))
    ]


def extract_header(text: str) -> tuple[str, str]:
    """Extract title and author from markdown header lines.

    Returns (title, author). Empty strings if not found.
    """
    title = ""
    author = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped.removeprefix("# ")
        elif stripped.startswith("##### "):
            author = stripped.removeprefix("##### ")
            break
    return title, author



def _single_word_highlights(text: str) -> list[str]:
    return [
        content
        for content in _highlight_contents(text)
        if len(content.split()) == 1
    ]


def _multi_word_highlights(text: str) -> list[str]:
    return [
        line
        for line in _normalised_lines(text)
        if _is_highlight_line(line) and len(_highlight_content(line).split()) > 1
    ]


def _highlight_contents(text: str) -> list[str]:
    return [
        _highlight_content(line)
        for line in _normalised_lines(text)
        if _is_highlight_line(line)
    ]


def _normalised_lines(text: str) -> list[str]:
    """Join multi-line highlights into single lines.

    KOReader can export highlights that span multiple lines. A highlight
    opens with * on one line and closes with * on a later line. These
    need joining before line-by-line extraction can see them.
    """
    result: list[str] = []
    buffer: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        if buffer:
            buffer.append(stripped)
            if stripped.endswith("*"):
                result.append(" ".join(buffer))
                buffer = []
        elif stripped.startswith("*") and not stripped.endswith("*") and len(stripped) > 1:
            buffer.append(stripped)
        else:
            result.append(line)

    # Unclosed highlight — append lines as-is rather than losing them
    result.extend(buffer)
    return result


def _is_highlight_line(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.startswith("*")
        and not stripped.startswith("**")
        and stripped.endswith("*")
        and len(stripped) > 2
    )


def _highlight_content(line: str) -> str:
    return line.strip()[1:-1].strip()

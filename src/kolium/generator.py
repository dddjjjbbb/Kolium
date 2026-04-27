"""Assemble the final Markdown output from parsed highlights."""

from __future__ import annotations

import spacy

from kolium.dictionary import define
from kolium.parser import extract_header, extract_notes, extract_people, extract_words


def generate_document(text: str, nlp: spacy.language.Language | None = None) -> str:
    """Build a Markdown document from extracted highlights.

    Only populated categories appear. A table of contents is included
    when two or more categories have content. Words include definitions
    from WordNet when available.
    """
    if nlp is None:
        nlp = spacy.load("en_core_web_sm")

    title, author = extract_header(text)
    people = extract_people(text, nlp)
    notes = extract_notes(text)
    words = extract_words(text, nlp)

    # Remove notes that are just person names (ignoring punctuation)
    notes = _filter_person_duplicates(notes, people)

    # Split words into those with and without definitions
    words_with_defs, words_without_defs = _split_words_by_definition(words)

    categories = [
        ("People", people),
        ("Notes", notes),
        ("Words with Definitions", words_with_defs),
        ("Words", words_without_defs),
    ]
    populated = [(name, items) for name, items in categories if items]

    if not populated:
        return ""

    lines: list[str] = []

    # Add H1 header with title and author
    if title:
        if author:
            lines.append(f"# {title} - {author}")
        else:
            lines.append(f"# {title}")
        lines.append("")

    if len(populated) >= 2:
        lines.append("## Table of Contents")
        lines.extend(f"- [{name}](#{_slugify(name)})" for name, _ in populated)
        lines.append("")

    for name, items in populated:
        lines.extend([f"## {name}", ""])
        if name == "Words with Definitions":
            _append_words_with_definitions(lines, items)
        else:
            lines.extend(f"- {item}" for item in items)
        lines.append("")

    return "\n".join(lines) + "\n"


def _filter_person_duplicates(notes: list[str], people: list[str]) -> list[str]:
    """Remove notes that match person names when punctuation is stripped."""
    people_normalised = {_strip_punctuation(name) for name in people}
    return [
        note
        for note in notes
        if _strip_punctuation(note) not in people_normalised
    ]


def _strip_punctuation(text: str) -> str:
    """Remove trailing punctuation for comparison."""
    return text.rstrip(".,!?;:")


def _split_words_by_definition(words: list[str]) -> tuple[list[str], list[str]]:
    """Split words into those with and without WordNet definitions."""
    with_defs = []
    without_defs = []
    for word in words:
        if define(word.lower()):
            with_defs.append(word)
        else:
            without_defs.append(word)
    return with_defs, without_defs


def _slugify(text: str) -> str:
    """Convert text to lowercase kebab-case for markdown anchors."""
    return text.lower().replace(" ", "-")


def _append_words_with_definitions(lines: list[str], words: list[str]) -> None:
    for word in words:
        lines.append(f"- {word}")
        definition = define(word.lower())
        if definition:
            lines.append(f"    - Definition: {definition.capitalize()}")

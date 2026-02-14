"""Assemble the final Markdown output from parsed highlights."""

from __future__ import annotations

import spacy

from kolium.dictionary import define
from kolium.parser import extract_notes, extract_people, extract_words


def generate_document(text: str, nlp: spacy.language.Language | None = None) -> str:
    """Build a Markdown document from extracted highlights.

    Only populated categories appear. A table of contents is included
    when two or more categories have content. Words include definitions
    from WordNet when available.
    """
    if nlp is None:
        nlp = spacy.load("en_core_web_sm")

    categories = [
        ("People", extract_people(text, nlp)),
        ("Notes", extract_notes(text)),
        ("Words", extract_words(text, nlp)),
    ]
    populated = [(name, items) for name, items in categories if items]

    if not populated:
        return ""

    lines: list[str] = []

    if len(populated) >= 2:
        lines.append("## Table of Contents")
        lines.extend(f"- [{name}](#{name.lower()})" for name, _ in populated)
        lines.append("")

    for name, items in populated:
        lines.extend([f"## {name}", ""])
        if name == "Words":
            _append_words_with_definitions(lines, items)
        else:
            lines.extend(f"- {item}" for item in items)
        lines.append("")

    return "\n".join(lines) + "\n"


def _append_words_with_definitions(lines: list[str], words: list[str]) -> None:
    for word in words:
        lines.append(f"- {word}")
        definition = define(word.lower())
        if definition:
            lines.append(f"    - Definition: {definition.capitalize()}")

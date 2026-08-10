"""Assemble the final Markdown output from parsed highlights."""

from __future__ import annotations

import spacy

from kolium.dictionary import define
from kolium.parser import (
    extract_annotations,
    extract_header,
    extract_notes,
    extract_people,
    extract_words,
)


def generate_document(
    text: str,
    nlp: spacy.language.Language | None = None,
    extra_categories: list[tuple[str, list[str]]] | None = None,
) -> str:
    """Build a Markdown document from extracted highlights.

    Only populated categories appear. A table of contents is included
    when two or more categories have content. Words include definitions
    from WordNet when available.

    Args:
        text: Raw highlight text (KOReader markdown format).
        nlp: A loaded spaCy language model. Loads default if None.
        extra_categories: Optional list of ``(section_name, items)`` tuples
            to append as additional categories. Use for data not derived
            from the raw highlight text (e.g., Kindle user notes).
    """
    if nlp is None:
        nlp = spacy.load("en_core_web_sm")

    title, author = extract_header(text)
    people = extract_people(text, nlp)
    notes = extract_notes(text)
    annotations = extract_annotations(text)
    words = extract_words(text, nlp)

    # Remove notes that are just person names (ignoring punctuation)
    notes = _filter_person_duplicates(notes, people)

    # Remove notes containing only extracted people + connectives
    notes = _filter_people_only_notes(notes, people)

    # Split words into those with and without definitions
    words_with_defs, words_without_defs = _split_words_by_definition(words)

    categories = [
        ("People", people),
        ("Notes", notes),
        ("Words with Definitions", words_with_defs),
        ("Words", words_without_defs),
    ]
    if annotations:
        categories.append(("Annotations", annotations))
    if extra_categories:
        categories.extend(extra_categories)
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


def _filter_people_only_notes(notes: list[str], people: list[str]) -> list[str]:
    """Remove notes that contain only person names and connectives.

    If all words in a note are either person names or common connectives
    (and, or, commas), the note is redundant as all people are already
    listed separately.
    """
    connectives = {"and", "or", "&"}

    filtered = []
    for note in notes:
        # Remove all person names from note
        remaining = note
        for person in people:
            remaining = remaining.replace(person, "")

        # Remove punctuation and connectives
        words = remaining.replace(",", "").replace(".", "").split()
        words = [w for w in words if w.lower() not in connectives]

        # If substantive words remain, keep the note
        if words:
            filtered.append(note)

    return filtered


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


def generate_task_list(text: str, nlp: spacy.language.Language | None = None) -> str:
    """Generate a task-list style Markdown document from notes paired with highlights.

    Each note becomes a checklist item with its source text in a structured
    format suitable for tracking edits and corrections::

        ## Title - Author

        **N corrections to apply**

        - [ ] Correction 1
            - source: "source text"
            - note: "correction to apply"

    Args:
        text: Raw highlight text (KOReader markdown format).
        nlp: A loaded spaCy language model (unused in this mode, but kept
            for API consistency with :func:`generate_document`).

    Returns:
        A complete Markdown task list string, or empty string if no notes.
    """
    from kolium.parser import extract_header, pair_notes_with_highlights

    title, author = extract_header(text)
    pairs = pair_notes_with_highlights(text)

    if not pairs:
        return ""

    lines: list[str] = []

    if title:
        if author:
            lines.append(f"# {title} - {author}")
        else:
            lines.append(f"# {title}")
        lines.append("")

    lines.append(f"**{len(pairs)} {'corrections' if len(pairs) != 1 else 'correction'} to apply**")
    lines.append("")

    for i, (source, note) in enumerate(pairs, 1):
        lines.append(f"- [ ] Correction {i}")
        lines.append(f"    - source: \"{source}\"")
        lines.append(f"    - note: \"{note}\"")
        lines.append("")

    return "\n".join(lines) + "\n"


def _append_words_with_definitions(lines: list[str], words: list[str]) -> None:
    for word in words:
        lines.append(f"- {word}")
        definition = define(word.lower())
        if definition:
            # Ensure first char uppercase, preserve rest (e.g., "World War I")
            formatted = definition[0].upper() + definition[1:] if definition else ""
            lines.append(f"    - Definition: {formatted}")

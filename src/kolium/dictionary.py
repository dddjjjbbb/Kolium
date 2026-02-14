"""WordNet-backed dictionary for definitions and word classification."""

from __future__ import annotations

from nltk.corpus import wordnet as wn

MIN_SYNSETS = 2


def define(word: str) -> str | None:
    """Return the most concise definition for a word, or None if not found."""
    synsets = wn.synsets(word)
    if not synsets:
        return None
    matching = [s for s in synsets if s.lemmas()[0].name().lower() == word.lower()]
    candidates = matching or synsets
    return min(candidates, key=lambda s: len(s.definition())).definition()


def is_common_phrase(phrase: str) -> bool:
    """True if every word in the phrase is a common English word.

    A word is considered common if it has at least MIN_SYNSETS meanings
    in WordNet. Proper nouns and rare words typically have fewer.
    """
    return all(
        len(wn.synsets(word)) >= MIN_SYNSETS
        for word in phrase.lower().split()
    )

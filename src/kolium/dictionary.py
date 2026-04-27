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


def is_very_common_phrase(phrase: str) -> bool:
    """True if all words are highly common (8+ synsets each).

    Filters technical concepts like "Reading List" where all words
    are very common. Person names usually have at least one less
    common word.
    """
    return all(
        len(wn.synsets(word)) >= 8
        for word in phrase.lower().split()
    )


def has_unknown_words(phrase: str) -> bool:
    """True if all words are lowercase AND have no WordNet entry.

    Filters foreign phrases like "Leck mich" where lowercase words
    have no English meaning. Capitalized proper names pass even if
    unknown (e.g., "Larry Goodell").
    """
    words = phrase.split()
    if not words:
        return False

    # Check if all words are lowercase (likely not a proper name)
    all_lowercase = all(w.islower() for w in words if w.isalpha())
    if not all_lowercase:
        return False

    # Check if all lowercase words have no synsets
    return all(
        len(wn.synsets(word)) == 0
        for word in words
        if word.islower() and word.isalpha()
    )

"""Integration tests for extraction correctness using spaCy NER."""

import pytest
import spacy

from kolium.parser import extract_notes, extract_people, extract_words


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


class TestPeopleFromHighlights:
    """Tests that real people are extracted and false positives are excluded."""

    def test_standalone_person_name_is_extracted(self, nlp):
        text = "*Larry Goodell*"
        assert "Larry Goodell" in extract_people(text, nlp)

    def test_person_in_multi_word_highlight_is_extracted(self, nlp):
        text = "*Ed Yourdon and Larry Constantine examined programs*"
        people = extract_people(text, nlp)
        assert "Ed Yourdon" in people
        assert "Larry Constantine" in people

    def test_real_people_survive_extraction(self, nlp):
        text = (
            "*Andre Van Der Hoek studied software design.*\n"
            "*Kent Beck wrote about tidying code.*\n"
            "*Ed Yourdon and Larry Constantine examined programs.*"
        )
        people = extract_people(text, nlp)
        assert "Andre Van Der Hoek" in people
        assert "Kent Beck" in people
        assert "Ed Yourdon" in people

    def test_concept_phrases_not_in_people(self, nlp):
        text = (
            "*Guard Clauses*\n"
            "*Code with guard clauses is easier to analyze.*\n"
            "*Batch Sizes*\n"
            "*Batch sizes matter for throughput.*\n"
            "*Reading List*\n"
        )
        people = extract_people(text, nlp)
        assert "Guard Clauses" not in people
        assert "Batch Sizes" not in people
        assert "Reading List" not in people

    def test_possessive_not_in_people(self, nlp):
        text = "*The mere presence of a system (Heisenberg's uncertainty principle).*"
        people = extract_people(text, nlp)
        assert "Heisenberg" not in people
        assert "Heisenberg's" not in people

    def test_brand_nouns_not_in_people(self, nlp):
        text = (
            "*Coupling, like the Lego piece in the night, often isn't obvious.*\n"
            "*If everyone follows the Scout rule the code will improve.*"
        )
        people = extract_people(text, nlp)
        assert "Lego" not in people
        assert "Scout" not in people

    def test_title_phrases_not_in_people(self, nlp):
        text = (
            "*Tidy*\n"
            "*Tidy First*\n"
            "*Tidy to enable the next behavior change.*"
        )
        people = extract_people(text, nlp)
        assert "Tidy" not in people
        assert "Tidy First" not in people


class TestWordsFromHighlights:
    """Tests that single-word highlights become titlecased vocabulary entries."""

    def test_single_word_highlights_become_words(self, nlp):
        text = (
            "*recapitulation*\n"
            "*muggins*\n"
            "*Prismatic*\n"
            "*belie*\n"
            "*officialdom*"
        )
        words = extract_words(text, nlp)
        assert "Recapitulation" in words
        assert "Muggins" in words
        assert "Prismatic" in words
        assert "Belie" in words
        assert "Officialdom" in words

    def test_words_are_titlecased(self, nlp):
        text = "*connascence*\n*amortizing*"
        words = extract_words(text, nlp)
        assert "Connascence" in words
        assert "Amortizing" in words

    def test_person_name_not_in_words(self, nlp):
        text = "*Larry Goodell*\n*recapitulation*"
        words = extract_words(text, nlp)
        assert "Larry Goodell" not in words
        assert "Recapitulation" in words


class TestNotesFromHighlights:
    """Tests that multi-word highlights are cleaned and formatted as notes."""

    def test_multi_word_highlight_becomes_note(self, nlp):
        text = "*I'm playing at sanity anyway.*"
        notes = extract_notes(text)
        assert len(notes) == 1
        assert notes[0] == "I'm playing at sanity anyway."

    def test_capitalises_lowercase_start(self, nlp):
        text = "*in England, the umbrella life*"
        notes = extract_notes(text)
        assert notes[0] == "In England, the umbrella life."

    def test_long_highlight_preserved(self, nlp):
        text = "*Learn when to say yes. No. Yes to life. Yes to death. Yes to love as it happens and yes when it doesn't.*"
        notes = extract_notes(text)
        assert "Learn when to say yes." in notes[0]

    def test_skips_single_word_highlights(self, nlp):
        text = "*recapitulation*\n*muggins*\n*I'm playing at sanity anyway.*"
        notes = extract_notes(text)
        assert len(notes) == 1

    def test_quote_highlight_gets_opening_quote(self, nlp):
        text = "*It's not how you live that matters it's how you die that's important.'*"
        notes = extract_notes(text)
        assert notes[0].startswith("'")

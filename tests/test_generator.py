"""Tests for document generation."""

import pytest
import spacy

from kolium.generator import generate_document


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


class TestGenerateDocument:
    def test_all_three_categories_includes_toc(self, nlp):
        text = "*Kent Beck*\n*vocabulary*\n*This is a note about something*"
        result = generate_document(text, nlp=nlp)
        assert "## Table of Contents" in result
        assert "- [People](#people)" in result
        assert "- [Notes](#notes)" in result
        assert "- [Words](#words)" in result

    def test_single_category_omits_toc(self, nlp):
        text = "*this is a highlight from a book*"
        result = generate_document(text, nlp=nlp)
        assert "## Notes" in result
        assert "Table of Contents" not in result

    def test_two_categories_includes_toc(self, nlp):
        text = "*vocabulary*\n*this is a multi word highlight*"
        result = generate_document(text, nlp=nlp)
        assert "## Table of Contents" in result
        assert "- [Notes](#notes)" in result
        assert "- [Words](#words)" in result

    def test_empty_categories_omitted(self, nlp):
        text = "*vocabulary*"
        result = generate_document(text, nlp=nlp)
        assert "## Words" in result
        assert "## People" not in result
        assert "## Notes" not in result

    def test_words_are_titlecased(self, nlp):
        text = "*hello*"
        result = generate_document(text, nlp=nlp)
        assert "- Hello" in result

    def test_words_include_definitions(self, nlp):
        text = "*muggins*"
        result = generate_document(text, nlp=nlp)
        assert "- Muggins" in result
        assert "    - Definition:" in result

    def test_words_without_definition_have_no_sub_bullet(self, nlp):
        text = "*connascence*"
        result = generate_document(text, nlp=nlp)
        assert "- Connascence" in result
        assert "Definition:" not in result

    def test_notes_are_processed(self, nlp):
        text = "*this is a highlight from a book*"
        result = generate_document(text, nlp=nlp)
        assert "- This is a highlight from a book." in result

    def test_empty_text_returns_empty(self, nlp):
        result = generate_document("", nlp=nlp)
        assert result == ""

    def test_person_names_removed_from_notes_when_in_people(self, nlp):
        text = "*Fritz Haber*\n*Heinrich Böll*\n*Hermann Göring*\n*Hermann Göring.*"
        result = generate_document(text, nlp=nlp)

        # All three should be in People section
        assert "## People" in result
        assert "- Fritz Haber" in result
        assert "- Heinrich Böll" in result
        assert "- Hermann Göring" in result

        # Notes section should be empty (person name duplicate removed)
        lines = result.split("\n")
        notes_idx = next(
            (i for i, line in enumerate(lines) if line == "## Notes"), None
        )
        if notes_idx is not None:
            # Check lines after "## Notes" heading until next section or end
            notes_content = []
            for line in lines[notes_idx + 1 :]:
                if line.startswith("## "):
                    break
                if line.strip() and not line.startswith("-"):
                    continue
                if line.strip():
                    notes_content.append(line)
            assert len(notes_content) == 0, f"Notes should be empty but got: {notes_content}"

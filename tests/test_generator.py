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

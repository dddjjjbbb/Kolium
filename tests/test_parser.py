"""Tests for parsing and extraction functions."""

import pytest

from kolium.parser import (
    _is_highlight_line,
    _normalised_lines,
    extract_notes,
    read_md_file,
    remove_nbsp,
)


class TestReadMdFile:
    def test_reads_existing_file(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("hello", encoding="utf-8")
        assert read_md_file(test_file) == "hello"

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            read_md_file("/nonexistent/path.md")


class TestRemoveNbsp:
    def test_replaces_nbsp_with_space(self):
        assert remove_nbsp("hello\xa0world") == "hello world"

    def test_leaves_normal_text_unchanged(self):
        assert remove_nbsp("hello world") == "hello world"


class TestExtractNotes:
    def test_extracts_multiword_highlights(self):
        text = "*single*\n*multi word highlight*\n*another one here*"
        notes = extract_notes(text)
        assert len(notes) == 2
        assert notes[0] == "Multi word highlight."
        assert notes[1] == "Another one here."

    def test_skips_single_word(self):
        text = "*word*\n*two words*"
        notes = extract_notes(text)
        assert len(notes) == 1

    def test_empty_text_returns_empty(self):
        assert extract_notes("") == []

    def test_extracts_two_line_highlight(self):
        text = "*This highlight spans\ntwo lines.*"
        notes = extract_notes(text)
        assert len(notes) == 1
        assert notes[0] == "This highlight spans two lines."

    def test_extracts_three_line_highlight(self):
        text = "*This highlight spans\nmultiple\nlines.*"
        notes = extract_notes(text)
        assert len(notes) == 1
        assert notes[0] == "This highlight spans multiple lines."

    def test_multiline_mixed_with_single_line(self):
        text = "*single line highlight*\n*spans\ntwo lines.*\n*word*"
        notes = extract_notes(text)
        assert len(notes) == 2
        assert notes[0] == "Single line highlight."
        assert notes[1] == "Spans two lines."


class TestNormalisedLines:
    def test_single_line_highlight_unchanged(self):
        lines = _normalised_lines("*hello world*")
        assert "*hello world*" in lines

    def test_joins_two_line_highlight(self):
        lines = _normalised_lines("*starts here\nends here.*")
        assert any("*starts here ends here.*" in line for line in lines)

    def test_joins_three_line_highlight(self):
        lines = _normalised_lines("*line one\nline two\nline three.*")
        joined = [line for line in lines if line.startswith("*") and line.endswith("*")]
        assert len(joined) == 1
        assert "line one" in joined[0]
        assert "line three.*" in joined[0]

    def test_non_highlight_lines_preserved(self):
        text = "## Chapter Title\n### Page 42 @ date\n*a highlight*"
        lines = _normalised_lines(text)
        assert "## Chapter Title" in lines

    def test_unclosed_highlight_not_lost(self):
        lines = _normalised_lines("*unclosed highlight without ending")
        assert any("unclosed" in line for line in lines)


class TestIsHighlightLine:
    def test_valid_highlight(self):
        assert _is_highlight_line("*hello world*") is True

    def test_bold_text_rejected(self):
        assert _is_highlight_line("**bold text**") is False

    def test_single_asterisk_rejected(self):
        assert _is_highlight_line("**") is False

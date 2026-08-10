"""Tests for parsing and extraction functions."""

import pytest

from kolium.parser import (
    _is_highlight_line,
    _normalised_lines,
    extract_annotations,
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


class TestExtractAnnotations:
    """Tests for extracting user-written notes after ``---`` separators."""

    def test_extracts_single_annotation_after_highlight(self):
        text = "*A highlighted passage*\n---\nMy note about this."
        assert extract_annotations(text) == ["My note about this."]

    def test_highlight_without_separator_returns_empty(self):
        text = "*A highlighted passage*"
        assert extract_annotations(text) == []

    def test_note_without_content_after_separator_returns_empty(self):
        text = "*A highlighted passage*\n---\n"
        assert extract_annotations(text) == []

    def test_empty_text_returns_empty(self):
        assert extract_annotations("") == []

    def test_multiple_highlights_with_notes_after(self):
        text = (
            "*First highlight*\n---\nFirst note\n"
            "*Second highlight*\n---\nSecond note"
        )
        annotations = extract_annotations(text)
        assert len(annotations) == 2
        assert annotations[0] == "First note"
        assert annotations[1] == "Second note"

    def test_highlight_without_note_mixed_with_annotated(self):
        text = (
            "*Highlight with note*\n---\nMy note\n"
            "*Highlight without note*\n"
            "*Another with note*\n---\nAnother note"
        )
        annotations = extract_annotations(text)
        assert len(annotations) == 2
        assert annotations[0] == "My note"
        assert annotations[1] == "Another note"

    def test_note_with_blank_lines(self):
        text = "*Highlight*\n---\nPart one\n\nPart two"
        annotations = extract_annotations(text)
        assert len(annotations) == 1
        assert annotations[0] == "Part one Part two"

    def test_note_with_multi_word_highlight(self):
        text = "*This is a\nmulti-line highlight*\n---\nNote for it."
        annotations = extract_annotations(text)
        assert annotations == ["Note for it."]

    def test_annotation_stops_at_page_header(self):
        text = (
            "*A highlight*\n---\nMy note\n"
            "### Page 42 @ 01 January 2025 01:23:44 AM\n"
            "*Another highlight*"
        )
        annotations = extract_annotations(text)
        assert annotations == ["My note"]

    def test_annotation_stops_at_chapter_header(self):
        text = (
            "*A highlight*\n---\nMy note\n"
            "## Next Chapter\n"
            "*Another highlight*"
        )
        annotations = extract_annotations(text)
        assert annotations == ["My note"]

    def test_note_before_highlight(self):
        """Note appears BEFORE the highlight it belongs to."""
        text = "---\ncut\n### Page 74 @ 05 June 2026 02:21:21 AM\n*foo bar baz,*"
        annotations = extract_annotations(text)
        assert annotations == ["cut"]

    def test_note_before_highlight_multiple(self):
        text = (
            "---\nFirst note\n### Page 10 @ ...\n*first highlight*\n"
            "---\nSecond note\n### Page 20 @ ...\n*second highlight*"
        )
        annotations = extract_annotations(text)
        assert len(annotations) == 2
        assert annotations[0] == "First note"
        assert annotations[1] == "Second note"

    def test_separator_in_non_highlight_context_yields_note(self):
        """A --- in non-highlight context still yields an annotation.
        This is safe because KOReader's markdown export only uses --- for notes."""
        text = "Some text\n---\nNot a note"
        annotations = extract_annotations(text)
        assert annotations == ["Not a note"]

    def test_canonical_format_with_blank_line_before_separator(self):
        """The canonical KOReader format: *highlight*, blank line, ---, note."""
        text = (
            "### Page 106 @ 05 June 2026 02:41:20 AM\n"
            "*me made*\n"
            "\n"
            "---\n"
            "you made"
        )
        assert extract_annotations(text) == ["you made"]

    def test_mixed_highlights_some_with_some_without_notes(self):
        text = (
            "*Highlight A*\n---\nNote A\n"
            "*Highlight B*\n"
            "*Highlight C*\n---\nNote C\n"
            "*Highlight D*"
        )
        annotations = extract_annotations(text)
        assert len(annotations) == 2
        assert annotations[0] == "Note A"
        assert annotations[1] == "Note C"

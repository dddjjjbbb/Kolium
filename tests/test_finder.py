"""Tests for Kobo highlight file discovery."""

from pathlib import Path

import pytest

from kolium.finder import BookMatch, find_epubs, find_highlights, list_all_books


@pytest.fixture()
def clipboard_dir(tmp_path):
    """Create a fake clipboard directory with sample highlight files."""
    shadowbahn = tmp_path / "2026-02-26-04-51-28-Shadowbahn.md"
    shadowbahn.write_text("# Shadowbahn\n##### Steve Erickson\n\n*some highlight*\n")

    burnout = tmp_path / "2025-03-18-02-28-43-The Burnout Society.md"
    burnout.write_text("# The Burnout Society\n##### Byung-Chul Han\n\n*tired*\n")

    border = tmp_path / "2025-04-06-23-45-03-Border Country (Library of Wales).md"
    border.write_text("# Border Country\n##### Raymond Williams\n\n*valley*\n")

    dirty = tmp_path / "2025-04-08-00-05-37-Dirty Work.md"
    dirty.write_text("# Dirty Work\n##### Larry Brown\n\n*sweat*\n")

    shadow_ticket = tmp_path / "2025-05-01-00-00-00-Shadow Ticket.md"
    shadow_ticket.write_text("# Shadow Ticket\n##### Thomas Pynchon\n\n*paranoia*\n")

    # Non-md files that should be ignored
    html_file = tmp_path / "2026-02-26-04-51-28-Shadowbahn.html"
    html_file.write_text("<html></html>")

    return tmp_path


class TestFindHighlights:
    def test_should_match_by_title_case_insensitively(self, clipboard_dir):
        matches = find_highlights("shadowbahn", clipboard_dir)

        assert len(matches) == 1
        assert matches[0].title == "Shadowbahn"

    def test_should_match_by_author_name(self, clipboard_dir):
        matches = find_highlights("erickson", clipboard_dir)

        assert len(matches) == 1
        assert matches[0].author == "Steve Erickson"

    def test_should_return_multiple_matches_for_ambiguous_query(self, clipboard_dir):
        matches = find_highlights("shadow", clipboard_dir)

        assert len(matches) == 2
        titles = {m.title for m in matches}
        assert titles == {"Shadowbahn", "Shadow Ticket"}

    def test_should_return_empty_list_when_no_matches(self, clipboard_dir):
        matches = find_highlights("nonexistent", clipboard_dir)

        assert matches == []

    def test_should_only_search_md_files(self, clipboard_dir):
        matches = find_highlights("shadowbahn", clipboard_dir)

        assert len(matches) == 1
        assert matches[0].path.suffix == ".md"

    def test_should_match_partial_title(self, clipboard_dir):
        matches = find_highlights("burnout", clipboard_dir)

        assert len(matches) == 1
        assert matches[0].title == "The Burnout Society"

    def test_should_match_by_filename_stem(self, clipboard_dir):
        matches = find_highlights("border country", clipboard_dir)

        assert len(matches) == 1
        assert matches[0].title == "Border Country"

    def test_should_populate_all_match_fields(self, clipboard_dir):
        matches = find_highlights("dirty", clipboard_dir)

        assert len(matches) == 1
        match = matches[0]
        assert match.title == "Dirty Work"
        assert match.author == "Larry Brown"
        assert match.path.name == "2025-04-08-00-05-37-Dirty Work.md"


class TestListAllBooks:
    def test_should_return_all_books_with_titles(self, clipboard_dir):
        books = list_all_books(clipboard_dir)

        titles = [b.title for b in books]
        assert titles == [
            "Border Country",
            "Dirty Work",
            "Shadow Ticket",
            "Shadowbahn",
            "The Burnout Society",
        ]

    def test_should_return_empty_for_nonexistent_dir(self, tmp_path):
        books = list_all_books(tmp_path / "nope")

        assert books == []

    def test_should_skip_files_without_title(self, tmp_path):
        no_title = tmp_path / "2025-01-01-00-00-00-empty.md"
        no_title.write_text("just some text\n")

        with_title = tmp_path / "2025-01-01-00-00-00-real.md"
        with_title.write_text("# Real Book\n##### Author\n")

        books = list_all_books(tmp_path)

        assert len(books) == 1
        assert books[0].title == "Real Book"

    def test_should_handle_files_with_invalid_utf8_bytes(self, tmp_path):
        # File with non-UTF8 bytes (latin-1 degree symbol at byte 0xb0)
        bad_encoding = tmp_path / "2025-01-01-00-00-00-bad.md"
        bad_encoding.write_bytes(b"# Title with degree \xb0 symbol\n##### Author\n")

        good_file = tmp_path / "2025-01-01-00-00-00-good.md"
        good_file.write_text("# Good Book\n##### Good Author\n")

        books = list_all_books(tmp_path)

        # Both files should be parsed, bad bytes are ignored
        assert len(books) == 2
        titles = {b.title for b in books}
        assert "Good Book" in titles
        assert "Title with degree  symbol" in titles


class TestFindEpubs:
    @pytest.fixture()
    def library_dir(self, tmp_path):
        (tmp_path / "Shadowbahn - Steve Erickson.epub").write_bytes(b"")
        (tmp_path / "The Burnout Society - Byung-Chul Han.epub").write_bytes(b"")
        (tmp_path / "Hard Rain Falling - Don Carpenter.epub").write_bytes(b"")
        (tmp_path / "some-other-file.pdf").write_bytes(b"")
        return tmp_path

    def test_should_match_epub_by_title(self, library_dir):
        matches = find_epubs("shadowbahn", library_dir)

        assert len(matches) == 1
        assert matches[0] == "Shadowbahn by Steve Erickson"

    def test_should_match_epub_by_author(self, library_dir):
        matches = find_epubs("carpenter", library_dir)

        assert len(matches) == 1
        assert matches[0] == "Hard Rain Falling by Don Carpenter"

    def test_should_return_empty_when_no_epub_matches(self, library_dir):
        assert find_epubs("nonexistent", library_dir) == []

    def test_should_return_empty_for_nonexistent_dir(self, tmp_path):
        assert find_epubs("anything", tmp_path / "nope") == []

    def test_should_only_search_epub_files(self, library_dir):
        matches = find_epubs("some-other", library_dir)

        assert matches == []


class TestBookMatch:
    def test_should_have_path_title_author_fields(self):
        match = BookMatch(
            path=Path("test.md"),
            title="Test Book",
            author="Test Author",
        )

        assert match.path == Path("test.md")
        assert match.title == "Test Book"
        assert match.author == "Test Author"

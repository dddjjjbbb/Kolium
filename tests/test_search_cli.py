"""Tests for the CLI search and browse modes."""

import pytest

from kolium.cli import main


@pytest.fixture()
def clipboard_dir(tmp_path):
    """Create a fake clipboard directory with sample highlight files."""
    shadowbahn = tmp_path / "2026-02-26-04-51-28-Shadowbahn.md"
    shadowbahn.write_text(
        "# Shadowbahn\n##### Steve Erickson\n\n"
        "## the unnamed song\n### Page 35 @ 02 December 2025 01:23:44 AM\n"
        "*stupefaction*\n"
    )

    burnout = tmp_path / "2025-03-18-02-28-43-The Burnout Society.md"
    burnout.write_text(
        "# The Burnout Society\n##### Byung-Chul Han\n\n*tired*\n"
    )

    shadow_ticket = tmp_path / "2025-05-01-00-00-00-Shadow Ticket.md"
    shadow_ticket.write_text(
        "# Shadow Ticket\n##### Thomas Pynchon\n\n*paranoia*\n"
    )

    return tmp_path


class TestSearchMode:
    def test_should_detect_search_mode_when_arg_is_not_a_file(self, clipboard_dir, capsys):
        result = main(["--clipboard-dir", str(clipboard_dir), "shadowbahn"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Processed highlights" in captured.out

    def test_should_use_file_mode_when_arg_is_existing_file(self, clipboard_dir, capsys):
        file_path = clipboard_dir / "2026-02-26-04-51-28-Shadowbahn.md"
        result = main([str(file_path)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Processed highlights" in captured.out

    def test_should_print_error_when_kobo_not_mounted(self, tmp_path, capsys):
        nonexistent = tmp_path / "does-not-exist"
        result = main(["--clipboard-dir", str(nonexistent), "shadowbahn"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "not mounted" in captured.err.lower()

    def test_should_print_no_results_message(self, clipboard_dir, capsys):
        result = main(["--clipboard-dir", str(clipboard_dir), "nonexistent"])

        assert result == 1
        captured = capsys.readouterr()
        assert "no highlights found" in captured.err.lower()

    def test_should_list_available_books_on_no_match(self, clipboard_dir, tmp_path, capsys):
        empty_library = tmp_path / "library"
        empty_library.mkdir()

        main([
            "--clipboard-dir", str(clipboard_dir),
            "--library-dir", str(empty_library),
            "nonexistent",
        ])

        captured = capsys.readouterr()
        assert "Available books" in captured.out
        assert "Shadowbahn" in captured.out

    def test_should_show_export_instructions_when_epub_found(self, clipboard_dir, tmp_path, capsys):
        library = tmp_path / "library"
        library.mkdir()
        (library / "Moby Dick - Herman Melville.epub").write_bytes(b"")

        main([
            "--clipboard-dir", str(clipboard_dir),
            "--library-dir", str(library),
            "moby dick",
        ])

        captured = capsys.readouterr()
        assert "Found on your Kobo but no exported highlights" in captured.err
        assert "Moby Dick by Herman Melville" in captured.err
        assert "Export highlights" in captured.err
        assert "tools menu" in captured.err

    def test_should_prompt_on_multiple_matches_non_tty(self, clipboard_dir, capsys, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "1")

        result = main(["--clipboard-dir", str(clipboard_dir), "shadow"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Shadow Ticket by Thomas Pynchon" in captured.out
        assert "Shadowbahn by Steve Erickson" in captured.out

    def test_should_print_searching_message(self, clipboard_dir, capsys):
        main(["--clipboard-dir", str(clipboard_dir), "burnout"])

        captured = capsys.readouterr()
        assert 'Searching Kobo highlights for "burnout"' in captured.err

    def test_should_auto_select_single_match(self, clipboard_dir, capsys):
        result = main(["--clipboard-dir", str(clipboard_dir), "burnout"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Processed highlights" in captured.out

    def test_should_list_all_books_with_list_flag(self, clipboard_dir, capsys):
        result = main(["--clipboard-dir", str(clipboard_dir), "--list"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Available books (3)" in captured.out
        assert "Shadowbahn by Steve Erickson" in captured.out
        assert "The Burnout Society by Byung-Chul Han" in captured.out
        assert "Shadow Ticket by Thomas Pynchon" in captured.out

    def test_should_error_on_list_when_kobo_not_mounted(self, tmp_path, capsys):
        nonexistent = tmp_path / "does-not-exist"
        result = main(["--clipboard-dir", str(nonexistent), "--list"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_should_list_books_alphabetically(self, clipboard_dir, capsys):
        main(["--clipboard-dir", str(clipboard_dir), "--list"])

        captured = capsys.readouterr()
        lines = [line.strip() for line in captured.out.splitlines() if line.strip().startswith(("Shadow", "The"))]
        titles = [line.split(" by ")[0] for line in lines]
        assert titles == sorted(titles, key=str.lower)

    def test_should_join_multi_word_unquoted_query(self, clipboard_dir, capsys):
        result = main(["--clipboard-dir", str(clipboard_dir), "burnout", "society"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Processed highlights" in captured.out

    def test_should_write_dated_output_file(self, clipboard_dir, tmp_path, capsys):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = main([
            "--clipboard-dir", str(clipboard_dir),
            "-o", str(output_dir / "test-output.md"),
            "shadowbahn",
        ])

        assert result == 0
        assert (output_dir / "test-output.md").exists()


class TestBrowseMode:
    def test_should_show_selection_menu_when_no_args(self, clipboard_dir, capsys, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "1")

        result = main(["--clipboard-dir", str(clipboard_dir)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Select a book" in captured.out
        assert "Shadowbahn by Steve Erickson" in captured.out

    def test_should_process_selected_book(self, clipboard_dir, capsys, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "2")

        result = main(["--clipboard-dir", str(clipboard_dir)])

        assert result == 0
        captured = capsys.readouterr()
        assert "Processed highlights" in captured.out

    def test_should_error_when_kobo_not_mounted_no_args(self, tmp_path, capsys):
        nonexistent = tmp_path / "does-not-exist"
        result = main(["--clipboard-dir", str(nonexistent)])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_should_return_error_when_no_books_found(self, tmp_path, capsys):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = main(["--clipboard-dir", str(empty_dir)])

        assert result == 1
        captured = capsys.readouterr()
        assert "no highlight files found" in captured.err.lower()

    def test_should_return_error_when_selection_cancelled(self, clipboard_dir, capsys, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "q")

        result = main(["--clipboard-dir", str(clipboard_dir)])

        assert result == 1

"""Tests for CLI output naming."""

from pathlib import Path

from kolium.cli import derive_output_name


class TestDeriveOutputName:
    def test_strips_date_prefix_and_adds_highlights(self):
        input_path = Path("2026-02-15-15-16-56-Tidy First_.md")
        assert derive_output_name(input_path) == Path("Highlights_Tidy First_.md")

    def test_preserves_parent_directory(self):
        input_path = Path("/tmp/exports/2026-02-15-15-16-56-Tidy First_.md")
        assert derive_output_name(input_path) == Path("/tmp/exports/Highlights_Tidy First_.md")

    def test_no_date_prefix_still_prepends_highlights(self):
        input_path = Path("My Book Notes.md")
        assert derive_output_name(input_path) == Path("Highlights_My Book Notes.md")

    def test_preserves_extension(self):
        input_path = Path("2026-01-01-00-00-00-Title.txt")
        assert derive_output_name(input_path) == Path("Highlights_Title.txt")

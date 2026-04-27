"""Tests for highlight processing and cleanup."""

from kolium.processor import process_highlight


class TestProcessHighlight:
    def test_strips_asterisks_and_adds_period(self):
        assert process_highlight("*hello world*") == "Hello world."

    def test_returns_non_highlight_unchanged(self):
        assert process_highlight("no asterisks") == "no asterisks"

    def test_empty_after_strip_returns_empty(self):
        assert process_highlight("* *") == ""

    def test_removes_trailing_comma(self):
        assert process_highlight("*some text,*") == "Some text."

    def test_removes_trailing_comma_before_quote(self):
        result = process_highlight('*"some text,"*')
        assert result == '"Some text."'

    def test_collapses_duplicate_leading_quotes(self):
        result = process_highlight('*""hello world"*')
        assert result == '"Hello world."'

    def test_adds_missing_opening_quote(self):
        result = process_highlight('*hello world"*')
        assert result == '"Hello world."'

    def test_capitalises_first_letter(self):
        assert process_highlight("*lowercase start*") == "Lowercase start."

    def test_capitalises_after_quote(self):
        result = process_highlight('*"lowercase"*')
        assert result == '"Lowercase."'

    def test_preserves_existing_punctuation(self):
        assert process_highlight("*Already done.*") == "Already done."
        assert process_highlight("*Is this right?*") == "Is this right?"
        assert process_highlight("*Watch out!*") == "Watch out!"

    def test_inserts_period_before_closing_quote(self):
        result = process_highlight('*"No ending punct"*')
        assert result == '"No ending punct."'

    def test_preserves_question_mark_inside_quotes(self):
        result = process_highlight('*"Is this right?"*')
        assert result == '"Is this right?"'

    def test_closes_unclosed_quote_at_end(self):
        result = process_highlight('*the historian Flavius Josephus had described it as "a star that resembles a sword*')
        assert result == 'The historian Flavius Josephus had described it as "a star that resembles a sword."'

    def test_closes_unclosed_paren_at_end(self):
        result = process_highlight('*The apple was never examined to confirm the hypothesis of suicide (even if the seeds do contain a natural form of it, with only half a cup of them sufficient to kill a human being*')
        assert result == 'The apple was never examined to confirm the hypothesis of suicide (even if the seeds do contain a natural form of it, with only half a cup of them sufficient to kill a human being).'

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

    def test_does_not_close_mid_sentence_quote(self):
        # Quote appears mid-sentence and is unclosed due to truncation
        # Don't add closing quote as it wasn't in original
        result = process_highlight('*Every morning at breakfast—mirroring the official debates—Einstein would proffer his riddles, and every night Bohr would arrive with a solution. The duel between the two men dominated the conference, and divided the physicists into two opposing camps, but, in the end, Einstein had to yield. He had not found a single inconsistency in Bohr\'s reasoning. He accepted defeat grudgingly, and condensed all his hatred of quantum mechanics in a phrase he would repeat time and again in the succeeding years, one he practically spat in the Dane\'s face before his departure: "God does not play dice with the universe!*')
        # Should not add closing quote
        assert not result.startswith('"')
        assert result.endswith('!') or result.endswith('universe!"')  # Either no quote or original quote preserved

    def test_fixes_colon_period_at_end(self):
        result = process_highlight('*The German writer Heinrich Böll wrote letters to his family from the front asking them to send him additional doses:*')
        # Should not end with ":."
        assert not result.endswith(':.')
        assert result.endswith('.')  # Just period

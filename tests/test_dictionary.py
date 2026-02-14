"""Tests for WordNet dictionary lookup."""

from kolium.dictionary import define, is_common_phrase


class TestDefine:
    def test_known_word_returns_definition(self):
        result = define("muggins")
        assert result is not None
        assert isinstance(result, str)

    def test_unknown_word_returns_none(self):
        assert define("connascence") is None

    def test_prefers_matching_lemma(self):
        result = define("recapitulation")
        assert "summary" in result.lower()


class TestIsCommonPhrase:
    def test_common_phrase_is_true(self):
        assert is_common_phrase("Guard Clauses") is True
        assert is_common_phrase("Batch Sizes") is True
        assert is_common_phrase("Reading List") is True

    def test_name_phrase_is_false(self):
        assert is_common_phrase("Kent Beck") is False
        assert is_common_phrase("Ed Yourdon") is False
        assert is_common_phrase("Larry Constantine") is False

    def test_single_common_word(self):
        assert is_common_phrase("guard") is True

    def test_single_rare_word(self):
        assert is_common_phrase("yourdon") is False

"""Tests for language resolution."""


from schemas.languages import LANGUAGE_MAP, resolve_language


class TestResolveLanguage:
    def test_resolve_german(self) -> None:
        assert resolve_language("german") == "german"

    def test_resolve_english(self) -> None:
        assert resolve_language("english") == "english"

    def test_resolve_case_insensitive(self) -> None:
        assert resolve_language("GERMAN") == "german"
        assert resolve_language("English") == "english"

    def test_resolve_unknown_returns_lowercased(self) -> None:
        assert resolve_language("Klingon") == "klingon"

    def test_all_supported_languages_resolve(self) -> None:
        for lang in LANGUAGE_MAP:
            assert resolve_language(lang) == lang

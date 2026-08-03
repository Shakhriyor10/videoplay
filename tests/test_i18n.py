import tempfile
import unittest
from pathlib import Path

from bot.i18n import LanguageStore, TEXTS


class LanguageStoreTests(unittest.TestCase):
    def test_all_languages_have_same_keys(self) -> None:
        expected = set(TEXTS["ru"])
        self.assertEqual(expected, set(TEXTS["uz"]))
        self.assertEqual(expected, set(TEXTS["en"]))

    def test_language_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "languages.json"
            store = LanguageStore(str(path))
            store.set(42, "ru")
            self.assertEqual(LanguageStore(str(path)).get(42), "ru")

    def test_default_language_is_uzbek(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = LanguageStore(str(Path(directory) / "languages.json"))
            self.assertEqual(store.get(404), "uz")

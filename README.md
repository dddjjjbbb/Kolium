# Kolium

Turns KOReader highlight exports into tidy, sorted Markdown. Splits your highlights into **People**, **Notes**, and **Words** sections using spaCy NER.

## Install

Requires Python 3.12+, the spaCy English model, and the NLTK WordNet corpus.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('wordnet')"
```

## Usage

```bash
kolium highlights.md
```

That's it. Output lands next to your input as `Highlights_<title>.md`.

If your input has KOReader's date prefix (e.g. `2026-02-15-15-16-56-Tidy First_.md`), it gets stripped automatically.

Want a custom output path? Use `-o`:

```bash
kolium highlights.md -o my-notes.md
```

## What it does

1. Strips non-breaking spaces and other KOReader quirks
2. Extracts person names via spaCy NER
3. Separates single-word highlights (vocabulary) from multi-word notes
4. Looks up WordNet definitions for vocabulary words
5. Cleans up punctuation, capitalisation, and dodgy quoting
6. Assembles a Markdown doc with a table of contents

## Tests

```bash
pytest
```

## Licence

[GNU General Public License v2.0 (GPL-2.0)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

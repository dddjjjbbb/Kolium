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

### Browse your Kobo

Plug in your Kobo and run kolium with no arguments to browse all your books:

```bash
kolium
```

An interactive arrow-key menu lets you scroll through all available books, pick one, and process its highlights immediately.

### Search by title or author

Already know which book you want? Search for it:

```bash
kolium shadowbahn
kolium erickson
kolium burnout society
```

Kolium searches the KOReader clipboard directory on your mounted Kobo, matching against filenames, titles, and authors. Single matches process immediately. Multiple matches get an interactive selection menu. No matches lists all available books so you can spot the right title.

If the book exists on your Kobo but has no exported highlights, Kolium shows instructions for exporting from KOReader.

Output lands in the current directory as `YYYY-MM-DD-Title-Highlights.md`.

### List all books

Print all books without the interactive menu (useful for scripting):

```bash
kolium --list
```

### Process a file directly

If you already have the highlight file:

```bash
kolium highlights.md
```

Output lands next to your input as `Highlights_<title>.md`.

If your input has KOReader's date prefix (e.g. `2026-02-15-15-16-56-Tidy First_.md`), it gets stripped automatically.

### Custom output path

Use `-o` with either mode:

```bash
kolium shadowbahn -o my-notes.md
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

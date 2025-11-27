# MKV Tools Bridge

Tiny wrapper around MKVToolNix command-line tools that exposes a simple
Python API for inspecting MKV files and changing the default audio track
language.

This project provides a minimal convenience layer on top of `mkvmerge` and
`mkvpropedit` so you can script language-track changes from Python instead of
building shell command strings yourself.

**What it does**

-   Parses `mkvmerge -J` JSON output into a small `MediaFile`/`Track` model.
-   Toggles the default audio track to a requested language for a single file.
-   Walks a directory tree and runs the language change operation across `.mkv` files.

**Important:** `mkvpropedit` edits files in-place. Back up important files before
running batch operations.

**Prerequisites**

-   MKVToolNix (mkvmerge, mkvpropedit) installed and available on `PATH`.
-   Python 3.12+ (uses typing and match).

## Usage (Python API)

Import the functions from `mkvtoolsBridge.py` and call them directly:

```python
from mkvtoolsBridge import (
		statFileAsJSON,
		MediaFile,
		changeDefaultTrackLanguage,
		changeDefaultTrackLanguageBatch,
)

# Inspect a file (produces an `output.json` file with the raw mkvmerge JSON)
data = statFileAsJSON(r"C:\path\to\file.mkv", output=True)
mf = MediaFile(data)
print(mf.tracks)

# Change the default audio language for a single file (example: to English)
success = changeDefaultTrackLanguage(r"C:\path\to\file.mkv", "en")
print("Success:", success)

# Batch-change a whole directory and get a list of failures
failures = changeDefaultTrackLanguageBatch(r"C:\path\to\directory", "en")
if failures:
		print("Failed to process:", failures)
```

## Errors and exceptions

-   `MediaFileParseException` — raised when the file inspection output cannot be
    parsed into the expected JSON structure.
-   `FailedToFindRequestedLanguageException` — raised when the requested language
    cannot be found on any audio track for the given file.

## Testing

There is a small test/usage file `mkv_test.py` that demonstrates the API and
contains simple unit tests. Run it with:

```
python .\mkv_test.py
```

## Safety and recommendations

-   `mkvpropedit` performs in-place edits — create backups if you need them.
-   Test on a single file before running batch operations on an entire directory.
-   You can inspect the generated `output.json` to see the raw `mkvmerge -J`
    output if something goes wrong.

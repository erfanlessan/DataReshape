# Understanding the project: the `with` statement, `open()`, and how the files fit together

This walks through the file-handling and data-writing code, explaining
the Python concepts it uses.

> **Note:** this originally described a single `main()` function that did
> all the file handling itself, all in one file. The project has since
> been split into three files:
>
> - `utils/reshape.py` — `reshape_csv(input_file, output_dir,
>   output_filename, template_file)` does the actual file reading/writing
>   for one file (the part walked through first, below), plus the
>   constants it needs (`COLUMN_MAP`, `HEADER_LINE_COUNT`, etc.).
> - `utils/folder_lookup.py` — `find_channel_folder()` locates one
>   channel's input folder by name pattern.
> - `program.py` — imports both of the above and just does the
>   orchestration: the `CHANNEL_FOLDER_TO_OUTPUT_NAME` mapping and
>   `main()`, which asks for one root directory, then loops over that
>   mapping, calling the other two functions once per channel.
>
> The core file-handling logic explained first below (the `with`
> statement, `open()`, reading the header block, the `csv` module, the
> per-row loop) is unchanged — only which file/function it lives in, and
> where its arguments come from, has moved. A section further down,
> ["How `program.py` finds the other two files"](#how-programpy-finds-the-other-two-files),
> explains the `import` lines this split introduced.

## The `open()` function

`open(path, mode, ...)` is Python's built-in for working with files. It
returns a **file object** you can read from or write to.

- `path` — the file to open, e.g. `"original_csv.csv"`.
- `mode` — a string telling Python what you intend to do:
  - `"r"` = read (the file must already exist)
  - `"w"` = write (creates the file if it doesn't exist, **overwrites** it
    if it does)
- `newline=""` — tells Python not to translate line-ending characters
  (`\n`, `\r\n`) itself. The `csv` module handles line endings on its own,
  so the Python docs recommend always passing `newline=""` when a file is
  going to be read or written through `csv`.

A file you open stays open — and holding a file open unnecessarily can
lock it, leak memory, or (for writes) leave data stuck in a buffer that
never actually reaches disk — until you explicitly `.close()` it. That's
what the `with` statement is for.

## The `with` statement

```python
with open("some_file.csv", "r") as f:
    ...  # use f here
# f is automatically closed here, even if an error happened above
```

`with` is Python's syntax for a **context manager**: it guarantees that
some cleanup action runs when the indented block finishes, whether it
finished normally or an exception was raised partway through. For files,
that cleanup is `f.close()`.

Without `with`, you'd have to write:

```python
f = open("some_file.csv", "r")
try:
    ...
finally:
    f.close()
```

`with` does exactly that, but shorter and harder to get wrong (it's easy
to forget the `try`/`finally` and accidentally leave a file open if an
error occurs).

You can open more than one file in a single `with` by separating them with
commas — that's what lines 87–90 below do.

## How `program.py` finds the other two files

```python
import os

from utils.folder_lookup import find_channel_folder
from utils.reshape import reshape_csv
```

- `utils/` is a **package** — a folder Python treats as an importable
  unit. What makes it one (rather than just an ordinary folder) is the
  presence of `utils/__init__.py`. That file is empty here — it doesn't
  need any content — its mere existence is what tells Python "this
  folder can be imported from."
- `from utils.folder_lookup import find_channel_folder` means: look
  inside the `utils` package, find the module `folder_lookup` (i.e.
  `utils/folder_lookup.py`), and from it, pull out the one name
  `find_channel_folder` — after this line, `find_channel_folder` can be
  used directly in `program.py`, exactly as if it had been defined there.
  The second `from utils.reshape import reshape_csv` line does the same
  for `reshape_csv`, from `utils/reshape.py`.
- For `import utils...` to work at all, Python has to know where to look
  for the `utils` folder. It finds it because Python automatically adds
  the directory containing the script you're running (here,
  `program.py`'s own folder) to the list of places it searches for
  imports — so `utils/`, sitting right next to `program.py`, is found
  without any extra setup. This is true whether you run
  `python3 program.py` from a terminal or press **F5** in Spyder.

## Walking through `reshape_csv()` (in `utils/reshape.py`)

### Line 68 — open the template, read-only

```python
with open(template_file, "r", newline="") as f:
```

Opens the template file (`target_format.CSV` by default) for reading and
names the resulting file object `f`. It will be automatically closed once
the indented block under this `with` ends (i.e. right after line 69).

### Line 69 — read the first N lines

```python
header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)]
```

This is a **list comprehension** — a compact way to build a list by
repeating an expression. Reading it right to left:

- `range(HEADER_LINE_COUNT)` — produces the numbers `0, 1, 2, ..., 10`
  (11 values, since `HEADER_LINE_COUNT = 11`), just to control *how many
  times* the loop repeats. The loop variable itself, `_`, is a throwaway
  name — a Python convention meaning "I don't actually need this value."
- `next(f)` — a file object is an **iterator** over its own lines; calling
  `next()` on it reads and returns exactly one line (including its
  trailing `\n`), and advances the file's internal position so the next
  call to `next()` returns the *following* line.
- Wrapping it in `[...]` collects each line returned into a list.

So this line reads the first 11 lines of the template file (the
metadata/header block) into the list `header_lines`, one line of text per
list element, and leaves the file positioned right after them — though
that no longer matters here, since the file is closed as soon as this
`with` block ends.

### Lines 71–72 — make sure the output name ends in `.csv`

```python
if not output_filename.lower().endswith(".csv"):
    output_filename += ".csv"
```

Appends `.csv` to `output_filename` when it isn't already there
(case-insensitively, via `.lower()`), so `"result"` and `"result.csv"`
both end up as `"result.csv"`.

### Lines 74–81 — put the output file's own name into cell B1

```python
first_row = next(csv.reader([header_lines[0]]))
first_row[1] = output_filename
buf = io.StringIO()
csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL).writerow(first_row)
header_lines[0] = buf.getvalue()
```

The template's first line is `"File name","GAVIML00.CSV","V 1.28"` — the
instrument's own name for itself, in column B. Rather than copy that
literally, this block replaces it with the name given to *this* output
file:

- `csv.reader([header_lines[0]])` is the same `csv.reader` used elsewhere
  for whole files, here handed a one-line list so it parses just that
  single line into a list of fields: `["File name", "GAVIML00.CSV", "V
  1.28"]`. `next(...)` pulls that one parsed row out of the reader (a
  `csv.reader` is itself an iterator, same idea as `next(f)` earlier).
- `first_row[1] = output_filename` overwrites index 1 — the second field,
  i.e. cell B1 — with the output file's name.
- `io.StringIO()` is an in-memory, file-like object: it behaves like an
  open file (you can `.write()` to it, and `csv.writer` doesn't know the
  difference) but stores what's written in memory rather than on disk.
  It's used here because `csv.writer` needs *something* file-like to
  write into, and there's no file to write this one modified line to yet
  — `outfile` isn't open until the next block.
- `csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL).writerow(first_row)`
  creates a one-off `csv.writer` around that in-memory buffer and writes
  `first_row` back out as a single properly-quoted, comma-separated line
  — `quoting=csv.QUOTE_ALL` matches the template's style of quoting every
  field, and `lineterminator="\n"` matches the plain `\n` line endings the
  template file uses (rather than `csv.writer`'s own default of `\r\n`).
- `buf.getvalue()` retrieves everything written to the in-memory buffer,
  as a string — here, the one reconstructed line, complete with its
  trailing `\n` — which replaces the original `header_lines[0]`.

### Lines 83–84 — build the output path

```python
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, output_filename)
```

- `os.makedirs(output_dir, exist_ok=True)` creates the output folder
  (including any missing parent folders) if it doesn't already exist.
  `exist_ok=True` means "don't raise an error if it's already there" —
  without it, `makedirs` would fail on the second run.
- `os.path.join(output_dir, output_filename)` combines the folder and file
  name into one path, using the correct separator for the operating
  system (`/` on Linux/macOS, `\` on Windows).

### Lines 87–90 — open the input and output files at once

```python
with (
    open(input_file, "r", newline="") as infile,
    open(output_file, "w", newline="") as outfile
):
```

A second `with` statement, this time opening **two** files at once. Since
Python 3.10, wrapping multiple `with` items in parentheses like this lets
you list each `open(...) as ...` on its own line, separated by commas —
the parenthesized form of the same thing you could also write on one
line as `with open(a) as x, open(b) as y:`. Here, the input CSV is opened
for reading (as `infile`) and the computed output path for writing (as
`outfile`). Both stay open for the whole indented block below (lines
91–113) and are both automatically closed together when that block ends,
in either order of success or failure.

(An older, also-common style writes this same two-file `with` using a
trailing `\` line continuation instead of parentheses:
`with open(a) as x, \`, then `     open(b) as y:` on the next line. Both
forms do exactly the same thing — this project uses the parenthesized
form.)

### Line 92 — write the copied header lines to the output

```python
outfile.writelines(header_lines)
```

`writelines()` writes a list of strings to a file, one after another,
without adding anything extra between them (unlike `print`, it does *not*
insert its own newlines — that's why line 69 needed to keep each line's
original trailing `\n` from the file). This writes the 11 header lines
captured earlier straight into the output file, unchanged.

### Lines 94–95 — set up CSV reading and writing

```python
reader = csv.DictReader(infile)
writer = csv.writer(outfile)
```

- `csv.DictReader(infile)` wraps the already-open `infile` so that each
  row it produces is a **dictionary** keyed by column name (taken from the
  input file's first line), e.g.
  `{"CH1_1": "25.5", "CH1_2": "25.41", ...}`. That's what lets the rest of
  the code look up columns by name (`row["CH1_1"]`) instead of by
  position.
- `csv.writer(outfile)` wraps the already-open `outfile` so you can hand it
  a plain Python list and have it correctly formatted as one CSV row
  (handling commas, quoting, etc.) and written out.

### Lines 98–113 — build and write one output row per input row

```python
for row in reader:
    data_row = [row[TIME_SOURCE_COLUMN]]
    data_row += [row[source_col] for source_col in COLUMN_MAP.values()]
    data_row += ALARM_PLACEHOLDER
    data_row += ALARM_SOURCE_PLACEHOLDER
    data_row.append(EVENT_PLACEHOLDER)
    data_row.append("")  # trailing empty field, matching the template
    writer.writerow(data_row)
```

(Shown here with its explanatory comments stripped out — the actual code
has one before each step, at lines 99, 102–103, 106, and 112.)

- `for row in reader:` — iterates over the input CSV one row at a time;
  each `row` is a dictionary as described above.
- `data_row = [row[TIME_SOURCE_COLUMN]]` — starts a new list for this
  output row, with the Time value first (`TIME_SOURCE_COLUMN` is
  `"TimeFromRecordStart_s"`).
- `data_row += [row[source_col] for source_col in COLUMN_MAP.values()]` —
  another list comprehension: for each source column name in
  `COLUMN_MAP` (in the fixed order the dictionary was written in), look up
  that value in the current row, and append all of them to `data_row` in
  one go. `+=` on a list means "extend this list with the following
  items," not "add" in the arithmetic sense.
- The next three lines (`+= ALARM_PLACEHOLDER`, `+= ALARM_SOURCE_PLACEHOLDER`,
  `.append(EVENT_PLACEHOLDER)`) tack on the fixed placeholder values for
  the columns that have no source data (`ALM-*`, `ALM-SOURCE-*`, `Event`).
  `+=` extends the list with multiple items; `.append()` adds a single
  item.
- `data_row.append("")` adds one more empty value at the very end, so the
  written row ends with a trailing comma — matching the trailing comma
  seen in every data row of `target_format.CSV`.
- `writer.writerow(data_row)` finally converts `data_row` (a plain list of
  strings) into one correctly-formatted CSV line and writes it to the
  output file.

This loop body runs once per row of the input CSV, so it produces exactly
one output row per input row. After the loop, line 115 (`return
output_file`) hands back the path that was written, so callers (like
`main()`, in `program.py`) can report it.

## `CHANNEL_FOLDER_TO_OUTPUT_NAME` — the batch's mapping (in `program.py`)

```python
CHANNEL_FOLDER_TO_OUTPUT_NAME = {
    "UU_IGBT": "GAVIML00",
    "UL_IGBT": "GAVIML01",
    ...
    "WL_FRD": "GAVIML11",
}
```

A plain dictionary, defined at module level (not inside any function) so
`main()`, defined further down in the same file, can see it. Each key is
a channel folder's name *suffix* (see below for why not the whole name);
each value is the output file name that channel should produce. Being a
`dict` also fixes an order — Python dictionaries remember insertion
order — which is what lets `main()`'s loop process channels in this same
order every run. (`find_channel_folder()`, imported from
`utils/folder_lookup.py`, doesn't reference this dictionary directly —
`main()` just passes it one suffix at a time, as an argument.)

## `find_channel_folder()` — locating a folder without knowing its exact name (in `utils/folder_lookup.py`)

```python
def find_channel_folder(root_dir, folder_suffix):
    matches = [
        path for path in glob.glob(os.path.join(root_dir, f"*{folder_suffix}"))
        if os.path.isdir(path)
    ]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected exactly one folder ending in '{folder_suffix}' inside "
            f"{root_dir!r}, found {len(matches)}: {matches}"
        )
    return matches[0]
```

Real channel folders look like `01_UU_IGBT`, `02_UL_IGBT`, etc. — a
numeric prefix, then the channel name. Rather than assume exactly what
that prefix looks like for all 12 folders, this searches for it:

- `glob.glob(pattern)` (from the standard-library `glob` module) returns a
  list of every path on disk that matches a shell-style wildcard pattern.
  `f"*{folder_suffix}"` — e.g. `"*UU_IGBT"` — means "anything, followed by
  `UU_IGBT`", so it matches `01_UU_IGBT`, `7_UU_IGBT`, or even `UU_IGBT`
  on its own, whatever the real prefix turns out to be.
- `os.path.join(root_dir, f"*{folder_suffix}")` puts that wildcard pattern
  inside `root_dir`, so only direct subfolders of the given root are
  searched, not the whole drive.
- The list comprehension `[path for path in glob.glob(...) if
  os.path.isdir(path)]` keeps only the matches that are actually folders
  (`os.path.isdir`), in case a file happened to match the same pattern.
- `if len(matches) != 1:` — if the search found anything other than
  *exactly* one folder (zero, meaning it's missing; or more than one,
  meaning the suffix was ambiguous), this `raise`s a `FileNotFoundError`
  with a message naming the folder suffix, the root directory searched,
  and every path it did find — rather than silently guessing which one
  (if any) was intended.
- If exactly one match was found, `matches[0]` — the only element of a
  one-item list — is returned as that channel's folder.

## `main()` — running the batch (in `program.py`)

```python
def main():
    output_dir = r"C:\00_Workspaces\1_lithium\2_lithium_frame_1\8_data\ProcessedData1"
    input_filename = "lr8400-all-channels.csv"

    input_root = input("Root directory containing the channel folders (e.g. .../RawData): ").strip()

    for folder_suffix, output_name in CHANNEL_FOLDER_TO_OUTPUT_NAME.items():
        try:
            input_dir = find_channel_folder(input_root, folder_suffix)
            input_file = os.path.join(input_dir, input_filename)
            output_file = reshape_csv(input_file, output_dir, output_name)
        except (FileNotFoundError, KeyError) as e:
            print(f"[{folder_suffix}] SKIPPED: {e}")
            continue
        print(f"[{folder_suffix}] Wrote reshaped data to {output_file}")
```

- `output_dir` and `input_filename` are fixed for every channel in this
  batch (same destination folder, same file name expected inside each
  channel folder), so they're set once as plain local variables rather
  than asked for.
- `input()` is still used, but now only once, for the one thing that
  varies per run: which root directory to search under.
- `for folder_suffix, output_name in CHANNEL_FOLDER_TO_OUTPUT_NAME.items():`
  — `.items()` on a dictionary gives you `(key, value)` pairs one at a
  time; unpacking each pair into two loop variables (`folder_suffix`,
  `output_name`) is a common pattern for looping over both a dictionary's
  keys and values together. This runs the loop body once per entry in
  `CHANNEL_FOLDER_TO_OUTPUT_NAME`, in the order the dictionary was
  written.
- `try` / `except (FileNotFoundError, KeyError) as e:` — this is Python's
  error-handling construct: code that might raise an exception goes under
  `try`; if it does, execution jumps to the matching `except` block
  instead of crashing the whole program. Listing two exception types in
  parentheses means "catch either of these." Here, `find_channel_folder()`
  can raise `FileNotFoundError` (see above), and `reshape_csv()` can raise
  `KeyError` if the input file it finds doesn't actually contain a column
  the mapping expects (e.g. the wrong CSV, or a differently-named
  channel). `as e` captures whichever exception object was raised, under
  the name `e`, so its message can be used afterward.
- `print(...)` then `continue` — when a channel fails, its error is
  printed with which channel it was, and `continue` skips the rest of
  *this* loop iteration, jumping straight to the next channel rather than
  stopping the whole batch. Twelve folders means one bad one shouldn't
  block reshaping the other eleven.
- When nothing raises, the `try` block runs to completion and the final
  `print` (outside the `try`) reports success for that channel instead.

### The script entry point

```python
if __name__ == "__main__":
    main()
```

Every Python module has a built-in variable `__name__`. When you *run* a
file directly (`python3 program.py`), Python sets `__name__` to the string
`"__main__"` for that file. If the same file is instead *imported* by
another script (`import program`), `__name__` is set to `"program"`
instead.

This `if` check means: "only call `main()` when this file is run directly,
not when something else imports it." It's a standard Python idiom that
lets a file be both a runnable script and something you could later import
functions from without it immediately executing.

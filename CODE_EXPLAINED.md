# Understanding `program.py`: the `with` statement, `open()`, and the main function

This walks through the file-handling and data-writing part of `program.py`,
explaining the Python concepts it uses.

> **Note:** this originally described a single `main()` function that did
> all the file handling itself. `program.py` has since been split into two
> functions: `reshape_csv(input_file, output_dir, output_filename,
> template_file)` does the actual file reading/writing (the part walked
> through below), and `main()` just asks the user four questions with
> `input()` and passes the answers to `reshape_csv()`. The core logic
> explained below (the `with` statement, `open()`, reading the header
> block, the `csv` module, the per-row loop) is unchanged — only which
> function it lives in, and where its arguments come from, has moved.

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
commas — that's what lines 86–87 below do.

## Walking through `reshape_csv()`

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

### Lines 86–87 — open the input and output files at once

```python
with open(input_file, "r", newline="") as infile, \
     open(output_file, "w", newline="") as outfile:
```

A second `with` statement, this time opening **two** files at once,
separated by a comma: the input CSV for reading (as `infile`) and the
computed output path for writing (as `outfile`). Both stay open for the
whole indented block below (lines 89–101) and are both automatically
closed together when that block ends.

The trailing `\` on line 86 is a **line continuation** — it just tells
Python "this statement keeps going on the next line," purely so the line
isn't too long to read comfortably. It has no other effect.

### Line 89 — write the copied header lines to the output

```python
outfile.writelines(header_lines)
```

`writelines()` writes a list of strings to a file, one after another,
without adding anything extra between them (unlike `print`, it does *not*
insert its own newlines — that's why line 69 needed to keep each line's
original trailing `\n` from the file). This writes the 11 header lines
captured earlier straight into the output file, unchanged.

### Lines 91–92 — set up CSV reading and writing

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

### Lines 94–101 — build and write one output row per input row

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
one output row per input row. After the loop, line 103 (`return
output_file`) hands back the path that was written, so callers (like
`main()`, below) can report it.

## `main()` — asking for the four inputs

```python
def main():
    input_dir = input("Directory containing the file to be reshaped: ").strip()
    input_filename = input("Name of the file to be reshaped: ").strip()
    output_dir = input("Destination directory for the output: ").strip()
    output_filename = input("Name to give the output CSV file: ").strip()

    input_file = os.path.join(input_dir, input_filename)
    output_file = reshape_csv(input_file, output_dir, output_filename)
    print(f"Wrote reshaped data to {output_file}")
```

- `input("some prompt: ")` is Python's built-in for interactive text
  input: it prints the prompt string, pauses execution, and returns
  whatever the user types (as a string) once they press Enter. It works
  identically whether the code is run from a terminal or from an IDE
  console like Spyder's — both just wait for you to type something.
- `.strip()` removes any leading/trailing whitespace (spaces, or an
  accidentally-included newline) from what was typed, so a stray space
  before or after a path doesn't break the file lookup.
- `os.path.join(input_dir, input_filename)` combines the directory and
  file name the user typed into one path, the same way line 84 does for
  the output side.
- The last two lines call `reshape_csv()` with the four collected values
  and print where the result went.

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

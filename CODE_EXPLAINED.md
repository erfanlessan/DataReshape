# Understanding `program.py`: the `with` statement, `open()`, and the main function

This walks through the file-handling and data-writing part of `program.py`,
explaining the Python concepts it uses.

> **Note:** this originally described a single `main()` function that read
> hardcoded file paths. `program.py` has since been generalized into a
> command-line tool: the file-handling logic below now lives in its own
> `reshape_csv(input_file, output_dir, output_filename, template_file)`
> function, and
> `main()` just parses command-line arguments (via `argparse`) and calls
> it. The concepts and the core logic explained below (the `with`
> statement, `open()`, reading the header block, the `csv` module, the
> per-row loop) are unchanged — only the line numbers and the fact that
> file paths now come from arguments instead of constants have moved.

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
commas — that's what line 62–63 below does.

## Walking through `main()`

### Line 59 — open the template, read-only

```python
with open(TEMPLATE_FILE, "r", newline="") as f:
```

Opens `target_format.CSV` for reading and names the resulting file object
`f`. It will be automatically closed once the indented block under this
`with` ends (i.e. right after line 60).

### Line 60 — read the first N lines

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

So this line reads the first 11 lines of `target_format.CSV` (the
metadata/header block) into the list `header_lines`, one line of text per
list element, and leaves the file positioned right after them — though
that no longer matters here, since the file is closed as soon as this
`with` block ends.

### Lines 62–63 — open two more files at once

```python
with open(INPUT_FILE, "r", newline="") as infile, \
     open(OUTPUT_FILE, "w", newline="") as outfile:
```

A second `with` statement, this time opening **two** files at once,
separated by a comma: `original_csv.csv` for reading (as `infile`) and
`reshaped_output.csv` for writing (as `outfile`). Both stay open for the
whole indented block below (lines 65–77) and are both automatically closed
together when that block ends.

The trailing `\` on line 62 is a **line continuation** — it just tells
Python "this statement keeps going on the next line," purely so the line
isn't too long to read comfortably. It has no other effect.

### Line 65 — write the copied header lines to the output

```python
outfile.writelines(header_lines)
```

`writelines()` writes a list of strings to a file, one after another,
without adding anything extra between them (unlike `print`, it does *not*
insert its own newlines — that's why line 60 needed to keep each line's
original trailing `\n` from the file). This writes the 11 header lines
captured earlier straight into `reshaped_output.csv`, unchanged.

### Lines 67–68 — set up CSV reading and writing

```python
reader = csv.DictReader(infile)
writer = csv.writer(outfile)
```

- `csv.DictReader(infile)` wraps the already-open `infile` so that each
  row it produces is a **dictionary** keyed by column name (taken from
  `original_csv.csv`'s first line), e.g.
  `{"CH1_1": "25.5", "CH1_2": "25.41", ...}`. That's what lets the rest of
  the code look up columns by name (`row["CH1_1"]`) instead of by
  position.
- `csv.writer(outfile)` wraps the already-open `outfile` so you can hand it
  a plain Python list and have it correctly formatted as one CSV row
  (handling commas, quoting, etc.) and written out.

### Lines 71–77 — build and write one output row per input row

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

- `for row in reader:` — iterates over `original_csv.csv` one row at a
  time; each `row` is a dictionary as described above.
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
  strings) into one correctly-formatted CSV line and writes it to
  `reshaped_output.csv`.

This loop body runs once per row of `original_csv.csv`, so it produces
exactly one output row per input row.

### Lines 82–83 — the script entry point

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

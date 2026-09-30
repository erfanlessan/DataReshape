# Understanding the project: the `with` statement, `open()`, and how the files fit together

This walks through the file-handling and data-writing code, explaining
the Python concepts it uses.

> **Note:** this originally described a single `main()` function that did
> all the file handling itself, all in one file, using only the standard
> library (`csv`, `io`, `os`). The project has since been split into three
> files, and `reshape_csv()` now uses the third-party `pandas` library for
> reading, filtering, and writing the row data:
>
> - `utils/reshape.py` — `reshape_csv(input_file, output_dir,
>   output_filename, template_file)` does the actual file reading/writing
>   for one file (the part walked through first, below), plus the
>   constants it needs (`COLUMN_MAP`, `HEADER_LINE_COUNT`, `TIME_WINDOW_S`,
>   etc.).
> - `utils/folder_lookup.py` — `find_channel_folder()` locates one
>   channel's input folder by name pattern.
> - `program.py` — imports both of the above and just does the
>   orchestration: the `CHANNEL_FOLDER_TO_OUTPUT_NAME` mapping and
>   `main()`, which asks for one root directory, then loops over that
>   mapping, calling the other two functions once per channel.
>
> The general Python concepts explained first below (the `with` statement,
> `open()`) still apply — `reshape_csv()` still uses plain `open()` for the
> template and the output file, just no longer for the input file (`pandas`
> opens that itself). A section further down, ["How `program.py` finds the
> other two
> files"](#how-programpy-finds-the-other-two-files), explains the `import`
> lines the file split introduced.

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

You can also open more than one file in a single `with` by separating them
with commas (or, since Python 3.10, by wrapping them in parentheses) —
`reshape_csv()` doesn't currently need to (it only ever has one file open
via `open()` at a time; `pandas` manages the input file's opening and
closing on its own), but you'll see this form if you look at an earlier
version of this project, or other code that reads and writes a file at
the same time.

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

### Line 76 — open the template, read-only

```python
with open(template_file, "r", newline="") as f:
```

Opens the template file (`target_format.CSV` by default) for reading and
names the resulting file object `f`. It will be automatically closed once
the indented block under this `with` ends (i.e. right after line 77).

### Line 77 — read the first N lines

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

### Lines 79–80 — make sure the output name ends in `.csv`

```python
if not output_filename.lower().endswith(".csv"):
    output_filename += ".csv"
```

Appends `.csv` to `output_filename` when it isn't already there
(case-insensitively, via `.lower()`), so `"result"` and `"result.csv"`
both end up as `"result.csv"`.

### Lines 82–89 — put the output file's own name into cell B1

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

### Lines 91–92 — build the output path

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

### Lines 98–100 — read the input CSV and filter it to the time window

```python
data = pd.read_csv(input_file, float_precision="round_trip")
time_min, time_max = TIME_WINDOW_S
data = data[data[TIME_SOURCE_COLUMN].between(time_min, time_max)]
```

- `pd.read_csv(input_file, ...)` reads the whole input CSV in one call and
  returns a `DataFrame` — pandas's table type, essentially a dictionary of
  columns (each one a `Series`, a 1-D labelled array) that all share the
  same row index. Every column's values are automatically parsed to a
  sensible type — here, the numeric columns become 64-bit floats
  (`float64`). This is the direct pandas equivalent of what
  `csv.DictReader` did row-by-row in the earlier version, except the
  entire file becomes one object up front, rather than one dictionary per
  row as you iterate.
- `float_precision="round_trip"` tells pandas's CSV parser to use the same
  (slower, but exact) decimal-to-binary conversion that Python's own
  `float()` uses. Without it, pandas's default parser can occasionally
  produce a `float64` that's 1 bit different from what `float()` would
  give for the same text — usually invisible, but avoidable, so it's
  asked for explicitly here.
- `time_min, time_max = TIME_WINDOW_S` — unpacks the 2-element tuple
  `TIME_WINDOW_S = (-600, 600)` into two separate names, for readability
  in the next line.
- `data[TIME_SOURCE_COLUMN]` selects one column (here, `"TimeFromTrigger_s"`)
  out of the DataFrame as a `Series`. `.between(time_min, time_max)`
  is a pandas `Series` method that compares every value in that column
  against the two bounds (inclusive) and returns a same-length `Series` of
  `True`/`False`.
- `data[<that True/False Series>]` — indexing a DataFrame with a
  same-length boolean `Series` is pandas's way of **filtering rows**: it
  keeps only the rows where the corresponding value is `True`, in this
  case every row whose `TimeFromTrigger_s` falls within `TIME_WINDOW_S`.
  Reassigning the result back to `data` replaces it with just those rows.

### Lines 102–114 — build the output columns

```python
output = pd.DataFrame({"Time": data[TIME_SOURCE_COLUMN]})
for target_col, source_col in COLUMN_MAP.items():
    output[target_col] = data[source_col]
for column in ALM_COLUMNS:
    output[column] = 0
for column in ALM_SOURCE_COLUMNS:
    output[column] = ""
output[EVENT_COLUMN] = 0
output["_trailing"] = ""  # trailing empty field, matching the template
```

- `pd.DataFrame({"Time": data[TIME_SOURCE_COLUMN]})` creates a brand-new,
  empty-except-for-one-column DataFrame called `output`, whose first (and
  so far only) column, `"Time"`, holds the filtered `TimeFromTrigger_s`
  values. Building a fresh DataFrame (rather than modifying `data` in
  place) keeps `output`'s columns in exactly the order they're added,
  which matters here because that order becomes the output file's column
  order.
- `for target_col, source_col in COLUMN_MAP.items(): output[target_col] =
  data[source_col]` — the same `.items()` loop pattern used elsewhere
  (see `main()`, below), but here each iteration **adds a new column** to
  `output`, named `target_col` (e.g. `"UU"`), containing the values of
  `data`'s `source_col` column (e.g. `"CH2_1_UU_V"`). This single loop is
  what does the renaming-and-reordering that the old code built up one
  list element at a time.
- The next two `for` loops add the four `ALM-*` columns (each filled with
  the single value `0`) and the four `ALM-SOURCE-*` columns (each filled
  with `""`). Assigning a single value like `output[column] = 0` to a
  DataFrame column fills every row with that same value — pandas calls
  this **broadcasting**.
- `output[EVENT_COLUMN] = 0` adds the `"Event"` column the same way.
- `output["_trailing"] = ""` adds one more, unnamed-in-the-output column,
  purely so the written row ends with an extra empty field — the same
  trailing comma the earlier, non-pandas version added with
  `data_row.append("")`. Its Python name (`"_trailing"`) never appears in
  the output, since the file is written without a header row (see below).

### Lines 116–118 — write the header lines, then the data

```python
with open(output_file, "w", newline="") as outfile:
    outfile.writelines(header_lines)
    output.to_csv(outfile, header=False, index=False, lineterminator="\n")
```

- `with open(output_file, "w", newline="") as outfile:` opens just the
  output file (unlike the input file, which `pandas` opened and closed on
  its own inside `pd.read_csv()`).
- `outfile.writelines(header_lines)` writes the 11 template header lines
  first, exactly as before.
- `output.to_csv(outfile, ...)` then writes the DataFrame itself,
  appending to the same already-open file handle rather than creating a
  new file (pandas accepts an open file object here just as readily as a
  path). Three arguments matter:
  - `header=False` — don't write `output`'s own column names
    (`"Time"`, `"UU"`, ...) as a header row; the template's own header
    rows, just written above, already serve that purpose.
  - `index=False` — don't write pandas's row index (0, 1, 2, ...) as an
    extra leading column; only the data columns are wanted.
  - `lineterminator="\n"` — matches the plain `\n` line endings used
    elsewhere in this file, rather than pandas's platform default.

### Line 120 — return the output path and row count

```python
return output_file, len(output)
```

Returns two values at once, as a **tuple** — Python doesn't need any
special syntax for this; separating two expressions with a comma after
`return` is enough. `len(output)` on a DataFrame gives its number of
rows, i.e. how many data rows actually fell inside `TIME_WINDOW_S` for
this particular input file. `main()` (below) uses this to check that
every channel produced the same number of rows.

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

    row_counts = {}
    for folder_suffix, output_name in CHANNEL_FOLDER_TO_OUTPUT_NAME.items():
        try:
            input_dir = find_channel_folder(input_root, folder_suffix)
            input_file = os.path.join(input_dir, input_filename)
            output_file, row_count = reshape_csv(input_file, output_dir, output_name)
        except (FileNotFoundError, KeyError) as e:
            print(f"[{folder_suffix}] SKIPPED: {e}")
            continue
        row_counts[folder_suffix] = row_count
        print(f"[{folder_suffix}] Wrote {row_count} rows to {output_file}")

    if row_counts and len(set(row_counts.values())) > 1:
        print("WARNING: channels do not all have the same number of rows:")
        for folder_suffix, row_count in row_counts.items():
            print(f"  {folder_suffix}: {row_count} rows")
```

- `output_dir` and `input_filename` are fixed for every channel in this
  batch (same destination folder, same file name expected inside each
  channel folder), so they're set once as plain local variables rather
  than asked for.
- `input()` is still used, but now only once, for the one thing that
  varies per run: which root directory to search under.
- `row_counts = {}` starts an empty dictionary that will collect
  `{folder_suffix: row_count}` for every channel that succeeds, so the
  counts can be compared once the whole loop is done.
- `for folder_suffix, output_name in CHANNEL_FOLDER_TO_OUTPUT_NAME.items():`
  — `.items()` on a dictionary gives you `(key, value)` pairs one at a
  time; unpacking each pair into two loop variables (`folder_suffix`,
  `output_name`) is a common pattern for looping over both a dictionary's
  keys and values together. This runs the loop body once per entry in
  `CHANNEL_FOLDER_TO_OUTPUT_NAME`, in the order the dictionary was
  written.
- `output_file, row_count = reshape_csv(...)` — unpacks the 2-item tuple
  `reshape_csv()` now returns (see its last line, above) into two separate
  names in one step, the same way `folder_suffix, output_name` was
  unpacked from `.items()` just above.
- `try` / `except (FileNotFoundError, KeyError) as e:` — this is Python's
  error-handling construct: code that might raise an exception goes under
  `try`; if it does, execution jumps to the matching `except` block
  instead of crashing the whole program. Listing two exception types in
  parentheses means "catch either of these." Here, `find_channel_folder()`
  can raise `FileNotFoundError` (see above), and `reshape_csv()` can raise
  `KeyError` if the input file it finds doesn't actually contain a column
  the mapping (or `TIME_SOURCE_COLUMN`) expects (e.g. the wrong CSV, or a
  differently-named channel). `as e` captures whichever exception object
  was raised, under the name `e`, so its message can be used afterward.
- `print(...)` then `continue` — when a channel fails, its error is
  printed with which channel it was, and `continue` skips the rest of
  *this* loop iteration, jumping straight to the next channel rather than
  stopping the whole batch. Twelve folders means one bad one shouldn't
  block reshaping the other eleven. Note that a channel that hits this
  `continue` is never added to `row_counts` at all.
- When nothing raises, `row_counts[folder_suffix] = row_count` records
  that channel's count, and the final `print` (outside the `try`) reports
  success for that channel instead.
- After the loop, `set(row_counts.values())` collects the distinct row
  counts seen across every channel that succeeded — a `set` automatically
  drops duplicates, so if every channel produced the same count, this set
  has exactly one element. `len(...) > 1` checks for more than one
  distinct count, i.e. at least one channel disagrees with the others; the
  `row_counts and` before it just guards against running this check (and
  printing a confusing warning) when the batch found zero successful
  channels at all. If the counts do disagree, every channel's count is
  printed so it's clear which one(s) are off.

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

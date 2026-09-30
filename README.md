# CSV Reshape Script

Converts a raw data-logger CSV (like `original_csv.csv`) into the layout
used by `target_format.CSV` (a Graphtec-style instrument format).
`utils/reshape.py`'s `reshape_csv()` handles one file at a time;
`program.py`'s `main()` batches this over a fixed set of per-channel
subfolders (IGBT/FRD × UU/UL/VU/VL/WU/WL) under a single root directory
you're asked for once, writing one named output file per channel.

## Project layout

```
program.py             entry point: the channel mapping and main()
utils/
    reshape.py          reshape_csv() and its column mapping/constants
    folder_lookup.py     find_channel_folder(), the per-channel folder finder
target_format.CSV      the instrument-format template (header rows + column layout)
data_reshape.md         the original CH1_x/CH2_x -> named-column mapping spec
```

`program.py` imports `reshape_csv` and `find_channel_folder` from `utils`
and focuses on orchestration: the `CHANNEL_FOLDER_TO_OUTPUT_NAME` mapping
and the batch loop in `main()`. Everything reusable — reading the
template, building each output row, locating a channel's folder — lives
in `utils/`.

## What it does

1. **Copies the header/metadata rows from the template.** The first 11
   lines of `target_format.CSV` (`File name`, `Title comment`, `Trigger
   Time`, `Ch`, `Mode`, `Range`, `Comment`, `Scaling`, `Ratio`, `Offset`,
   and the `Time`/units row: `"Time","1-1[V]","1-2[V]",...,"Event",`)
   describe the instrument format itself. `original_csv.csv` has no
   equivalent metadata, so these 11 lines are copied from the template
   into the output file, with one change: **cell B1** (the second field of
   the `"File name",...` row) is replaced with the name given to the
   output file, instead of the template's own file name
   (`GAVIML00.CSV`).

2. **Builds the `Time` column from `TimeFromRecordStart_s`.** The target
   format's `Time` column values (`0, 0.1, 0.2, ...`) match
   `TimeFromRecordStart_s` in the original data exactly, so that's the
   source column used.

3. **Maps each named data column to its source column**, based on
   `data_reshape.md`:

   | Target column | Source column         |
   |----------------|------------------------|
   | UU             | CH2_1_UU_V             |
   | UL             | CH2_2_UL_V             |
   | VU             | CH2_3_VU_V             |
   | VL             | CH2_4_VL_V             |
   | WU             | CH2_5_WU_V             |
   | WL             | CH2_6_WL_V             |
   | Therm          | CH2_8_Thermistor_V     |
   | Amb            | CH2_7_Ambient_degC     |
   | Tuu            | CH1_6                  |
   | Tul            | CH1_12                 |
   | Tvu            | CH1_4                  |
   | Tvl            | CH1_10                 |
   | Twu            | CH1_2                  |
   | Twl            | CH1_8                  |
   | Duu            | CH1_5                  |
   | Dul            | CH1_11                 |
   | Dvu            | CH1_3                  |
   | Dvl            | CH1_9                  |
   | Dwu            | CH1_1                  |
   | Dwl            | CH1_7                  |

   **Note on `CH1_8`:** `data_reshape.md` literally maps both `CH1_2` and
   `CH1_8` to `Twu`, which would leave `Twl` with no source at all. Every
   other channel follows a `Dxx`/`Txx` upper/lower pairing pattern
   (e.g. `Dwu`/`Twu`, `Dwl`/`Twl`), so `CH1_8` is treated here as `Twl`
   instead of the literal (duplicate) `Twu`.

4. **Fills the remaining columns with placeholder values.** The target
   format also has `ALM-1..4`, `ALM-SOURCE-1..4`, and `Event` columns.
   These have no corresponding data in `original_csv.csv`, so every output
   row uses the same placeholder values the sample template uses:
   `ALM-1..4 = 0`, `ALM-SOURCE-1..4 = ""` (empty), `Event = 0`.

5. **Writes one output row per input row**, in the exact column order
   required by the target format, followed by a trailing empty field
   (matching the trailing comma seen in `target_format.CSV`).

## Known simplifications

- Numeric values are written as plain numbers/strings passed through from
  the source CSV, not reformatted into the target sample's scientific
  notation (e.g. `1.28500E+00`).
- Empty `ALM-SOURCE-*` fields are written unquoted, whereas the sample
  target file quotes them (`""`).

If the tool that consumes `reshaped_output.csv` requires exact formatting
to match `target_format.CSV` (scientific notation, quoted empty strings),
the script will need to be updated to reproduce that formatting.

## Usage

```bash
python3 program.py
```

Running the script (from a terminal or as a Spyder "Run file") asks once
for the root directory that contains all 12 channel subfolders:

```
Root directory containing the channel folders (e.g. .../RawData): C:\...\8_data\RawData
```

It then loops over `CHANNEL_FOLDER_TO_OUTPUT_NAME` (defined near the top
of `program.py`, above `main()`), and for each channel:

1. Searches directly inside the root directory for the one subfolder whose
   name *ends with* that channel's suffix (e.g. `UU_IGBT` matches
   `01_UU_IGBT`, whatever numeric prefix it has).
2. Looks for `lr8400-all-channels.csv` inside that subfolder.
3. Reshapes it and writes the result to the fixed output directory (also
   set near the top of `main()`), named after that channel (e.g.
   `GAVIML00.csv`, `GAVIML01.csv`, ...).

If a channel's folder can't be found (missing, or more than one folder
matches that suffix), that channel is skipped with a printed message and
the rest of the batch still runs.

To point this at a different machine's folder layout, edit the constants
at the top of `main()`:

- `output_dir` — where all the reshaped files get written.
- `input_filename` — the file name expected inside each channel folder.
- `CHANNEL_FOLDER_TO_OUTPUT_NAME` — which folder suffix produces which
  output file name.

### Reshaping a single file instead

`reshape_csv(input_file, output_dir, output_filename)`, in
`utils/reshape.py`, is the underlying function `main()` calls per channel,
and remains a plain function you can call yourself for one file at a
time. From a terminal or your own script:

```python
from utils.reshape import reshape_csv

reshape_csv("data/original_csv.csv", "output", "my_result.csv")
```

Or interactively from Spyder's console, once `program.py` has been run
(F5) — its `from utils.reshape import reshape_csv` line at the top makes
`reshape_csv` available in the console too, without needing to repeat the
import:

```python
reshape_csv("data/original_csv.csv", "output", "my_result.csv")
```

## Using it from Spyder

`input()` works the same in Spyder's IPython console as it does in a
terminal, so pressing **F5** (Run file) prompts for the root directory
right there in the console and runs the same batch described above.
Relative paths are resolved against Spyder's current working directory
(shown in its "Files"/toolbar, and changeable there).

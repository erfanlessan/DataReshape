# CSV Reshape Script

`program.py` converts `original_csv.csv` (raw data-logger export) into the
layout used by `target_format.CSV` (a Graphtec-style instrument format),
writing the result to `reshaped_output.csv`.

## What it does

1. **Copies the header/metadata rows as-is.** The first 11 lines of
   `target_format.CSV` (`File name`, `Title comment`, `Trigger Time`, `Ch`,
   `Mode`, `Range`, `Comment`, `Scaling`, `Ratio`, `Offset`, and the
   `Time`/units row: `"Time","1-1[V]","1-2[V]",...,"Event",`) describe the
   instrument format itself. `original_csv.csv` has no equivalent metadata,
   so these 11 lines are copied verbatim from the template into the output
   file, unchanged.

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

Reads `original_csv.csv` and `target_format.CSV` from the current directory
and writes `reshaped_output.csv`.

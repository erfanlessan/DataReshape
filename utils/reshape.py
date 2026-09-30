# -*- coding: utf-8 -*-
"""Core CSV-reshaping logic: convert one data-logger CSV into the layout
used by target_format.CSV."""

import csv
import io
import os

import pandas as pd

# Falls back to the current working directory if __file__ isn't defined
# (e.g. when this file's code is run via exec() rather than as a script).
if "__file__" in globals():
    _UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(_UTILS_DIR)
else:
    PROJECT_ROOT = os.getcwd()
DEFAULT_TEMPLATE_FILE = os.path.join(PROJECT_ROOT, "target_format.CSV")

# Number of leading metadata/header lines in the template that describe the
# instrument format (File name, Title comment, Trigger Time, Ch, Mode,
# Range, Comment, Scaling, Ratio, Offset, and the Time/units row: "Time",
# "1-1[V]", "1-2[V]", ...) and are copied as-is.
HEADER_LINE_COUNT = 11

# Target data column (in output order) -> source column in the input CSV.
# Order matches the "Comment" row of target_format.CSV.
# Note: data_reshape.md maps both CH1_2 and CH1_8 to "Twu", which would leave
# "Twl" without a source. Following the Dxx/Txx pairing pattern used by every
# other channel, CH1_8 is treated here as "Twl".
COLUMN_MAP = {
    "UU": "CH2_1_UU_V",
    "UL": "CH2_2_UL_V",
    "VU": "CH2_3_VU_V",
    "VL": "CH2_4_VL_V",
    "WU": "CH2_5_WU_V",
    "WL": "CH2_6_WL_V",
    "Therm": "CH2_8_Thermistor_V",
    "Amb": "CH2_7_Ambient_degC",
    "Tuu": "CH1_6",
    "Tul": "CH1_12",
    "Tvu": "CH1_4",
    "Tvl": "CH1_10",
    "Twu": "CH1_2",
    "Twl": "CH1_8",
    "Duu": "CH1_5",
    "Dul": "CH1_11",
    "Dvu": "CH1_3",
    "Dvl": "CH1_9",
    "Dwu": "CH1_1",
    "Dwl": "CH1_7",
}

# TimeFromTrigger_s runs negative before the trigger, hits 0 at the
# trigger, then increments positively. Using it (rather than
# TimeFromRecordStart_s) as the output Time column, and keeping only rows
# within TIME_WINDOW_S of the trigger, gives every channel's output the
# same time span relative to the trigger event.
TIME_SOURCE_COLUMN = "TimeFromTrigger_s"
TIME_WINDOW_S = (-600, 600)  # inclusive (seconds before trigger, seconds after)

# The template's ALM-*, ALM-SOURCE-*, and Event columns have no equivalent
# in the input data, so every output row gets the same placeholder values
# the sample template uses.
ALM_COLUMNS = ["ALM-1", "ALM-2", "ALM-3", "ALM-4"]
ALM_SOURCE_COLUMNS = ["ALM-SOURCE-1", "ALM-SOURCE-2", "ALM-SOURCE-3", "ALM-SOURCE-4"]
EVENT_COLUMN = "Event"


def reshape_csv(input_file, output_dir, output_filename, template_file=DEFAULT_TEMPLATE_FILE):
    """Reshape a single input CSV into the target format and write it to
    output_dir/output_filename. Returns (output_file, row_count): the path
    of the file that was written, and how many data rows it contains."""

    # Create list onject 'header lines' storing template file header columns
    with open(template_file, "r", newline="") as f:
        header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)]

    if not output_filename.lower().endswith(".csv"):
        output_filename += ".csv"

    # Header row 1 is `"File name","<name>","<version>"` in the template
    # (e.g. "GAVIML00.CSV"). Replace cell B1 with the name being given to
    # this output file.
    first_row = next(csv.reader([header_lines[0]]))
    first_row[1] = output_filename
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL).writerow(first_row)
    header_lines[0] = buf.getvalue()

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_filename)

    # Read the input data and keep only the rows within TIME_WINDOW_S of
    # the trigger, so every channel's output covers the same time span.
    # float_precision="round_trip" avoids pandas's default (faster but
    # occasionally 1-bit-off) float parser subtly changing values.
    data = pd.read_csv(input_file, float_precision="round_trip")
    time_min, time_max = TIME_WINDOW_S
    data = data[data[TIME_SOURCE_COLUMN].between(time_min, time_max)]

    # Build the output columns, in the exact order the target format
    # expects: Time, then every mapped channel (renamed/reordered per
    # COLUMN_MAP), then the ALM/Event placeholders and a trailing empty
    # field.
    output = pd.DataFrame({"Time": data[TIME_SOURCE_COLUMN]})
    for target_col, source_col in COLUMN_MAP.items():
        output[target_col] = data[source_col]
    for column in ALM_COLUMNS:
        output[column] = 0
    for column in ALM_SOURCE_COLUMNS:
        output[column] = ""
    output[EVENT_COLUMN] = 0
    output["_trailing"] = ""  # trailing empty field, matching the template

    with open(output_file, "w", newline="") as outfile:
        outfile.writelines(header_lines)
        output.to_csv(outfile, header=False, index=False, lineterminator="\n")

    return output_file, len(output)

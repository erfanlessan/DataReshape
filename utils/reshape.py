# -*- coding: utf-8 -*-
"""Core CSV-reshaping logic: convert one data-logger CSV into the layout
used by target_format.CSV."""

import csv
import io
import os

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

TIME_SOURCE_COLUMN = "TimeFromRecordStart_s"

# The template's ALM-*, ALM-SOURCE-*, and Event columns have no equivalent
# in the input data, so every data row gets the same placeholder values the
# sample template uses.
ALARM_PLACEHOLDER = ["0", "0", "0", "0"]
ALARM_SOURCE_PLACEHOLDER = ["", "", "", ""]
EVENT_PLACEHOLDER = "0"


def reshape_csv(input_file, output_dir, output_filename, template_file=DEFAULT_TEMPLATE_FILE):
    """Reshape a single input CSV into the target format and write it to
    output_dir/output_filename. Returns the path of the file that was
    written."""

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

    # Open input and output csv files
    with (
        open(input_file, "r", newline="") as infile,
        open(output_file, "w", newline="") as outfile
    ):
        # Write header_lines to outfile starting from top left of csv
        outfile.writelines(header_lines)

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)

        # Iterate through all rows in reader, write each row into data_row list
        for row in reader:
            # Time column for row vector being constructed
            data_row = [row[TIME_SOURCE_COLUMN]]

            # Data columns (Vce, Tamb, Tc, Vtherm) for row vector being made
            # Order data in the order specified by COLUMN_MAP.values()
            data_row += [row[source_col] for source_col in COLUMN_MAP.values()]

            # Alarm and event placeholders to match target format
            data_row += ALARM_PLACEHOLDER
            data_row += ALARM_SOURCE_PLACEHOLDER
            data_row.append(EVENT_PLACEHOLDER)
            data_row.append("")  # trailing empty field, matching the template

            # For row iteration, write data_row list to target csv
            writer.writerow(data_row)

    return output_file

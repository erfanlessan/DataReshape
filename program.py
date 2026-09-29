# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:54:44 2026

@author: lesser01
"""

import csv
import io
import os

# Falls back to the current working directory if __file__ isn't defined
# (e.g. when this file's code is run via exec() rather than as a script).
if "__file__" in globals():
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    SCRIPT_DIR = os.getcwd()
DEFAULT_TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "target_format.CSV")

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

    with open(input_file, "r", newline="") as infile, \
         open(output_file, "w", newline="") as outfile:

        outfile.writelines(header_lines)

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            data_row = [row[TIME_SOURCE_COLUMN]]
            data_row += [row[source_col] for source_col in COLUMN_MAP.values()]
            data_row += ALARM_PLACEHOLDER
            data_row += ALARM_SOURCE_PLACEHOLDER
            data_row.append(EVENT_PLACEHOLDER)
            data_row.append("")  # trailing empty field, matching the template
            writer.writerow(data_row)

    return output_file


def main():
    """Prompt for the four pieces of information needed to reshape one
    file, then do it. Works the same whether run from a terminal or from
    Spyder's console (both support input())."""
    input_dir = input("Directory containing the file to be reshaped: ").strip()
    input_filename = input("Name of the file to be reshaped: ").strip()
    output_dir = input("Destination directory for the output: ").strip()
    output_filename = input("Name to give the output CSV file: ").strip()

    input_file = os.path.join(input_dir, input_filename)
    output_file = reshape_csv(input_file, output_dir, output_filename)
    print(f"Wrote reshaped data to {output_file}")


if __name__ == "__main__":
    main()

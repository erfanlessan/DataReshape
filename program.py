# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:54:44 2026

@author: lesser01
"""

import argparse
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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


def reshape_csv(input_file, output_dir, template_file=DEFAULT_TEMPLATE_FILE):
    """Reshape a single input CSV into the target format and write it into
    output_dir. Returns the path of the file that was written."""
    with open(template_file, "r", newline="") as f:
        header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)]

    os.makedirs(output_dir, exist_ok=True)
    input_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{input_name}_reshaped.csv")

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
    parser = argparse.ArgumentParser(
        description="Reshape a data-logger CSV into the target_format.CSV layout."
    )
    parser.add_argument("input_file", help="Path to the CSV file to reshape")
    parser.add_argument(
        "-o", "--output-dir", default="output",
        help="Folder to write the reshaped CSV into (default: output)",
    )
    parser.add_argument(
        "-t", "--template", default=DEFAULT_TEMPLATE_FILE,
        help=f"Path to the target format template CSV (default: {DEFAULT_TEMPLATE_FILE})",
    )
    args = parser.parse_args()

    output_file = reshape_csv(args.input_file, args.output_dir, args.template)
    print(f"Wrote reshaped data to {output_file}")


if __name__ == "__main__":
    main()

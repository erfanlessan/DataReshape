# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:54:44 2026

@author: lesser01
"""

import csv

INPUT_FILE = "original_csv.csv"
TEMPLATE_FILE = "target_format.CSV"
OUTPUT_FILE = "reshaped_output.csv"

# Number of leading metadata/header lines in the template that describe the
# instrument format (File name, Title comment, Trigger Time, Ch, Mode,
# Range, Comment, Scaling, Ratio, Offset, Time) and are copied as-is.
HEADER_LINE_COUNT = 10

# Target data column (in output order) -> source column in original_csv.csv
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
# in original_csv.csv, so every data row gets the same placeholder values
# the sample template uses.
ALARM_PLACEHOLDER = ["0", "0", "0", "0"]
ALARM_SOURCE_PLACEHOLDER = ["", "", "", ""]
EVENT_PLACEHOLDER = "0"


def main():
    with open(TEMPLATE_FILE, "r", newline="") as f:
        header_lines = [next(f) for _ in range(HEADER_LINE_COUNT)]

    with open(INPUT_FILE, "r", newline="") as infile, \
         open(OUTPUT_FILE, "w", newline="") as outfile:

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

    print(f"Wrote reshaped data to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

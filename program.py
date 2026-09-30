# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:54:44 2026

@author: lesser01
"""

import csv
import glob
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


# Each RawData channel folder (identified by its name's suffix, since the
# numeric prefix in front of it, e.g. "01_", isn't assumed to be fixed or
# known) -> the output file name it should produce.
CHANNEL_FOLDER_TO_OUTPUT_NAME = {
    "UU_IGBT": "GAVIML00",
    "UL_IGBT": "GAVIML01",
    "VU_IGBT": "GAVIML02",
    "VL_IGBT": "GAVIML03",
    "WU_IGBT": "GAVIML04",
    "WL_IGBT": "GAVIML05",
    "UU_FRD": "GAVIML06",
    "UL_FRD": "GAVIML07",
    "VU_FRD": "GAVIML08",
    "VL_FRD": "GAVIML09",
    "WU_FRD": "GAVIML10",
    "WL_FRD": "GAVIML11",
}


def find_channel_folder(root_dir, folder_suffix):
    """Find the one subfolder of root_dir whose name ends with
    folder_suffix (e.g. "UU_IGBT" matches "01_UU_IGBT"), regardless of
    whatever prefix comes before it. Raises FileNotFoundError if there
    isn't exactly one match."""
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


def main():
    """Ask once for the root folder containing all the channel
    subfolders, then reshape every channel's file in one go, using
    CHANNEL_FOLDER_TO_OUTPUT_NAME to find each input folder and name its
    output file. Works the same whether run from a terminal or from
    Spyder's console (both support input())."""
    output_dir = r"C:\00_Workspaces\1_lithium\2_lithium_frame_1\8_data\ProcessedData1"
    input_filename = "lr8400-all-channels.csv"

    input_root = input("Root directory containing the channel folders (e.g. .../RawData): ").strip()

    for folder_suffix, output_name in CHANNEL_FOLDER_TO_OUTPUT_NAME.items():
        try:
            input_dir = find_channel_folder(input_root, folder_suffix)
            input_file = os.path.join(input_dir, input_filename)
            output_file = reshape_csv(input_file, output_dir, output_name)
        except (FileNotFoundError, KeyError) as e:
            print(f"[{folder_suffix}] SKIPPED: {e}")
            continue
        print(f"[{folder_suffix}] Wrote reshaped data to {output_file}")


if __name__ == "__main__":
    main()

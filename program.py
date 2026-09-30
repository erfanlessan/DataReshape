# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 12:54:44 2026

@author: lesser01
"""

import os

from utils.folder_lookup import find_channel_folder
from utils.reshape import reshape_csv

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

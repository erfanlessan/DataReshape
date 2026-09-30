# -*- coding: utf-8 -*-
"""Helper for locating a channel's input folder by name suffix, without
assuming its exact numeric prefix."""

import glob
import os


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

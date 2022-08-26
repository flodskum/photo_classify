# Utility functions
# Copyright (c) 2022 Jeremy Johnson
# SPDX-Identifier: MIT License
from __future__ import annotations

import sys
import datetime
import re
from pathlib import Path
from typing import Any


EXTENSIONS = [".jpg", ".heic"]
DATE_FORMAT_EXIF = "%Y:%m:%d %H:%M:%S"
DATE_FORMAT_FILE = "%Y%m%d_%H%M%S"

REGEX_MARKED_FILES = r"[a-z]_[0-9]+.*"

def get_file_list(path: Path, extensions: list[str] = None) -> list[dict[str,Any]]:
    """Get a list of files as dictionaries of file, status."""
    if extensions is None:
        extensions = EXTENSIONS
    files = path.glob("*")
    file_list = []
    for f in files:
        if f.name[0] == "." or f.suffix.lower() not in extensions:
            #  Skip over hidden/special or files without correct extension
            continue
        match = re.match(REGEX_MARKED_FILES, f.name)
        name = f.name[2:] if match else f.name
        fdict = { "unmarked_name": name, "file": f, "status": ""}
        file_list.append(fdict)

    file_list = sorted(file_list, key = lambda fl: fl["unmarked_name"])
    
    return file_list

def convert_from_stat_datetime(stat_date) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(stat_date)

def convert_from_exif_datetime(raw_date: str) -> datetime.datetime:
    return datetime.datetime.strptime(raw_date, DATE_FORMAT_EXIF)

def convert_to_file_datetime(dt: datetime.datetime) -> str:
    return dt.strftime(DATE_FORMAT_FILE)

def convert_from_file_datetime(file_date: str) -> datetime.datetime:
    return datetime.datetime.strptime(file_date, DATE_FORMAT_FILE)


if __name__ == "__main__":
    print("Not runnable")
    sys.exit(0)

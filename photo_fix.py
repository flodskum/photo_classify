#!/usr/bin/env python3
# Copyright (c) 2022 Jeremy Johnson
# SPDX-Identifier: MIT License
from __future__ import annotations

import os
import logging
import sys
import argparse
import re
import piexif

from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener
from photo_utils import get_file_list, EXTENSIONS
from photo_utils import convert_from_exif_datetime,  convert_from_stat_datetime
from photo_utils import convert_to_file_datetime, convert_from_file_datetime

# Allow loading of HEIC files
register_heif_opener()

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("path", type=Path, help="Directory containing files to fix")
    parser.add_argument("--dummy-run", action="store_true", help="Show operations without doing them")
    parser.add_argument("--fix-timestamps", action="store_true", help="Set the creation/modification timestamps to the filename info (Only needed for files without EXIF info)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show debug")

    return parser.parse_args()

EXIF = "Exif"
EXIF_DATE = "DateTimeOriginal"
REGEX_FILE_NAME_DATE = r"([1-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9]).*"
REGEX_FILE_NAME_DATE_IMG = f"IMG[\-_]{REGEX_FILE_NAME_DATE}"

EXTENSIONS_MOVIES = [".mp4"]

def main():
    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    files = get_file_list(args.path, EXTENSIONS + EXTENSIONS_MOVIES)
    failed = []
    dummy = "DUMMY_RUN: " if args.dummy_run else ""

    for num, file in enumerate(files):
        prefix = f"{dummy}{num+1}/{len(files)}"
        path = file["file"]
        name = path.name

        # Check if the unmarked name already contains the datetime string
        # Unmarked name is one without a rating latter at the start (a_2022...jpg)
        match = re.match(REGEX_FILE_NAME_DATE, file["unmarked_name"])
        if not match:
            if args.fix_timestamps:
                logging.info(f"{prefix} {name} - skipping can't fix timestamps on in-correct filename")
            # Check if the file name just has and IMG_ prefix to the datetime string
            match = re.match(REGEX_FILE_NAME_DATE_IMG, name)
            if match:
                # IMG_/IMG- prefix - remove it
                new_name = name[4:]

            else:
                if path.suffix.lower() in EXTENSIONS_MOVIES:
                    # Need to use the file date/time
                    datetime = convert_from_stat_datetime(path.stat().st_ctime)

                else:
                    # Need to get EXIF data to rename
                    img = Image.open(str(path))
                    try:
                        exif_data = img.info["exif"]
                    except KeyError:
                        logging.warning(f"{prefix} {name} - FAILED to get EXIF data")
                        failed.append(name)
                        continue
                    exif_dict = piexif.load(exif_data, key_is_name=True)

                    date_string = exif_dict[EXIF][EXIF_DATE].decode('utf-8')
                    datetime = convert_from_exif_datetime(date_string)

                # Sort out new name for file using found datetime
                new_name = f"{convert_to_file_datetime(datetime)}-{name}"

            logging.info(f"{prefix} {name} - renaming to {new_name}")
            new_path = path.parent / new_name
            logging.debug(f"{str(path)} -> {str(new_path)}")

            if not args.dummy_run:
                path.rename(new_path)
        else:
            if args.fix_timestamps:
                date_string = match.group(1)
                datetime = convert_from_file_datetime(date_string)
                logging.info(f"{prefix} {name} - setting timestamps based on name")
                logging.debug(f"{str(path)} modified to {datetime}")
                if not args.dummy_run:
                    ts = datetime.timestamp()
                    # Will set access & modified times, but will update creation time too
                    # if those are before the creation time
                    os.utime(str(path), times=(ts, ts))
            else:
                logging.info(f"{prefix} {name} - skipping as correct name")
    if failed:
        logging.error(f"{len(failed)} errors - {failed}")

if __name__ == "__main__":
    sys.exit(main())

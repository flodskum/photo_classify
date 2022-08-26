# Photo Classify

Simple photo tagger - marking photos with rating a, b or nothing. The rating is just prefixed to the filename as "a_" or "b_".

Either renames files in the source directory, or copies them over to a destination.

## Set up

Install tk on your system, for MacOS:
    brew install python-tk

Requires the following packages:
    pip install pillow
    pip install pillow-heif
    pip install piexif

## Use

./photo-classify SOURCE [--destination DESTINATION]

A GUI (tkinter) window should appear if the source contains images (jpg or HEIC). Then simple controls to Skip Forward or Back, Copy without marking (if DESTINATION specified), or mark as a or b rating (copying over first if there is a destination).

./photo-fix.py [--dummy-run] [--fix-timestamps] [--verbose] path

By default this tries to set the image filenames to YYYYMMMDD_hhmmss-ORIGINAL_NAME. It can remove an IMG prefix off a name that matches this already. It uses Date of photo taken EXIF data to add the date if it is missing.

The option --fix-timestamps does the opposite, it uses the filename information to then set the time and date of the file. This is useful when the EXIF data is missing.


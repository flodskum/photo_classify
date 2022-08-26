#!/usr/bin/env python3
# Copyright (c) 2022 Jeremy Johnson
# SPDX-Identifier: MIT License
from __future__ import annotations

import logging
import sys
import shutil
import argparse

import tkinter as tk
from pathlib import Path
from PIL import ImageTk, Image
from pillow_heif import register_heif_opener
from photo_utils import get_file_list

# Allow loading of HEIC files
register_heif_opener()

logging.basicConfig(level=logging.INFO)
# BROKEN for some reason???
#logger = logging.getLogger("photo-classify")
#logger.setLevel(logging.DEBUG)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("source", type=Path, help="From directory")
    parser.add_argument("--destination", type=Path, help="Optional to directory")

    return parser.parse_args()

CANVAS_DIMS = 800

THUMBNAIL_DIMS = 100
THUMBNAILS = 5
THUMBNAILS_HALF = int((THUMBNAILS - 1) / 2)

MARK_A = "a"
MARK_B = "b"

class images_handler():
    _thumb_images = {}

    def __init__(self, src_path: Path, dest_path: Path, canvas, status, thumbnails):
        logging.info(f"Reading {src_path}")
        self.path = src_path
        self.dest = dest_path
        self.canvas = canvas
        self.status = status
        self.list_files = get_file_list(self.path)
        self.thumbnails = thumbnails
        self.img = None
        self.current_index = None

    def _get_current_file(self) -> Path:
        return self.list_files[self.current_index]["file"]

    def _set_current_file(self, file: Path) -> Path:
        self.list_files[self.current_index]["file"] = file

    def _get_current_status(self) -> str:
        return self.list_files[self.current_index]["status"]

    def _set_current_status(self, status: str) -> Path:
        self.list_files[self.current_index]["status"] = status

    def copy(self, marking=None):
        current_file = self._get_current_file()
        name = current_file.name
        if self.dest is None:
            if marking is None:
                # No copy and nothing to rename
                return
            action = "Renaming"
            status = "Renamed"
            dest = current_file.parent
        else:
            action = "Copying"
            status = "Copied"
            dest = self.dest
        self._show_status(name, f"{action} - please wait...")
        if marking is not None:
            new_name = f"{marking}_{name}"
            status = f"{status} as {marking}"
        else:
            new_name = name
        new_file = dest / new_name
        logging.info(f"{action} {current_file} to {new_file}")
        if action == "Copying":
            shutil.copy2(str(current_file), str(new_file))
        else:
            current_file.rename(new_file)
            # Fix up file list
            self._set_current_file(new_file)
            if name in images_handler._thumb_images:
                # Copy over image to new thumbnail entry
                images_handler._thumb_images[new_name] = images_handler._thumb_images[name]
        self._set_current_status(status)
        self.show_next()

    def show_prev(self):
        if self.current_index is not None:
            if self.current_index > 0:
                self.current_index -= 1
        else:
            return
        self._show_image(self._get_current_file())
        self._show_status(self._get_current_file().name, self._get_current_status())
        self._show_thumbnails()

    def show_next(self):
        if self.current_index is not None:
            if self.current_index < (len(self.list_files) - 1):
                self.current_index += 1
        else:
            self.current_index = 0
        self._show_image(self._get_current_file())
        self._show_status(self._get_current_file().name, self._get_current_status())
        self._show_thumbnails()

    def _get_image(self, path, max_dim):
        orig_i = Image.open(str(path))
        w, h = orig_i.size
        large_dim = max(w, h)
        factor = max_dim / large_dim
        new_w = int(w * factor)
        new_h = int(h * factor)
        logging.debug("dim:(%d, %d) max:%d factor:%d new dims:(%d, %d)", w,h,large_dim,factor,new_w,new_h)
        small_i = orig_i.resize((new_w, new_h))
        return ImageTk.PhotoImage(small_i, size=(new_w, new_h))

    def _show_image(self, path: Path):
        logging.info(f"Showing {path}")
        self.img = self._get_image(path, CANVAS_DIMS)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.img, anchor=tk.NW)

    def _show_thumbnails(self):
        start_idx = max(0, self.current_index - THUMBNAILS_HALF)
        if len(self.list_files) - start_idx < THUMBNAILS:
            start_idx = len(self.list_files) - THUMBNAILS
        end_idx = min(len(self.list_files), start_idx + THUMBNAILS)
        for num, idx in enumerate(range(start_idx, end_idx)):
            file = self.list_files[idx]["file"]
            name = file.name
            if name in images_handler._thumb_images:
                img = images_handler._thumb_images[name]
            else:
                logging.info(f"Creating thumbnail of {name}")
                img = self._get_image(file, THUMBNAIL_DIMS)
                images_handler._thumb_images[name] = img
            self.thumbnails[num]["canvas"].delete("all")
            self.thumbnails[num]["canvas"].create_image(0, 0, image=img, anchor=tk.NW)
            text = "<<<" if idx == self.current_index else "   "
            self.thumbnails[num]["select"].config(text=text)

    def _show_status(self, name, status):
        self.status.config(text=f"{name}\n{status}")


def main():
    args = parse_args()

    assert(args.source.is_dir())
    if args.destination is not None:
        assert(args.destination.is_dir())

    window = tk.Tk()
    window.title("Photo Classify")
    window.geometry("1000x800")
    canvas_frame = tk.Frame(window)
    canvas_frame.place(x=0, y=0, anchor=tk.NW, width=800, height=800)
    canvas = tk.Canvas(canvas_frame, width = CANVAS_DIMS, height = CANVAS_DIMS)
    canvas.pack()

    side_frame = tk.Frame(window)
    side_frame.place(x=801, y=0, anchor=tk.NW, width=200, height=800)
    side_frame.columnconfigure(0, weight=1)
    side_frame.grid_propagate(0)

    row = 0
    button_skip = tk.Button(side_frame, text="Skip Forward", command=lambda :images.show_next())
    button_skip.grid(column=0, row=row)
    row += 1
    button_back = tk.Button(side_frame, text="Skip Back", command=lambda :images.show_prev())
    button_back.grid(column=0, row=row)
    row += 1
    if args.destination is not None:
        button_copy = tk.Button(side_frame, text="Copy", command=lambda :images.copy())
        button_copy.grid(column=0, row=row)
        row += 1
    button_copy_a = tk.Button(side_frame, text="Mark A", command=lambda :images.copy(MARK_A))
    button_copy_a.grid(column=0, row=row)
    row += 1
    button_copy_b = tk.Button(side_frame, text="Mark B", command=lambda :images.copy(MARK_B))
    button_copy_b.grid(column=0, row=row)
    row += 1
    status = tk.Label(side_frame)
    status.grid(column=0, row=row) 
    row += 1
    thumbnail_frame = tk.Frame(side_frame)
    thumbnail_frame.grid(column=0, row=row)

    thumbnails = []
    for i in range(THUMBNAILS):
        thumbnail_canvas = tk.Canvas(thumbnail_frame, width=THUMBNAIL_DIMS, height=THUMBNAIL_DIMS)
        thumbnail_canvas.grid(column=0, row=i)
        thumbnail_select = tk.Label(thumbnail_frame, text="   ")
        thumbnail_select.grid(column=1, row=i)
        tdict = { "canvas": thumbnail_canvas, "select": thumbnail_select }
        thumbnails.append(tdict)

    images = images_handler(args.source, args.destination, canvas, status, thumbnails)

    images.show_next()
    window.mainloop()


if __name__ == "__main__":
    sys.exit(main())

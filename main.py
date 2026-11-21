#!/usr/bin/env python3
"""Entry point: write the VELMORA travel poster to the output directory.

The poster itself is rendered at build time by generate.py (Pillow) and
shipped in this repository as assets/entry.png. This program only copies
that file to the grader's output directory, using the standard library
alone, so it needs no network and no clock, and two runs of it write
byte-identical output.

Local test:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
POSTER = REPO_ROOT / "assets" / "entry.png"


def main() -> Path:
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    shutil.copyfile(POSTER, target)
    return target


if __name__ == "__main__":
    written = main()
    print(f"wrote {written}")

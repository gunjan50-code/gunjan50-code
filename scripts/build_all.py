#!/usr/bin/env python3
"""
Rebuild every generated asset in dependency order.

Skips the portrait if there's no prepped source image yet -- the portrait is the
one step that needs a photo and the optional heavy extras, so it shouldn't block
the rest of the build.

    python scripts/build_all.py
"""
import os
import subprocess
import sys

from config import ROOT

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args):
    print(f"\n$ python scripts/{script} {' '.join(args)}".rstrip())
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args])
    if r.returncode != 0:
        sys.exit(r.returncode)


if os.path.exists(os.path.join(ROOT, "source-prepped.png")):
    run("make_ascii_svg.py")
else:
    print("skipping portrait: no source-prepped.png "
          "(run: python scripts/prep_photo.py <your-photo.jpg>)")

run("make_wordmark_svg.py", "--mode", "rock")
run("fetch_contributions.py")
run("render_heatmap_svg.py")
run("build_readme.py")
print("\ndone.")

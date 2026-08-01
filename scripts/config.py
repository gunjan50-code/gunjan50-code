"""
Single source of truth for everything that is "you" in this repo.

Every generator script imports from here instead of hard-coding a username, so
changing profile.json is enough to re-skin the whole profile. Environment
variables still win, which is what lets the GitHub Action override the user
without editing files.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CONFIG_PATH = os.path.join(ROOT, "profile.json")

with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = json.load(f)

USERNAME = os.environ.get("GH_PROFILE_USER") or CONFIG["username"]
DISPLAY_NAME = CONFIG.get("display_name", USERNAME)
# the "who@github" bit in every terminal title bar
SHELL_USER = CONFIG.get("shell_user") or USERNAME.lower()
WORDMARK_TEXT = os.environ.get("WORDMARK_TEXT") or CONFIG.get("wordmark_text", "DEV")
ROLE_LINE = CONFIG.get("role_line", "")
LINKS = CONFIG.get("links", [])
# (left, top, right, bottom) as fractions of the source photo. The ASCII grid is
# only 100x53, so a full-body or loosely-cropped frame spends most of its
# resolution on clothing. Crop to head and upper shoulders.
PHOTO_CROP = CONFIG.get("photo_crop")
# clahe / smooth / stretch percentiles for prep_photo.py
PHOTO_TUNING = CONFIG.get("photo_tuning", {})

# ---- shared palette (all three SVGs use the same one so they read as a set) --
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"


def prompt(cmd):
    """Terminal-title-bar string, e.g. 'you@github: ~$ ./portrait.sh'."""
    return f"{SHELL_USER}@github: {cmd}"

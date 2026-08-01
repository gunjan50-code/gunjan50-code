"""
Prepare a portrait photo for clean ASCII conversion.

The pipeline, and why each step is there:

  1. remove the background (rembg) so the subject is isolated. Everything after
     this measures the subject only, which is the point.
  2. crop to head and upper shoulders. The ASCII grid is 100x53, so a wide shot
     spends most of its resolution on clothing.
  3. downscale to ~800px wide. Everything lands on that 100x53 grid eventually,
     and an edge-preserving filter over a 4000px frame takes minutes for no
     visible gain.
  4. CLAHE for local contrast, then a bilateral blur. The blur is what kills
     skin texture and stray hair, which otherwise survive the downsample as
     isolated dark characters and read as speckle.
  5. stretch the tonal range using percentiles of the SUBJECT's own histogram.
     This is the step that makes the portrait legible: it drives the face into
     the sparse end of the character ramp and the hair into the dense end. A
     photo that comes out uniformly mid-grey renders as noise, because every
     cell picks a similar glyph and the eye reads texture instead of shape.
  6. composite onto pure white, so the removed background maps to blank spaces.

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Run once whenever the source photo changes; the ascii SVG itself is static.

    python scripts/prep_photo.py <input.jpg> [output.png]

Tuning lives in profile.json under "photo_crop" and "photo_tuning".
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from config import ROOT, PHOTO_CROP, PHOTO_TUNING

args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = {a for a in sys.argv[1:] if a.startswith("--")}

INP = args[0] if args else os.path.join(ROOT, "source-photo.jpg")
OUT = args[1] if len(args) > 1 else os.path.join(ROOT, "source-prepped.png")

CLAHE_CLIP = PHOTO_TUNING.get("clahe", 1.6)
SMOOTH = PHOTO_TUNING.get("smooth", 30)
STRETCH_LO, STRETCH_HI = PHOTO_TUNING.get("stretch", [5, 90])
WORK_W = PHOTO_TUNING.get("work_width", 800)

try:
    import cv2
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False

try:
    from rembg import remove
    HAVE_REMBG = "--no-cutout" not in flags
except ImportError:
    HAVE_REMBG = False


# ---- 1. cut out the subject ------------------------------------------------
src = Image.open(INP).convert("RGBA")
if HAVE_REMBG:
    cut = remove(src)
else:
    print("rembg not installed -- keeping the original background. "
          "pip install -r scripts/requirements-photo.txt for a clean cutout",
          file=sys.stderr)
    cut = src

rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])          # 0 = background

# ---- 2. crop to the framing set in profile.json ----------------------------
if PHOTO_CROP:
    h, w = alpha.shape
    l, t, r, b = PHOTO_CROP
    x0, y0, x1, y1 = int(w * l), int(h * t), int(w * r), int(h * b)
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    print(f"photo_crop: ({x0}, {y0}, {x1}, {y1}) of {w}x{h}")

# ---- 3. downscale to working size -----------------------------------------
if rgb.shape[1] > WORK_W:
    size = (WORK_W, int(rgb.shape[0] * WORK_W / rgb.shape[1]))
    if HAVE_CV2:
        rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(alpha, size, interpolation=cv2.INTER_AREA)
    else:
        rgb = np.asarray(Image.fromarray(rgb).resize(size, Image.LANCZOS))
        alpha = np.asarray(Image.fromarray(alpha).resize(size, Image.LANCZOS))

# ---- 4. local contrast, then smooth away texture --------------------------
if HAVE_CV2:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if CLAHE_CLIP:
        gray = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(8, 8)).apply(gray)
    if SMOOTH:
        gray = cv2.bilateralFilter(gray, d=9, sigmaColor=SMOOTH, sigmaSpace=SMOOTH)
else:
    g = Image.fromarray(rgb).convert("L")
    g = ImageOps.autocontrast(g, cutoff=1)
    if SMOOTH:
        g = g.filter(ImageFilter.MedianFilter(size=3))
    gray = np.asarray(g, np.uint8)

# ---- 5. stretch the subject's own tonal range -----------------------------
subject = gray[alpha > 30]
if subject.size:
    p_lo, p_hi = np.percentile(subject, [STRETCH_LO, STRETCH_HI])
    gray = np.clip((gray.astype(np.float32) - p_lo) / max(p_hi - p_lo, 1.0) * 255.0,
                   0, 255).astype(np.uint8)
    print(f"tonal stretch: {p_lo:.0f}-{p_hi:.0f} -> 0-255 "
          f"(percentiles {STRETCH_LO}-{STRETCH_HI} of the subject)")

# ---- 6. composite onto white ----------------------------------------------
mask = alpha.astype(np.float32) / 255.0
if HAVE_CV2:
    mask = cv2.GaussianBlur(mask, (0, 0), 1.0)   # feathered to avoid a halo
else:
    mask = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255.0

if "--white-bg" in flags and not HAVE_REMBG:
    # crude stand-in for a cutout: anything already brighter than the subject
    # gets pushed to pure white. Works when you shot against a light wall.
    mask = np.where(gray > 205, 0.0, mask)

out = np.clip(gray.astype(np.float32) * mask + 255.0 * (1.0 - mask), 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape,
      f"(cutout={'rembg' if HAVE_REMBG else 'none'}, contrast={'clahe' if HAVE_CV2 else 'autocontrast'})")

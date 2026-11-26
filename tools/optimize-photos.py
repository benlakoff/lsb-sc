#!/usr/bin/env python3
"""Resize + compress listing photos in place and build grid thumbnails.

Usage: python3 tools/optimize-photos.py            (run from the repo root)

For every photos/*.jpg: applies EXIF rotation, converts to sRGB (so stripping
the iPhone Display P3 profile does not shift colours), strips metadata
(including GPS), caps the long edge at 2000px and writes a progressive JPEG.
Also writes photos/thumbs/<name>.jpg (long edge 900px) for the gallery grid
and photos/og.jpg (1200x630 crop of terrace.jpg, the lead photo) for link previews.
Safe to re-run: files already within the size cap are left untouched.
Requires Pillow.
"""
import io
import pathlib
from PIL import Image, ImageCms, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent / "photos"
FULL_EDGE, THUMB_EDGE = 2000, 900
SRGB = ImageCms.createProfile("sRGB")


def load(path):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src, SRGB, outputMode="RGB")
    return im.convert("RGB")


def save(im, path, edge, quality):
    im = im.copy()
    im.thumbnail((edge, edge), Image.LANCZOS)
    path.parent.mkdir(exist_ok=True)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size


for src in sorted(ROOT.glob("*.jpg")):
    if src.name == "og.jpg":
        continue
    with Image.open(src) as probe:
        small = max(probe.size) <= FULL_EDGE and not probe.info.get("icc_profile")
    thumb = ROOT / "thumbs" / src.name
    if small and thumb.exists():
        continue
    before = src.stat().st_size
    im = load(src)
    if not small:
        size = save(im, src, FULL_EDGE, 82)
    else:
        size = im.size
    save(im, thumb, THUMB_EDGE, 78)
    print(f"{src.name}: {before // 1024}KB -> {src.stat().st_size // 1024}KB {size}, thumb {thumb.stat().st_size // 1024}KB")

hero = load(ROOT / "terrace.jpg")
og = ImageOps.fit(hero, (1200, 630), Image.LANCZOS, centering=(0.5, 0.56))
og.save(ROOT / "og.jpg", "JPEG", quality=82, optimize=True, progressive=True)
print("og.jpg", (ROOT / "og.jpg").stat().st_size // 1024, "KB")

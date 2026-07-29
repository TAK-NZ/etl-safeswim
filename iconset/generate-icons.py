#!/usr/bin/env python3
"""
Generate the SafeSwim NZ TAK iconset icons from reference pin images.

Produces the compact (no pin tail / "stick") icon set used by the iconset,
written directly into source/Safeswim/. This mirrors the visual composition
used on the Safeswim website map (a coloured water-quality circle with an
optional lifeguard/hazard overlay badge).

For icons that combine a water-quality circle with a lifeguard flag, the
circle is horizontally centered on the flag's visual bounding box (rather
than the flag's pole position), so the flag sticks out evenly on both
sides of the circle. As a final step, every icon is padded to a square
canvas (ATAK expects square icons) by adding transparent space above and
below, keeping the artwork vertically centered.

Usage:
  pip install Pillow numpy
  python3 generate-icons.py

Requires rsvg-convert (librsvg2-bin) for SVG -> PNG rendering of the warning
diamond overlay.
"""

import os
import subprocess
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(SCRIPT_DIR, 'reference-icons')
OUT_DIR = os.path.join(SCRIPT_DIR, 'source', 'Safeswim')

PIN_WIDTH = 168  # base pin width in pixels (native reference pin size)

# ---------------------------------------------------------------------------
# SVG for warning diamond (no background box)
# ---------------------------------------------------------------------------
WARNING_SVG = '''\
<svg width="48" height="49" viewBox="0 0 48 49" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M21.9152 8.29496L7.79497 22.4152C6.64358 23.5666 6.64358 25.4334 7.79497 26.5848L21.9152 40.705C23.0666 41.8564 24.9334 41.8564 26.0848 40.705L40.205 26.5848C41.3564 25.4334 41.3564 23.5666 40.205 22.4152L26.0848 8.29496C24.9334 7.14358 23.0666 7.14358 21.9152 8.29496Z" fill="#FFF000"/>
<path d="M23.4019 11.4681L10.9666 23.9034C10.6371 24.2329 10.6371 24.767 10.9666 25.0965L23.4019 37.5318C23.7314 37.8612 24.2655 37.8612 24.595 37.5318L37.0303 25.0965C37.3598 24.767 37.3598 24.2329 37.0303 23.9034L24.595 11.4681C24.2655 11.1386 23.7314 11.1386 23.4019 11.4681Z" stroke="black" stroke-width="0.990344"/>
<path d="M24.1467 31.5154C25.0262 31.5154 25.7392 30.8024 25.7392 29.9229C25.7392 29.0433 25.0262 28.3303 24.1467 28.3303C23.2671 28.3303 22.5541 29.0433 22.5541 29.9229C22.5541 30.8024 23.2671 31.5154 24.1467 31.5154Z" fill="black"/>
<path d="M25.7042 17.7183C25.5917 17.5732 25.42 17.4874 25.2365 17.4844H22.7855C22.602 17.4785 22.4273 17.5673 22.3178 17.7183C22.2083 17.8633 22.155 18.0409 22.1609 18.2244L23.5226 26.9302C23.564 27.241 23.8304 27.4749 24.1442 27.4749C24.458 27.4749 24.7244 27.241 24.7658 26.9302L25.8137 18.2244C25.8552 18.0468 25.8137 17.8603 25.6983 17.7183H25.7042Z" fill="black"/>
</svg>'''

# ---------------------------------------------------------------------------
# Measurements from reference pins
# ---------------------------------------------------------------------------
# Base pin (168x260): circle at rows ~20-157, pole center at x=84
# SLS badge (84x130): flag rows 22-77 (height=56), pole at x=5-11 (center=8)
# Scale SLS so flag height (56) matches circle height (137): scale = 137/56

CIRCLE_TOP = 21
CIRCLE_BOTTOM = 157  # +2px extra to avoid cutting off the bottom
CIRCLE_HEIGHT = CIRCLE_BOTTOM - CIRCLE_TOP + 1  # 137
SLS_FLAG_TOP = 22  # first row of flag content in native SLS image
SLS_FLAG_BOTTOM = 77  # last row of flag content in native SLS image
SLS_FLAG_HEIGHT = SLS_FLAG_BOTTOM - SLS_FLAG_TOP + 1  # 56
SLS_SCALE = CIRCLE_HEIGHT / SLS_FLAG_HEIGHT  # flag height matches circle height

# Wide scratch canvas used while recentering the circle over the flag, before
# cropping to the tight content bounding box.
RECENTER_CANVAS_WIDTH = 600
RECENTER_FLAG_ANCHOR_X = 200

# Per-icon left edge of the "primary shape" (the water-quality circle for
# combined/quality icons, or the flag itself for patrol-only icons). Used to
# align the hazard warning diamond consistently, even though combined icons
# no longer have a fixed circle position.
icon_left_edge = {}


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, f))


def render_warning_diamond():
    """Render warning diamond SVG to PNG at pin width."""
    svg_path = '/tmp/sw-warning-nobg.svg'
    png_path = '/tmp/sw-warning-nobg.png'
    with open(svg_path, 'w') as f:
        f.write(WARNING_SVG)
    subprocess.run(
        ['rsvg-convert', '-w', str(PIN_WIDTH), '-h', str(PIN_WIDTH),
         svg_path, '-o', png_path],
        check=True, capture_output=True
    )
    return Image.open(png_path).convert('RGBA')


def bbox_x(img):
    """Return (x0, x1) of the visible (alpha > threshold) content."""
    arr = np.array(img)
    ys, xs = np.where(arr[:, :, 3] > 20)
    return int(xs.min()), int(xs.max())


def bbox(img):
    """Return (x0, x1, y0, y1) of the visible (alpha > threshold) content."""
    arr = np.array(img)
    ys, xs = np.where(arr[:, :, 3] > 20)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def build_combined_icon(base_file, overlay_file):
    """
    Composite a water-quality circle with a lifeguard/warning flag, with the
    circle horizontally centered on the flag's visual bounding box (so the
    flag sticks out evenly on both sides of the circle).

    Returns (image, circle_left_edge) where circle_left_edge is the x
    position of the circle's left edge in the returned (cropped) image,
    used later to align the hazard diamond.
    """
    base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
    circle = base.crop((0, CIRCLE_TOP, base.width, CIRCLE_BOTTOM + 1))
    circle_x0, circle_x1 = bbox_x(circle)
    circle_center = (circle_x0 + circle_x1) / 2

    overlay = Image.open(os.path.join(REF_DIR, overlay_file)).convert('RGBA')
    scaled_w = int(overlay.width * SLS_SCALE)
    scaled_h = int(overlay.height * SLS_SCALE)
    overlay_scaled = overlay.resize((scaled_w, scaled_h), Image.LANCZOS)
    scaled_flag_top = int(SLS_FLAG_TOP * SLS_SCALE)
    flag_window = overlay_scaled.crop((0, scaled_flag_top, scaled_w, scaled_flag_top + CIRCLE_HEIGHT))
    flag_x0, flag_x1 = bbox_x(flag_window)
    flag_center = (flag_x0 + flag_x1) / 2

    # Build on a wide scratch canvas: place the flag at a fixed anchor, then
    # place the circle so its bbox center aligns with the flag's bbox center.
    canvas = Image.new('RGBA', (RECENTER_CANVAS_WIDTH, CIRCLE_HEIGHT), (0, 0, 0, 0))
    canvas.paste(flag_window, (RECENTER_FLAG_ANCHOR_X, 0), flag_window)
    flag_center_canvas = RECENTER_FLAG_ANCHOR_X + flag_center
    circle_paste_x = int(round(flag_center_canvas - circle_center))
    canvas.paste(circle, (circle_paste_x, 0), circle)

    # Crop to the tight bounding box of the combined content.
    x0, x1 = bbox_x(canvas)
    result = canvas.crop((x0, 0, x1 + 1, CIRCLE_HEIGHT))

    circle_left_in_result = circle_paste_x + circle_x0 - x0
    return result, circle_left_in_result


def pad_to_square(img):
    """Pad the image with transparent space to make it square, keeping the
    artwork centered. ATAK expects square icons."""
    w, h = img.size
    if w == h:
        return img
    size = max(w, h)
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = (size - w) // 2
    y = (size - h) // 2
    canvas.paste(img, (x, y), img)
    return canvas


def generate_icons(warning_diamond):
    """Generate compact icons (no pin tail) into source/Safeswim/."""
    bases = {
        'Green': 'green_pin.png',
        'Red': 'red_pin.png',
        'Black': 'black_pin.png',
    }
    sls_overlays = {
        '.Lifeguarded': 'sls-default.png',
        '.LifeguardedOff': 'sls-offduty.png',
        '.Warning': 'sls-dangerous.png',
    }
    patrol_map = {
        'OnDuty': 'sls-default.png',
        'OffDuty': 'sls-offduty.png',
        'None': 'safety_only.png',
    }

    crop_top = CIRCLE_TOP
    crop_bottom = CIRCLE_BOTTOM + 1  # +1 because crop is exclusive on bottom
    circle_h = crop_bottom - crop_top

    # Warning diamond at 75% of circle height for overlay.
    warn_size = int(circle_h * 0.75)
    warn_small = warning_diamond.resize(
        (warn_size, int(warning_diamond.height * warn_size / warning_diamond.width)),
        Image.LANCZOS
    )

    # --- Combined mode: plain quality circle (no overlay) ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
        circle = base.crop((0, crop_top, base.width, crop_bottom))
        filename = f'SW.{quality}.png'
        circle.save(os.path.join(OUT_DIR, filename))
        icon_left_edge[filename] = bbox_x(circle)[0]

    # --- Combined mode: circle + lifeguard/warning flag, recentered ---
    for quality, base_file in bases.items():
        for suffix, overlay_file in sls_overlays.items():
            result, circle_left = build_combined_icon(base_file, overlay_file)
            filename = f'SW.{quality}{suffix}.png'
            result.save(os.path.join(OUT_DIR, filename))
            icon_left_edge[filename] = circle_left

    # --- Quality-only mode ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
        circle = base.crop((0, crop_top, base.width, crop_bottom))
        filename = f'SW.Quality.{quality}.png'
        circle.save(os.path.join(OUT_DIR, filename))
        icon_left_edge[filename] = bbox_x(circle)[0]

    # --- Patrol-only mode ---
    for patrol, src_file in patrol_map.items():
        img = Image.open(os.path.join(REF_DIR, src_file)).convert('RGBA')
        img_arr = np.array(img)

        if src_file == 'safety_only.png':
            # This is a circle+pole icon (like the quality pins) -- crop
            # circle, drop pole. Find the pole width (constant narrow strip
            # at bottom).
            pole_width = 0
            for row in range(img.height - 1, img.height - 20, -1):
                cols = [x for x in range(img.width) if img_arr[row, x, 3] > 50]
                if cols:
                    pole_width = max(pole_width, cols[-1] - cols[0] + 1)
            # Circle = rows wider than pole.
            circle_top_local = None
            circle_bottom_local = None
            for row in range(img.height):
                cols = [x for x in range(img.width) if img_arr[row, x, 3] > 50]
                width = (cols[-1] - cols[0] + 1) if cols else 0
                if width > pole_width + 2:
                    if circle_top_local is None:
                        circle_top_local = row
                    circle_bottom_local = row
            # Scale so circle matches target height, then crop.
            local_h = circle_bottom_local - circle_top_local + 1
            scale_factor = circle_h / local_h
            img_scaled = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)
            scaled_top = int(circle_top_local * scale_factor)
            scaled_bottom = scaled_top + circle_h
            cropped = img_scaled.crop((0, scaled_top, img_scaled.width, scaled_bottom))
        else:
            # Flag badges (sls-default, sls-offduty) -- use SLS scale and crop.
            img_scaled = img.resize((int(img.width * SLS_SCALE), int(img.height * SLS_SCALE)), Image.LANCZOS)
            scaled_flag_top = int(SLS_FLAG_TOP * SLS_SCALE)
            scaled_flag_bottom = int((SLS_FLAG_BOTTOM + 1) * SLS_SCALE)
            cropped = img_scaled.crop((0, scaled_flag_top, img_scaled.width, scaled_flag_bottom))

        filename = f'SW.Patrol.{patrol}.png'
        cropped.save(os.path.join(OUT_DIR, filename))
        icon_left_edge[filename] = bbox_x(cropped)[0]

    # --- Hazard variants: warning diamond overlaid, left+top aligned with
    #     each icon's own primary shape (circle or flag). ---
    base_icons = sorted([f for f in os.listdir(OUT_DIR) if f.endswith('.png')])
    for filename in base_icons:
        base = Image.open(os.path.join(OUT_DIR, filename)).convert('RGBA')
        result = base.copy()

        # Diamond's own leftmost visible column, at its widest row.
        warn_arr = np.array(warn_small)
        max_w = 0
        warn_left = 0
        for row in range(warn_small.height):
            cols = [x for x in range(warn_small.width) if warn_arr[row, x, 3] > 50]
            w = (cols[-1] - cols[0] + 1) if cols else 0
            if w > max_w:
                max_w = w
                warn_left = cols[0]

        paste_x = icon_left_edge[filename] - warn_left

        # Align diamond's top visible pixel with top of icon (y=0).
        warn_top_row = 0
        for row in range(warn_small.height):
            cols = [x for x in range(warn_small.width) if warn_arr[row, x, 3] > 50]
            if cols:
                warn_top_row = row
                break
        paste_y = -warn_top_row

        result.paste(warn_small, (paste_x, paste_y), warn_small)
        result.save(os.path.join(OUT_DIR, f'{filename.replace(".png", "")}.Hazard.png'))

    print(f"Generated icons: {len(os.listdir(OUT_DIR))}")


def squareify_all():
    """Final pass: pad every generated icon to a square canvas. ATAK expects
    square icons; this adds transparent space above/below (or left/right)
    while keeping the artwork centered."""
    for filename in os.listdir(OUT_DIR):
        path = os.path.join(OUT_DIR, filename)
        img = Image.open(path).convert('RGBA')
        squared = pad_to_square(img)
        squared.save(path)


def main():
    ensure_dirs()
    warning_diamond = render_warning_diamond()
    generate_icons(warning_diamond)
    squareify_all()
    print("\nDone.")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generate Safeswim icons for TAK.NZ from reference pin images.

Produces two sets:
  - icons/          Pin-shaped icons (with stick/teardrop tail)
  - icons-nostick/  Compact icons (circle only, no tail)

Usage:
  pip install Pillow numpy
  python3 generate-icons.py

Requires rsvg-convert for SVG→PNG rendering of the warning diamond.
"""

import os
import subprocess
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(SCRIPT_DIR, 'reference-icons')
OUT_DIR = os.path.join(SCRIPT_DIR, 'icons')
NOSTICK_DIR = os.path.join(SCRIPT_DIR, 'icons-nostick')

PIN_WIDTH = 168  # base pin width in pixels

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
# Scale SLS so flag height (56) matches circle height (94): scale = 94/56 = 1.678

CIRCLE_TOP = 21
CIRCLE_BOTTOM = 157  # +2px extra to avoid cutting off the bottom
CIRCLE_HEIGHT = CIRCLE_BOTTOM - CIRCLE_TOP + 1  # 137
SLS_FLAG_TOP = 22  # first row of flag content in native SLS image
SLS_FLAG_BOTTOM = 77  # last row of flag content in native SLS image
SLS_FLAG_HEIGHT = SLS_FLAG_BOTTOM - SLS_FLAG_TOP + 1  # 56
SLS_TOTAL_BOTTOM = 108  # last row of pole content in native SLS image
SLS_SCALE = CIRCLE_HEIGHT / SLS_FLAG_HEIGHT  # 137/56 = 2.446 — flag matches circle height
SLS_POLE_X = 8  # pole center in native SLS image


def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(NOSTICK_DIR, exist_ok=True)
    # Clear existing
    for d in [OUT_DIR, NOSTICK_DIR]:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))


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


def generate_pin_icons(warning_diamond):
    """Generate pin-shaped icons (with stick)."""
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

    # --- Combined mode: base pin + SLS flag behind ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')

        # Plain quality pin
        base.save(os.path.join(OUT_DIR, f'SW.{quality}.png'))

        for suffix, overlay_file in sls_overlays.items():
            overlay = Image.open(os.path.join(REF_DIR, overlay_file)).convert('RGBA')
            # Scale overlay so total visible height (flag+pole) matches circle height
            scaled_w = int(overlay.width * SLS_SCALE)
            scaled_h = int(overlay.height * SLS_SCALE)
            overlay_scaled = overlay.resize((scaled_w, scaled_h), Image.LANCZOS)

            # Align poles: shift SLS right so its pole aligns with pin center
            scaled_pole_x = int(SLS_POLE_X * SLS_SCALE)
            scaled_flag_top = int(SLS_FLAG_TOP * SLS_SCALE)
            x_offset = PIN_WIDTH // 2 - scaled_pole_x
            # Vertically: align SLS flag top with circle top (row CIRCLE_TOP on pin)
            y_offset = CIRCLE_TOP - scaled_flag_top

            canvas_width = max(base.width, x_offset + scaled_w)
            canvas_height = max(base.height, y_offset + scaled_h)
            canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
            canvas.paste(overlay_scaled, (x_offset, y_offset), overlay_scaled)
            canvas.paste(base, (0, 0), base)
            canvas.save(os.path.join(OUT_DIR, f'SW.{quality}{suffix}.png'))

    # --- Quality-only mode ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
        base.save(os.path.join(OUT_DIR, f'SW.Quality.{quality}.png'))

    # --- Patrol-only mode ---
    for patrol, src_file in patrol_map.items():
        img = Image.open(os.path.join(REF_DIR, src_file)).convert('RGBA')
        img_scaled = img.resize((int(img.width * SLS_SCALE), int(img.height * SLS_SCALE)), Image.LANCZOS)
        img_scaled.save(os.path.join(OUT_DIR, f'SW.Patrol.{patrol}.png'))

    # --- Hazard variants: warning diamond on top, pin below ---
    base_icons = sorted([f for f in os.listdir(OUT_DIR) if f.endswith('.png')])
    for filename in base_icons:
        base = Image.open(os.path.join(OUT_DIR, filename)).convert('RGBA')
        pin_center_x = PIN_WIDTH // 2
        circle_top = 42

        # Scale warning to pin width
        warn_scaled = warning_diamond.resize(
            (PIN_WIDTH, int(warning_diamond.height * PIN_WIDTH / warning_diamond.width)),
            Image.LANCZOS
        )
        warn_x = pin_center_x - (warn_scaled.width // 2)
        pin_y = warn_scaled.height - circle_top

        canvas_height = pin_y + base.height
        canvas_width = max(base.width, warn_x + warn_scaled.width)
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        canvas.paste(base, (0, pin_y), base)
        canvas.paste(warn_scaled, (warn_x, 0), warn_scaled)
        canvas.save(os.path.join(OUT_DIR, f'{filename.replace(".png", "")}.Hazard.png'))

    print(f"Pin icons: {len(os.listdir(OUT_DIR))}")


def generate_nostick_icons(warning_diamond):
    """Generate compact icons (no stick) with warning diamond overlaid top-left."""
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

    PAD = 0
    crop_top = CIRCLE_TOP
    crop_bottom = CIRCLE_BOTTOM + 1  # +1 because crop is exclusive on bottom
    circle_h = crop_bottom - crop_top

    # Warning diamond at 75% of circle height for overlay
    # Left edge of diamond aligns with left edge of circle
    # Top edge of diamond aligns with top edge of circle
    warn_size = int(circle_h * 0.75)
    warn_small = warning_diamond.resize(
        (warn_size, int(warning_diamond.height * warn_size / warning_diamond.width)),
        Image.LANCZOS
    )

    # Find left edge of circle content
    base_sample = Image.open(os.path.join(REF_DIR, 'green_pin.png')).convert('RGBA')
    base_arr = np.array(base_sample)
    # Find leftmost non-transparent pixel in the circle area
    circle_left = PIN_WIDTH
    for row in range(CIRCLE_TOP, CIRCLE_BOTTOM + 1):
        for x in range(PIN_WIDTH):
            if base_arr[row, x, 3] > 50:
                circle_left = min(circle_left, x)
                break

    # --- Combined mode (no stick) ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
        circle = base.crop((0, crop_top, base.width, crop_bottom))
        circle.save(os.path.join(NOSTICK_DIR, f'SW.{quality}.png'))

        for suffix, overlay_file in sls_overlays.items():
            overlay = Image.open(os.path.join(REF_DIR, overlay_file)).convert('RGBA')
            # Scale SLS so its total visible height matches circle height exactly
            scaled_w = int(overlay.width * SLS_SCALE)
            scaled_h = int(overlay.height * SLS_SCALE)
            overlay_scaled = overlay.resize((scaled_w, scaled_h), Image.LANCZOS)

            # The SLS visible content starts at SLS_FLAG_TOP (scaled) from the top of the image
            # We want that content to start at y=0 in our output (aligned with circle top)
            # And the pole center aligns with pin center horizontally
            scaled_pole_x = int(SLS_POLE_X * SLS_SCALE)
            scaled_flag_top = int(SLS_FLAG_TOP * SLS_SCALE)
            x_offset = PIN_WIDTH // 2 - scaled_pole_x
            y_offset = -scaled_flag_top  # shift up so visible content starts at y=0

            canvas_width = max(PIN_WIDTH, x_offset + scaled_w)
            canvas = Image.new('RGBA', (canvas_width, circle_h), (0, 0, 0, 0))

            # Place SLS behind (its visible content fills full height)
            canvas.paste(overlay_scaled, (x_offset, y_offset), overlay_scaled)
            # Place cropped circle on top
            circle = base.crop((0, crop_top, base.width, crop_bottom))
            canvas.paste(circle, (0, 0), circle)
            canvas.save(os.path.join(NOSTICK_DIR, f'SW.{quality}{suffix}.png'))

    # --- Quality-only (no stick) ---
    for quality, base_file in bases.items():
        base = Image.open(os.path.join(REF_DIR, base_file)).convert('RGBA')
        circle = base.crop((0, crop_top, base.width, crop_bottom))
        circle.save(os.path.join(NOSTICK_DIR, f'SW.Quality.{quality}.png'))

    # --- Patrol-only (no stick) ---
    for patrol, src_file in patrol_map.items():
        img = Image.open(os.path.join(REF_DIR, src_file)).convert('RGBA')
        img_arr = np.array(img)

        if src_file == 'safety_only.png':
            # This is a circle+pole icon (like the quality pins) — crop circle, drop pole
            # Find the pole width (constant narrow strip at bottom)
            pole_width = 0
            for row in range(img.height - 1, img.height - 20, -1):
                cols = [x for x in range(img.width) if img_arr[row, x, 3] > 50]
                if cols:
                    pole_width = max(pole_width, cols[-1] - cols[0] + 1)
            # Circle = rows wider than pole
            circle_top_local = None
            circle_bottom_local = None
            for row in range(img.height):
                cols = [x for x in range(img.width) if img_arr[row, x, 3] > 50]
                width = (cols[-1] - cols[0] + 1) if cols else 0
                if width > pole_width + 2:
                    if circle_top_local is None:
                        circle_top_local = row
                    circle_bottom_local = row
            # Scale so circle matches target height, then crop
            local_h = circle_bottom_local - circle_top_local + 1
            scale_factor = circle_h / local_h
            img_scaled = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)
            scaled_top = int(circle_top_local * scale_factor)
            scaled_bottom = scaled_top + circle_h
            cropped = img_scaled.crop((0, scaled_top, img_scaled.width, scaled_bottom))
        else:
            # Flag badges (sls-default, sls-offduty) — use SLS scale and crop
            img_scaled = img.resize((int(img.width * SLS_SCALE), int(img.height * SLS_SCALE)), Image.LANCZOS)
            scaled_flag_top = int(SLS_FLAG_TOP * SLS_SCALE)
            scaled_flag_bottom = int((SLS_FLAG_BOTTOM + 1) * SLS_SCALE)
            cropped = img_scaled.crop((0, scaled_flag_top, img_scaled.width, scaled_flag_bottom))

        cropped.save(os.path.join(NOSTICK_DIR, f'SW.Patrol.{patrol}.png'))

    # --- Hazard variants: warning diamond overlaid, left+top aligned with circle ---
    base_icons = sorted([f for f in os.listdir(NOSTICK_DIR) if f.endswith('.png')])
    for filename in base_icons:
        base = Image.open(os.path.join(NOSTICK_DIR, filename)).convert('RGBA')
        result = base.copy()
        # Align diamond's left vertex with circle's left edge
        warn_arr = np.array(warn_small)
        max_w = 0
        warn_left = 0
        for row in range(warn_small.height):
            cols = [x for x in range(warn_small.width) if warn_arr[row, x, 3] > 50]
            w = (cols[-1] - cols[0] + 1) if cols else 0
            if w > max_w:
                max_w = w
                warn_left = cols[0]
        paste_x = circle_left - warn_left
        # Align diamond's top visible pixel with top of icon (y=0)
        # Diamond has transparent padding at top — find first visible row
        warn_top_row = 0
        for row in range(warn_small.height):
            cols = [x for x in range(warn_small.width) if warn_arr[row, x, 3] > 50]
            if cols:
                warn_top_row = row
                break
        paste_y = -warn_top_row  # shift up so visible content starts at y=0
        result.paste(warn_small, (paste_x, paste_y), warn_small)
        result.save(os.path.join(NOSTICK_DIR, f'{filename.replace(".png", "")}.Hazard.png'))

    print(f"No-stick icons: {len(os.listdir(NOSTICK_DIR))}")


def main():
    ensure_dirs()
    warning_diamond = render_warning_diamond()
    generate_pin_icons(warning_diamond)
    generate_nostick_icons(warning_diamond)
    print("\nDone.")


if __name__ == '__main__':
    main()

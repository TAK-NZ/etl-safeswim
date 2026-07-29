# SafeSwim NZ TAK Iconset

A custom TAK iconset for [Safeswim](https://safeswim.org.nz) beach water
quality and lifeguard patrol status, used by the `etl-safeswim` ETL to
render composite status icons on TAK clients (ATAK, WinTAK, CloudTAK).

Each icon is a compact, non-square PNG combining a coloured water-quality
circle with an optional lifeguard/hazard overlay badge, matching the visual
language used on the Safeswim website map.

## Icons Included

36 icons across three display modes, organised in `source/Safeswim/`.

### Combined mode (water quality + patrol/safety, 24 icons)

| Icon | Filename | Description |
|------|----------|--------------|
| ![SW.Green](source/Safeswim/SW.Green.png) | `SW.Green.png` | Good water quality |
| ![SW.Green.Lifeguarded](source/Safeswim/SW.Green.Lifeguarded.png) | `SW.Green.Lifeguarded.png` | Good water quality, lifeguards on duty |
| ![SW.Green.LifeguardedOff](source/Safeswim/SW.Green.LifeguardedOff.png) | `SW.Green.LifeguardedOff.png` | Good water quality, lifeguards off duty |
| ![SW.Green.Warning](source/Safeswim/SW.Green.Warning.png) | `SW.Green.Warning.png` | Good water quality, safety warning |
| ![SW.Green.Hazard](source/Safeswim/SW.Green.Hazard.png) | `SW.Green.Hazard.png` | Good water quality, hazard flagged |
| ![SW.Green.Lifeguarded.Hazard](source/Safeswim/SW.Green.Lifeguarded.Hazard.png) | `SW.Green.Lifeguarded.Hazard.png` | Good water quality, lifeguards on duty, hazard flagged |
| ![SW.Green.LifeguardedOff.Hazard](source/Safeswim/SW.Green.LifeguardedOff.Hazard.png) | `SW.Green.LifeguardedOff.Hazard.png` | Good water quality, lifeguards off duty, hazard flagged |
| ![SW.Green.Warning.Hazard](source/Safeswim/SW.Green.Warning.Hazard.png) | `SW.Green.Warning.Hazard.png` | Good water quality, safety warning, hazard flagged |
| ![SW.Red](source/Safeswim/SW.Red.png) | `SW.Red.png` | Swimming not advised |
| ![SW.Red.Lifeguarded](source/Safeswim/SW.Red.Lifeguarded.png) | `SW.Red.Lifeguarded.png` | Swimming not advised, lifeguards on duty |
| ![SW.Red.LifeguardedOff](source/Safeswim/SW.Red.LifeguardedOff.png) | `SW.Red.LifeguardedOff.png` | Swimming not advised, lifeguards off duty |
| ![SW.Red.Warning](source/Safeswim/SW.Red.Warning.png) | `SW.Red.Warning.png` | Swimming not advised, safety warning |
| ![SW.Red.Hazard](source/Safeswim/SW.Red.Hazard.png) | `SW.Red.Hazard.png` | Swimming not advised, hazard flagged |
| ![SW.Red.Lifeguarded.Hazard](source/Safeswim/SW.Red.Lifeguarded.Hazard.png) | `SW.Red.Lifeguarded.Hazard.png` | Swimming not advised, lifeguards on duty, hazard flagged |
| ![SW.Red.LifeguardedOff.Hazard](source/Safeswim/SW.Red.LifeguardedOff.Hazard.png) | `SW.Red.LifeguardedOff.Hazard.png` | Swimming not advised, lifeguards off duty, hazard flagged |
| ![SW.Red.Warning.Hazard](source/Safeswim/SW.Red.Warning.Hazard.png) | `SW.Red.Warning.Hazard.png` | Swimming not advised, safety warning, hazard flagged |
| ![SW.Black](source/Safeswim/SW.Black.png) | `SW.Black.png` | Do not swim (wastewater overflow) |
| ![SW.Black.Lifeguarded](source/Safeswim/SW.Black.Lifeguarded.png) | `SW.Black.Lifeguarded.png` | Do not swim, lifeguards on duty |
| ![SW.Black.LifeguardedOff](source/Safeswim/SW.Black.LifeguardedOff.png) | `SW.Black.LifeguardedOff.png` | Do not swim, lifeguards off duty |
| ![SW.Black.Warning](source/Safeswim/SW.Black.Warning.png) | `SW.Black.Warning.png` | Do not swim, safety warning |
| ![SW.Black.Hazard](source/Safeswim/SW.Black.Hazard.png) | `SW.Black.Hazard.png` | Do not swim, hazard flagged |
| ![SW.Black.Lifeguarded.Hazard](source/Safeswim/SW.Black.Lifeguarded.Hazard.png) | `SW.Black.Lifeguarded.Hazard.png` | Do not swim, lifeguards on duty, hazard flagged |
| ![SW.Black.LifeguardedOff.Hazard](source/Safeswim/SW.Black.LifeguardedOff.Hazard.png) | `SW.Black.LifeguardedOff.Hazard.png` | Do not swim, lifeguards off duty, hazard flagged |
| ![SW.Black.Warning.Hazard](source/Safeswim/SW.Black.Warning.Hazard.png) | `SW.Black.Warning.Hazard.png` | Do not swim, safety warning, hazard flagged |

### Quality-only mode (plain circles, 6 icons)

| Icon | Filename | Description |
|------|----------|--------------|
| ![SW.Quality.Green](source/Safeswim/SW.Quality.Green.png) | `SW.Quality.Green.png` | Good water quality |
| ![SW.Quality.Red](source/Safeswim/SW.Quality.Red.png) | `SW.Quality.Red.png` | Swimming not advised |
| ![SW.Quality.Black](source/Safeswim/SW.Quality.Black.png) | `SW.Quality.Black.png` | Do not swim |
| ![SW.Quality.Green.Hazard](source/Safeswim/SW.Quality.Green.Hazard.png) | `SW.Quality.Green.Hazard.png` | Good water quality, hazard flagged |
| ![SW.Quality.Red.Hazard](source/Safeswim/SW.Quality.Red.Hazard.png) | `SW.Quality.Red.Hazard.png` | Swimming not advised, hazard flagged |
| ![SW.Quality.Black.Hazard](source/Safeswim/SW.Quality.Black.Hazard.png) | `SW.Quality.Black.Hazard.png` | Do not swim, hazard flagged |

### Patrol-only mode (lifeguard flag badges, 6 icons)

| Icon | Filename | Description |
|------|----------|--------------|
| ![SW.Patrol.OnDuty](source/Safeswim/SW.Patrol.OnDuty.png) | `SW.Patrol.OnDuty.png` | Lifeguards on duty |
| ![SW.Patrol.OffDuty](source/Safeswim/SW.Patrol.OffDuty.png) | `SW.Patrol.OffDuty.png` | Lifeguards off duty |
| ![SW.Patrol.None](source/Safeswim/SW.Patrol.None.png) | `SW.Patrol.None.png` | Not lifeguarded |
| ![SW.Patrol.OnDuty.Hazard](source/Safeswim/SW.Patrol.OnDuty.Hazard.png) | `SW.Patrol.OnDuty.Hazard.png` | Lifeguards on duty, hazard flagged |
| ![SW.Patrol.OffDuty.Hazard](source/Safeswim/SW.Patrol.OffDuty.Hazard.png) | `SW.Patrol.OffDuty.Hazard.png` | Lifeguards off duty, hazard flagged |
| ![SW.Patrol.None.Hazard](source/Safeswim/SW.Patrol.None.Hazard.png) | `SW.Patrol.None.Hazard.png` | Not lifeguarded, hazard flagged |

### Overview

![Icons overview](Overview/icons-overview.png)

## Reference Icons

The `reference-icons/` folder contains the original pin PNGs downloaded from
the Safeswim website (`https://safeswim.org.nz/images/pins/`). These are the
source images `generate-icons.py` composites to produce the icons in
`source/Safeswim/`.

![Reference icons overview](Overview/reference-icons-overview.png)

| Reference file | Safeswim meaning | Used for |
|---------------|------------------|----------|
| `green_pin.png` | Good water quality | Base for `SW.Green.*` |
| `red_pin.png` | Swimming not advised | Base for `SW.Red.*` |
| `black_pin.png` | Do not swim (overflow) | Base for `SW.Black.*` |
| `sls-default.png` | Lifeguards on duty | Overlay for `*.Lifeguarded` / `SW.Patrol.OnDuty` |
| `sls-offduty.png` | Lifeguards off duty | Overlay for `*.LifeguardedOff` / `SW.Patrol.OffDuty` |
| `sls-dangerous.png` | Dangerous conditions | Overlay for `*.Warning` |
| `hazard_pin.png` | Safety hazard warning | Reference (full pin) |
| `unavailable.png` | Data not available | Not used |
| `long-term-red.png` | Consistently poor quality | Not used |
| `safety_only.png` | Water safety info only | Standalone for `SW.Patrol.None` |
| `information.png` | Information note | Not used |

## Regenerating the Icons

If the icons need to be regenerated (e.g. after Safeswim updates their pin
designs):

```bash
pip install Pillow numpy
python3 generate-icons.py  # composites reference-icons/ -> source/Safeswim/
```

Requires `rsvg-convert` (from `librsvg2-bin`) to render the warning diamond
overlay.

## Building the TAK Data Package

```bash
./scripts/create_TAKDataPackage.sh
```

This generates `SafeSwimNZ-Package.zip`, which can be distributed to ATAK
devices via device profiles or imported manually into ATAK/CloudTAK as an
iconset.

## Installation

1. Download the latest release package (or build it as above).
2. Import the `.zip` file into your TAK application.
3. The SafeSwim NZ icons will be available in the iconset selection.

## Usage in TAK

Once installed, reference these icons using the format
`{iconset-uid}:Safeswim/{filename}`:

```
c2ec216e-9bfc-461d-b77a-e2099ffa9fa7:Safeswim/SW.Green.Lifeguarded.png
```

See [`../SPEC.md`](../SPEC.md) for the full icon selection logic used by the
`etl-safeswim` ETL.

## Structure

- `source/` - Contains `iconset.xml` and the generated icon PNGs (`Safeswim/`)
- `reference-icons/` - Original Safeswim pin/badge PNGs used to generate the icon set
- `generate-icons.py` - Script that composites `reference-icons/` into `source/Safeswim/`
- `datapackage/` - TAK mission package structure
- `scripts/` - Build automation scripts
- `Overview/` - Preview spritesheets of the generated icons and reference icons

## License

AGPL-3.0-only. See [`LICENSE`](LICENSE).

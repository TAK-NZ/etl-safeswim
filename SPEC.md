# ETL-Safeswim — Implementation Specification

An ETL to ingest beach water quality and patrol status data from Safeswim
(safeswim.org.nz) into TAK.NZ as CoT point features.

---

## Data Source

**Endpoint:** `https://safeswim.org.nz/api/locations`

**Method:** GET (no authentication required)

**Response format:** Custom JSON (NOT GeoJSON)

```json
{
  "locations": [
    {
      "name": "Kawakawa Bay",
      "alternative_name": null,
      "slug": "kawakawa-bay",
      "position": [-36.883, 175.063],
      "patrolled": true,
      "state": {
        "quality": "GREEN",
        "patrol": "OFF_DUTY"
      }
    },
    {
      "name": "Tauranga Bay Estuary",
      "alternative_name": null,
      "slug": "tauranga-bay-estuary",
      "position": [-35.004112, 173.787586],
      "patrolled": false,
      "state": {
        "quality": "RED+"
      }
    }
  ]
}
```

### Important notes about the source data

1. **Coordinate order is `[lat, lng]`** — NOT GeoJSON order. Must be swapped
   to `[lng, lat]` when creating GeoJSON/CoT features.
2. **`position` is always a 2-element array** — `[latitude, longitude]`
3. **`state.quality`** — present on all locations. Values: `GREEN`, `RED`,
   `RED+`, `BLACK`
4. **`state.patrol`** — only present when `patrolled: true`. Values:
   `ON_DUTY`, `OFF_DUTY`
5. **`state.safety`** — only present when a safety hazard exists. Values:
   `WARNING`, `WARNING+`. Most locations do not have this field.
6. **`alternative_name`** — nullable. When present, use as secondary label.
7. **~400+ locations nationwide** — from Cape Reinga to Invercargill.
8. **Data updates every 15 minutes** — per Auckland Council documentation.

### Quality states

| Value | Meaning | Safeswim pin colour |
|-------|---------|---------------------|
| `GREEN` | Good water quality (low risk) | Green |
| `RED` | Swimming not advised (high risk) | Red |
| `RED+` | Swimming not advised (overflow indicator) | Red |
| `BLACK` | Do not swim (wastewater overflow) | Black |

### Safety states

| Value | Meaning |
|-------|---------|
| `WARNING` | Safety hazard present (e.g. coastal hazard, construction) |
| `WARNING+` | Elevated safety hazard |
| *(absent)* | No safety concern |

When `state.safety` is present, the location has an active safety warning
regardless of water quality. This should override the icon/colour to indicate
hazard — use the NZTA-style hazard icon `NZTransportAgency/NZTA.area-warnings.png`
or `Incidents/INC.60.GHS08.HealthHazard.png` with an orange/amber marker-color.

### Patrol states

| Value | Meaning |
|-------|---------|
| `ON_DUTY` | Lifeguards actively patrolling |
| `OFF_DUTY` | Lifeguard-capable beach, but no patrol currently |
| *(absent)* | Beach is not lifeguarded (patrolled: false) |

---

## ETL Configuration

### Environment variables (admin-configurable via CloudTAK UI)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `Show All` | Boolean | `false` | When `false`, only show non-GREEN locations (and any with safety warnings). When `true`, show all ~400 locations including GREEN. |
| `Display Mode` | String | `combined` | Icon display mode: `combined` (water quality + patrol/safety as composite icon), `quality` (water quality colour only), or `patrol` (lifeguard status only). |

### Scheduling

- **Invocation type:** Schedule
- **Recommended interval:** 15 minutes (matches Safeswim's update frequency)
- **Stale time:** 20 minutes

---

## Feature Output

Each location becomes a single Point feature.

### Feature ID

```
safeswim-{slug}
```

Example: `safeswim-kawakawa-bay`

### CoT Type

```
a-o-X-i-e-h
```

(Atoms → Other → Incident → Environmental → Health)

### Callsign

```
{name}: {quality_label}
```

Examples:
- `Kawakawa Bay: Good`
- `Tauranga Bay Estuary: Do Not Swim`

Quality label mapping:
| State | Label |
|-------|-------|
| `GREEN` | `Good` |
| `RED` | `Not Advised` |
| `RED+` | `Not Advised (Overflow)` |
| `BLACK` | `Do Not Swim` |

### Remarks

```
Water Quality: {quality_label}
Patrol: {patrol_label}
Location: {name}{alternative_name_suffix}
More info: https://safeswim.org.nz/locations/{slug}
```

Where `patrol_label` is:
| Condition | Label |
|-----------|-------|
| `patrolled: false` | `Not lifeguarded` |
| `patrol: ON_DUTY` | `Lifeguards on duty` |
| `patrol: OFF_DUTY` | `Lifeguards off duty` |

And `alternative_name_suffix` is ` (aka {alternative_name})` when present, or
empty string when null.

### Metadata

```json
{
  "quality": "GREEN",
  "patrol": "OFF_DUTY",
  "safety": "WARNING",
  "patrolled": true,
  "slug": "kawakawa-bay",
  "name": "Kawakawa Bay",
  "alternative_name": null
}
```

All raw fields from the API are preserved in metadata for downstream consumers
(display-proxy filters, highlight templates). The `safety` field is only included
when present in the source data.

### Icon selection

The ETL uses pre-rendered composite icons that combine water quality (base
circle colour) with patrol/safety status (overlay badge) — matching the visual
language used on the Safeswim website itself. No `marker-color` tinting is
needed; the colour is baked into each icon.

#### Composite icon set (to be added to `iconset-nzem-symbology/source/Safeswim/`)

All icons are 128×128 PNGs with transparent background. Each icon is a coloured
circle (representing water quality) with an optional overlay badge (representing
patrol or safety status).

**Base circle colours:**

| Quality | Circle colour | Hex |
|---------|--------------|-----|
| GREEN | Green | `#00c853` |
| RED / RED+ | Red | `#ff1744` |
| BLACK | Black | `#212121` |

**Overlay badges:**

| Overlay | Badge |
|---------|-------|
| None | Plain circle only |
| Lifeguarded (on duty) | Red+yellow flag (active) |
| Lifeguarded (off duty) | Red+yellow flag (greyed/faded) |
| Safety warning | Orange/amber hazard triangle |

#### Full icon matrix (18 icons total across 3 modes)

**Combined mode icons (12):**

| Filename | Quality | Overlay |
|----------|---------|---------|
| `SW.Green.png` | GREEN | None |
| `SW.Green.Lifeguarded.png` | GREEN | Lifeguards on duty |
| `SW.Green.LifeguardedOff.png` | GREEN | Lifeguards off duty |
| `SW.Green.Warning.png` | GREEN | Safety warning |
| `SW.Red.png` | RED/RED+ | None |
| `SW.Red.Lifeguarded.png` | RED/RED+ | Lifeguards on duty |
| `SW.Red.LifeguardedOff.png` | RED/RED+ | Lifeguards off duty |
| `SW.Red.Warning.png` | RED/RED+ | Safety warning |
| `SW.Black.png` | BLACK | None |
| `SW.Black.Lifeguarded.png` | BLACK | Lifeguards on duty |
| `SW.Black.LifeguardedOff.png` | BLACK | Lifeguards off duty |
| `SW.Black.Warning.png` | BLACK | Safety warning |

**Quality-only mode icons (3):**

Simple coloured circles, no overlay badge.

| Filename | Meaning |
|----------|---------|
| `SW.Quality.Green.png` | Good water quality |
| `SW.Quality.Red.png` | Swimming not advised |
| `SW.Quality.Black.png` | Do not swim |

**Patrol-only mode icons (3):**

Flag/badge icons indicating lifeguard status.

| Filename | Meaning |
|----------|---------|
| `SW.Patrol.OnDuty.png` | Lifeguards on duty (active flag) |
| `SW.Patrol.OffDuty.png` | Lifeguards off duty (faded flag) |
| `SW.Patrol.None.png` | Not lifeguarded (no flag) |

#### Icon selection logic in the ETL

```typescript
function getIcon(
    mode: string,
    quality: string,
    patrolled: boolean,
    patrol?: string,
    safety?: string
): string {
    const PREFIX = 'bb4df0a6-ca8d-4ba8-bb9e-3deb97ff015e:Safeswim/';

    // --- Quality-only mode ---
    if (mode === 'quality') {
        if (quality === 'BLACK') return PREFIX + 'SW.Quality.Black.png';
        if (quality === 'RED' || quality === 'RED+') return PREFIX + 'SW.Quality.Red.png';
        return PREFIX + 'SW.Quality.Green.png';
    }

    // --- Patrol-only mode ---
    if (mode === 'patrol') {
        if (patrolled && patrol === 'ON_DUTY') return PREFIX + 'SW.Patrol.OnDuty.png';
        if (patrolled) return PREFIX + 'SW.Patrol.OffDuty.png';
        return PREFIX + 'SW.Patrol.None.png';
    }

    // --- Combined mode (default) ---
    let base: string;
    if (quality === 'BLACK') base = 'Black';
    else if (quality === 'RED' || quality === 'RED+') base = 'Red';
    else base = 'Green';

    let suffix = '';
    if (safety === 'WARNING' || safety === 'WARNING+') {
        suffix = '.Warning';
    } else if (patrolled && patrol === 'ON_DUTY') {
        suffix = '.Lifeguarded';
    } else if (patrolled) {
        suffix = '.LifeguardedOff';
    }

    return PREFIX + `SW.${base}${suffix}.png`;
}
```

#### Priority when safety + patrol both present

Safety warnings take priority over patrol status for the overlay badge.
A location with `quality: GREEN`, `patrol: ON_DUTY`, and `safety: WARNING`
gets `SW.Green.Warning.png` — not the lifeguard flag.

#### Iconset UUID and paths

Iconset UUID (same NZEM iconset, extended with Safeswim folder):
```
bb4df0a6-ca8d-4ba8-bb9e-3deb97ff015e
```

Icon path format in CloudTAK:
```
bb4df0a6-ca8d-4ba8-bb9e-3deb97ff015e:Safeswim/SW.Green.Lifeguarded.png
```

#### Fallback (before custom icons are created)

Until the Safeswim icons are designed and added to the iconset, use these
existing NZEM icons as temporary placeholders:

| State | Fallback icon | marker-color |
|-------|---------------|-------------|
| GREEN | `Operations/OP.40.Marine.png` | `#00c853` |
| RED/RED+ | `Incidents/INC.60.GHS08.HealthHazard.png` | `#ff1744` |
| BLACK | `Incidents/INC.60.GHS08.HealthHazard.png` | `#212121` |
| WARNING/WARNING+ | `NZTransportAgency/NZTA.area-warnings.png` | `#ff6d00` |

When using fallback icons, `marker-color` IS needed for tinting (since the
fallback icons are white-on-transparent). Once the composite Safeswim icons
are available, remove `marker-color` as the colour is baked in.

---

## Icon Generation

### Generated icons

The `icons/` folder contains all 18 pre-generated composite PNG icons, created
by compositing Safeswim's base quality pins with lifeguard/warning overlay
badges — matching the same visual style used on the Safeswim website map.

Icons are **not square** — they use the pin/badge aspect ratio (168×260 for
combined/quality mode, 84×130 for patrol-only mode). TAK handles non-square
icons correctly, scaling them while preserving aspect ratio.

### Reference images

The `reference-icons/` folder contains all 11 original pin PNGs downloaded from
the Safeswim website (`https://safeswim.org.nz/images/pins/`). These are the
source images used to generate the composite icons.

| Reference file | Safeswim meaning | Used for |
|---------------|------------------|----------|
| `green_pin.png` | Good water quality | Base for `SW.Green.*` |
| `red_pin.png` | Swimming not advised | Base for `SW.Red.*` |
| `black_pin.png` | Do not swim (overflow) | Base for `SW.Black.*` |
| `sls-default.png` | Lifeguards on duty | Overlay for `*.Lifeguarded` |
| `sls-offduty.png` | Lifeguards off duty | Overlay for `*.LifeguardedOff` |
| `sls-dangerous.png` | Dangerous conditions | Overlay for `*.Warning` |
| `hazard_pin.png` | Safety hazard warning | Reference (full pin) |
| `unavailable.png` | Data not available | Not used |
| `long-term-red.png` | Consistently poor quality | Not used |
| `safety_only.png` | Water safety info only | Standalone for `SW.Patrol.None` |
| `information.png` | Information note | Not used |

### Compositing approach

Combined mode icons are generated by overlaying the SLS badge (84×130) on the
top-right corner of the base quality pin (168×260). The badge overlaps the
circle area of the pin, matching the Safeswim website's visual composition.

Quality-only icons are the unmodified base pins.
Patrol-only icons are the standalone SLS badge images.

### Regeneration

If the icons need to be regenerated (e.g. after Safeswim updates their pin
designs), the generation script uses Python Pillow:

```bash
pip install Pillow
python3 generate-icons.py  # composites reference-icons/ → icons/
```

### Links

Each feature should include a link to the Safeswim detail page:

```json
"links": [{
  "uid": "safeswim-{slug}",
  "relation": "r-u",
  "mime": "text/html",
  "url": "https://safeswim.org.nz/locations/{slug}",
  "remarks": "Safeswim Details"
}]
```

---

## Iconset UUID

The NZEM iconset UUID used in CloudTAK icon paths:
```
bb4df0a6-ca8d-4ba8-bb9e-3deb97ff015e
```

---

## Repository Structure

Follow the same structure as all other TAK-NZ ETLs (`etl-avalanche`,
`etl-floodhub`, etc.):

```
etl-safeswim/
├── task.ts              # ETL handler — fetch, transform, submit
├── package.json
├── tsconfig.json
├── eslint.config.js
├── Dockerfile
├── LICENSE              # AGPL-3.0-only
├── README.md
├── CHANGELOG.md
└── SPEC.md              # This file
```

### package.json

```json
{
  "name": "etl-safeswim",
  "type": "module",
  "version": "1.0.0",
  "description": "ETL to bring beach water quality data from Safeswim into TAK",
  "main": "index.js",
  "scripts": {
    "lint": "eslint *.ts",
    "build": "tsc --build",
    "test": "exit 0"
  },
  "author": "Christian Elsen <chris@elsen.nz>",
  "license": "AGPL-3.0-only",
  "devDependencies": {
    "@eslint/js": "^10.0.1",
    "@types/geojson": "^7946.0.16",
    "eslint": "^10.6.0",
    "ts-node": "^10.9.2",
    "typescript": "^6.0.3",
    "typescript-eslint": "^8.62.1"
  },
  "dependencies": {
    "@sinclair/typebox": "^0.34.49",
    "@tak-ps/etl": "^10.8.0"
  },
  "overrides": {
    "fast-xml-parser": "5.9.3"
  }
}
```

### Dockerfile

```dockerfile
FROM node:24-alpine

WORKDIR /home/etl

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

CMD ["node", "dist/task.js"]
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2022"],
    "types": ["node"],
    "outDir": "./dist",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["*.ts"],
  "exclude": ["node_modules", "dist"]
}
```

---

## task.ts — Implementation Guide

### Class structure

```typescript
import { Type, TSchema } from '@sinclair/typebox';
import { fetch } from '@tak-ps/etl';
import ETL, {
  Event, SchemaType, handler as internal, local,
  InvocationType, DataFlowType
} from '@tak-ps/etl';

const Environment = Type.Object({
  'Show All': Type.Boolean({
    default: false,
    description: 'Show all locations including GREEN quality. When false, only non-GREEN locations and those with safety warnings are shown.'
  }),
  'Display Mode': Type.String({
    default: 'combined',
    description: 'Icon display mode: "combined" (water quality + patrol/safety composite), "quality" (water quality only), or "patrol" (lifeguard status only)'
  })
});

export default class Task extends ETL {
  static name = 'etl-safeswim';
  static flow = [DataFlowType.Incoming];
  static invocation = [InvocationType.Schedule];

  // ... schema(), control()
}
```

### control() logic

1. Read environment config
2. Fetch `https://safeswim.org.nz/api/locations`
3. Parse response as JSON
4. Iterate `data.locations`
5. For each location:
   - Skip if `Show All` is false AND quality is `GREEN` AND no safety warning
   - Swap coordinates: `[lat, lng]` → GeoJSON `[lng, lat]`
   - Determine icon and marker-color based on quality/safety state
   - Build feature with id, callsign, remarks, metadata, links
6. Submit FeatureCollection

### Coordinate swap

The API returns `position: [lat, lng]`. GeoJSON/CoT requires `[lng, lat]`:

```typescript
const [lat, lng] = location.position;
// GeoJSON geometry:
geometry: {
  type: 'Point',
  coordinates: [lng, lat]
}
```

### Stale time

Set stale to 20 minutes from now:
```typescript
stale: new Date(Date.now() + 20 * 60 * 1000).toISOString()
```

---

## Reference: Existing ETL patterns

Look at `etl-avalanche/task.ts` and `etl-geonet-quakes/task.ts` for the
standard patterns:

- `async schema()` — returns Environment for Input, output schema for Output
- `async control()` — main logic, calls `this.env(Environment)` then
  `this.submit(fc)`
- Bottom of file: `await local(new Task(import.meta.url), import.meta.url);`
  and `export async function handler(event) { ... }`

---

## Testing

After implementation, test locally:

```bash
npm install
npm run build
npx ts-node --esm task.ts
```

This will invoke the ETL in local mode and print the submitted FeatureCollection.
Verify:
- Correct number of features (all ~400 when Show All = true, only non-GREEN
  otherwise)
- Coordinates are in `[lng, lat]` order (longitude first)
- Icons and marker-colors are set correctly
- Metadata contains all expected fields
- Stale time is ~20 minutes in the future

# ETL-Safeswim

<p align='center'>Beach water quality and lifeguard patrol status from Safeswim for TAK</p>

## Data Source

[Safeswim](https://safeswim.org.nz) (public, no authentication):

- `https://safeswim.org.nz/api/locations` — bulk list of all locations with current state (used every run)
- `https://safeswim.org.nz/api/locations/{slug}` — per-location detail, including the full text of any
  active safety alert (used only for locations with an active safety warning, per run)

~300+ swimming locations nationwide (Cape Reinga to Invercargill), covering water quality, lifeguard
patrol status, and active safety hazards. Safeswim updates the underlying data roughly every 15 minutes.

### Data notes

- The API returns coordinates as `[lat, lng]`; the ETL swaps these to GeoJSON's `[lng, lat]` order.
- `state.quality` (`GREEN`, `RED`, `RED+`, `BLACK`) is **not present on every location** — roughly a
  quarter of locations (mostly surf-lifesaving patrolled beaches without council water-quality testing)
  only report `patrol` and/or `safety`. These locations are always shown (regardless of `Show All`) using
  a patrol-status icon rather than being misrepresented as good water quality.
- `state.patrol` (`ON_DUTY`, `OFF_DUTY`) is only present when `patrolled: true`.
- `state.safety` (`WARNING`, `WARNING+`) is only present when an active safety hazard exists. In combined
  icon mode this adds a hazard-diamond overlay on top of whatever patrol-status badge already applies
  (they're independent, combinable overlays — e.g. a lifeguarded beach with a hazard shows both the
  lifeguard flag and the hazard diamond). The bulk list endpoint only reports this enum, not the actual
  alert text — the ETL fetches the per-location detail endpoint for these locations to get the real alert
  `title`/`description` (e.g. "Shellfish warning" with the full explanation), falling back to a generic
  label if the detail request fails or returns no alerts.

## Configuration

| Setting | Default | Description |
|---|---|---|
| `Show All` | `false` | When `false`, only non-GREEN locations and those with a safety warning (or no quality rating) are shown. When `true`, all ~300+ locations are shown. |
| `Display Mode` | `combined` | Icon display mode: `combined` (water quality + patrol/safety composite), `quality` (water quality colour only), or `patrol` (lifeguard status only). |

## CoT Mapping

| Field | Value |
|---|---|
| CoT type | `a-o-X-i-e-h` (Other, Incident, Environmental, Health) |
| CoT UID | `safeswim-{slug}` |
| Callsign | `{name}: {quality label}` |
| Icon | Composite SafeSwim NZ iconset icon (see below) — colour baked in, no `marker-color` needed |
| Stale | 20 minutes from ETL run time |

### Remarks format

```
Water Quality: Good
Patrol: Lifeguards off duty
Location: Kawakawa Bay
More info: https://safeswim.org.nz/locations/kawakawa-bay
```

One or more `Safety: {alert title}` lines (each followed by the alert's full description) are inserted
between `Patrol` and `Location` when the location has an active safety hazard (`state.safety` is
`WARNING` or `WARNING+`), e.g.:

```
Water Quality: Good
Patrol: Not lifeguarded
Safety: Shellfish warning
Avoid collecting shellfish in this area due to a recent discharge from the Māngere Wastewater Treatment
Plant that did not meet UV treatment standards. Shellfish samples are being analysed and results will be
used to identify when the risk has passed.
Location: Oruarangi Creek
More info: https://safeswim.org.nz/locations/oruarangi-creek
```

If the detail endpoint has no alerts, or the request fails, this falls back to a generic
`Safety: Safety hazard present` / `Safety: Elevated safety hazard` line based on `state.safety`.

### Metadata

All raw fields from the API are preserved under `metadata` (`quality`, `patrol`, `safety`, `patrolled`,
`slug`, `name`, `alternative_name`) for downstream consumers such as display-proxy filters and highlight
templates. When an active safety alert has full text available, it's also included as `metadata.alerts`
(array of `{ title, description, from, to }`).

## Icons

Icons come from the custom **SafeSwim NZ** iconset in [`iconset/`](iconset/), built from Safeswim's own
website pin artwork. See [`iconset/README.md`](iconset/README.md) for the full icon set and
[`SPEC.md`](SPEC.md) for the icon selection logic.

Iconset UID: `c2ec216e-9bfc-461d-b77a-e2099ffa9fa7`

## Deployment

Deployment into the CloudTAK environment for ETL tasks is done via automatic releases to the TAK.NZ AWS environment.

Github actions will build and push docker releases on every version tag which can then be automatically configured via the
CloudTAK API.

### GitHub Actions Setup

The workflow uses GitHub variables and secrets to make it reusable across different ETL repositories.

#### Organization Variables (recommended)
- `DEMO_STACK_NAME`: Name of the demo stack (default: "Demo")
- `PROD_STACK_NAME`: Name of the production stack (default: "Prod")

#### Organization Secrets (recommended)
- `DEMO_AWS_ACCOUNT_ID`: AWS account ID for demo environment
- `DEMO_AWS_REGION`: AWS region for demo environment
- `DEMO_AWS_ROLE_ARN`: IAM role ARN for demo environment
- `PROD_AWS_ACCOUNT_ID`: AWS account ID for production environment
- `PROD_AWS_REGION`: AWS region for production environment
- `PROD_AWS_ROLE_ARN`: IAM role ARN for production environment

#### Repository Variables
- `ETL_NAME`: Name of the ETL (default: repository name)

#### Repository Secrets (alternative to organization secrets)
- `AWS_ACCOUNT_ID`: AWS account ID for the environment
- `AWS_REGION`: AWS region for the environment
- `AWS_ROLE_ARN`: IAM role ARN for the environment

These variables and secrets can be set in the GitHub organization or repository settings under Settings > Secrets and variables.

### Manual Deployment

For manual deployment you can use the `scripts/etl/deploy-etl.sh` script from the [CloudTAK](https://github.com/TAK-NZ/CloudTAK/) repo.
As an example:
```
../CloudTAK/scripts/etl/deploy-etl.sh Demo v1.0.0 --profile tak-nz-demo
```

### CloudTAK Configuration

When registering this ETL as a task in CloudTAK:

- Use the `<repo-name>.png` file in the main folder of this repository as the Task Logo
- Use the raw GitHub URL of this README.md file as the Task Markdown Readme URL

This will ensure proper visual identification and documentation for the task in the CloudTAK interface.

## Development

TAK.NZ provided Lambda ETLs are currently all written in [NodeJS](https://nodejs.org/en) through the use of a AWS Lambda optimized
Docker container. Documentation for the Dockerfile can be found in the [AWS Help Center](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)

```sh
npm install
```

Add a .env file in the root directory that gives the ETL script the necessary variables to communicate with a local ETL server.
When the ETL is deployed the `ETL_API` and `ETL_LAYER` variables will be provided by the Lambda Environment

```json
{
    "ETL_API": "http://localhost:5001",
    "ETL_LAYER": "19"
}
```

To run the task, ensure the local [CloudTAK](https://github.com/TAK-NZ/CloudTAK/) server is running and then run with typescript runtime
or build to JS and run natively with node

```
ts-node task.ts
```

```
npm run build
cp .env dist/
node dist/task.js
```

## License

TAK.NZ is distributed under [AGPL-3.0-only](LICENSE)
Copyright (C) 2025 - Christian Elsen, Team Awareness Kit New Zealand (TAK.NZ)

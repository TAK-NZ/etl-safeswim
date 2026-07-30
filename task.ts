import { Type, TSchema } from '@sinclair/typebox';
import { fetch } from '@tak-ps/etl';
import ETL, { Event, SchemaType, handler as internal, local, InvocationType, DataFlowType } from '@tak-ps/etl';

const API_URL = 'https://safeswim.org.nz/api/locations';
const DETAIL_API_URL = (slug: string) => `https://safeswim.org.nz/api/locations/${slug}`;

// SafeSwim NZ iconset - see iconset/README.md and iconset/source/iconset.xml
const ICONSET = 'c2ec216e-9bfc-461d-b77a-e2099ffa9fa7';
const ICON_PREFIX = `${ICONSET}:Safeswim/`;

const QUALITY_LABELS: Record<string, string> = {
    'GREEN': 'Good',
    'RED': 'Not Advised',
    'RED+': 'Not Advised (Overflow)',
    'BLACK': 'Do Not Swim',
    'UNKNOWN': 'Not Rated'
};

interface SafeswimLocation {
    name: string;
    alternative_name: string | null;
    slug: string;
    position: [number, number]; // [lat, lng]
    patrolled: boolean;
    // Note: `quality` is not always present in the API response - roughly a
    // quarter of locations only report `patrol` and/or `safety` (e.g. surf
    // lifesaving patrolled beaches without council water quality testing).
    state: {
        quality?: string;
        patrol?: string;
        safety?: string;
    };
}

interface SafeswimResponse {
    locations: SafeswimLocation[];
}

interface SafeswimAlert {
    id: string;
    title: string;
    description: string;
    from: string;
    to: string | null;
}

interface SafeswimLocationDetail {
    alerts?: SafeswimAlert[];
}

type Feature = {
    id: string;
    type: 'Feature';
    properties: Record<string, unknown>;
    geometry: { type: 'Point'; coordinates: number[] };
};

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

const OutputSchema = Type.Object({
    quality: Type.String({ description: 'Water quality state (GREEN, RED, RED+, BLACK, or UNKNOWN if not reported by Safeswim for this location)' }),
    patrol: Type.Optional(Type.String({ description: 'Lifeguard patrol state (ON_DUTY, OFF_DUTY) - only present when patrolled' })),
    safety: Type.Optional(Type.String({ description: 'Safety hazard state (WARNING, WARNING+) - only present when a hazard exists' })),
    patrolled: Type.Boolean({ description: 'Whether the location is lifeguard-capable' }),
    slug: Type.String({ description: 'Safeswim location slug' }),
    name: Type.String({ description: 'Location name' }),
    alternative_name: Type.Union([Type.String(), Type.Null()], { description: 'Alternative location name, if any' }),
    alerts: Type.Optional(Type.Array(Type.Object({
        title: Type.String(),
        description: Type.String(),
        from: Type.String(),
        to: Type.Union([Type.String(), Type.Null()])
    }), { description: 'Active safety alert(s) for this location, fetched from the per-location detail endpoint - only present when a safety warning is active' }))
});

function getPatrolIcon(patrolled: boolean, patrol: string | undefined, hasSafetyWarning: boolean): string {
    let filename: string;
    if (patrolled && patrol === 'ON_DUTY') filename = 'SW.Patrol.OnDuty';
    else if (patrolled) filename = 'SW.Patrol.OffDuty';
    else filename = 'SW.Patrol.None';
    if (hasSafetyWarning) filename += '.Hazard';
    return ICON_PREFIX + filename + '.png';
}

/**
 * Determine the icon path for a location based on display mode, water
 * quality, patrol state, and safety state.
 *
 * A safety warning always adds the `.Hazard` diamond overlay on top of
 * whatever patrol-status overlay already applies (they're independent,
 * combinable badges in the iconset - not mutually exclusive).
 *
 * Roughly a quarter of Safeswim locations don't report a `quality` value at
 * all (surf-lifesaving patrolled beaches without council water-quality
 * testing). There is no "unrated" water-quality circle in the iconset, so
 * for these locations we fall back to the patrol-status badge (with the
 * hazard overlay if a safety warning is present) regardless of display mode,
 * rather than misrepresenting them as GREEN/good quality.
 */
function getIcon(
    mode: string,
    quality: string | undefined,
    patrolled: boolean,
    patrol: string | undefined,
    safety: string | undefined
): string {
    const hasSafetyWarning = safety === 'WARNING' || safety === 'WARNING+';

    if (!quality) {
        return getPatrolIcon(patrolled, patrol, hasSafetyWarning);
    }

    // --- Quality-only mode ---
    if (mode === 'quality') {
        if (quality === 'BLACK') return ICON_PREFIX + 'SW.Quality.Black.png';
        if (quality === 'RED' || quality === 'RED+') return ICON_PREFIX + 'SW.Quality.Red.png';
        return ICON_PREFIX + 'SW.Quality.Green.png';
    }

    // --- Patrol-only mode ---
    if (mode === 'patrol') {
        return getPatrolIcon(patrolled, patrol, false);
    }

    // --- Combined mode (default) ---
    let base: string;
    if (quality === 'BLACK') base = 'Black';
    else if (quality === 'RED' || quality === 'RED+') base = 'Red';
    else base = 'Green';

    // Patrol status and hazard flag are independent, combinable overlays in
    // the iconset (e.g. SW.Green.Lifeguarded.Hazard.png exists alongside
    // SW.Green.Lifeguarded.png and SW.Green.Hazard.png), so build them up
    // separately rather than treating hazard as a replacement for patrol
    // status.
    let suffix = '';
    if (patrolled && patrol === 'ON_DUTY') {
        suffix = '.Lifeguarded';
    } else if (patrolled) {
        suffix = '.LifeguardedOff';
    }
    if (hasSafetyWarning) {
        suffix += '.Hazard';
    }

    return ICON_PREFIX + `SW.${base}${suffix}.png`;
}

function getPatrolLabel(patrolled: boolean, patrol?: string): string {
    if (!patrolled) return 'Not lifeguarded';
    if (patrol === 'ON_DUTY') return 'Lifeguards on duty';
    if (patrol === 'OFF_DUTY') return 'Lifeguards off duty';
    return 'Not lifeguarded';
}

function getSafetyLabel(safety: string): string {
    if (safety === 'WARNING+') return 'Elevated safety hazard';
    return 'Safety hazard present';
}

/**
 * Fetch the active safety alert(s) for a location (title + description text
 * shown on the Safeswim website, e.g. "Shellfish warning" details). This is
 * only available on the per-location detail endpoint, not the bulk list
 * endpoint, so it's only called for locations that already report a safety
 * warning from the list response - keeping the number of extra requests
 * small (currently a handful out of ~315 locations).
 *
 * Returns an empty array on any fetch/parse failure so callers can fall back
 * to the generic safety label rather than failing the whole ETL run.
 */
async function fetchAlerts(slug: string): Promise<SafeswimAlert[]> {
    try {
        const res = await fetch(DETAIL_API_URL(slug));
        if (!res.ok) {
            console.warn(`warn - failed to fetch alert detail for ${slug}: ${res.status} ${res.statusText}`);
            return [];
        }
        const detail = await res.json() as SafeswimLocationDetail;
        return detail.alerts || [];
    } catch (err) {
        console.warn(`warn - error fetching alert detail for ${slug}:`, err);
        return [];
    }
}

export default class Task extends ETL {
    static name = 'etl-safeswim';
    static flow = [DataFlowType.Incoming];
    static invocation = [InvocationType.Schedule];

    async schema(
        type: SchemaType = SchemaType.Input,
        flow: DataFlowType = DataFlowType.Incoming
    ): Promise<TSchema> {
        if (flow === DataFlowType.Incoming) {
            if (type === SchemaType.Input) {
                return Environment;
            } else {
                return OutputSchema;
            }
        } else {
            return Type.Object({});
        }
    }

    async control(): Promise<void> {
        const env = await this.env(Environment);
        const showAll = env['Show All'];
        const displayMode = env['Display Mode'];

        console.log(`ok - fetching Safeswim locations from ${API_URL}`);
        const res = await fetch(API_URL);
        if (!res.ok) {
            throw new Error(`Failed to fetch Safeswim locations: ${res.status} ${res.statusText}`);
        }

        const body = await res.json() as SafeswimResponse;
        console.log(`ok - fetched ${body.locations.length} Safeswim locations`);

        const stale = new Date(Date.now() + 20 * 60 * 1000).toISOString();
        const now = new Date().toISOString();

        const features: Feature[] = [];

        for (const loc of body.locations) {
            const quality = loc.state.quality;
            const patrol = loc.state.patrol;
            const safety = loc.state.safety;
            const hasSafetyWarning = safety === 'WARNING' || safety === 'WARNING+';

            // Locations with no quality rating at all are kept regardless of
            // `Show All`, since they aren't "good quality" - they simply have
            // no water quality data (usually patrol-only beaches).
            if (!showAll && quality === 'GREEN' && !hasSafetyWarning) continue;

            const [lat, lng] = loc.position;
            const qualityLabel = quality ? (QUALITY_LABELS[quality] || quality) : QUALITY_LABELS['UNKNOWN'];
            const patrolLabel = getPatrolLabel(loc.patrolled, patrol);
            const altSuffix = loc.alternative_name ? ` (aka ${loc.alternative_name})` : '';

            // Fetch the actual alert text (e.g. "Shellfish warning" + full
            // description) for locations with an active safety warning. Only
            // a handful of locations have this at any given time, so the
            // extra per-location request is cheap.
            const alerts = hasSafetyWarning ? await fetchAlerts(loc.slug) : [];
            const safetyLines = alerts.length > 0
                ? alerts.flatMap(alert => [
                    `Safety: ${alert.title}`,
                    ...(alert.description ? [alert.description.trim()] : [])
                ])
                : (hasSafetyWarning && safety ? [`Safety: ${getSafetyLabel(safety)}`] : []);

            const metadata: Record<string, unknown> = {
                quality: quality || 'UNKNOWN',
                patrolled: loc.patrolled,
                slug: loc.slug,
                name: loc.name,
                alternative_name: loc.alternative_name
            };
            if (patrol !== undefined) metadata.patrol = patrol;
            if (safety !== undefined) metadata.safety = safety;
            if (alerts.length > 0) {
                metadata.alerts = alerts.map(alert => ({
                    title: alert.title,
                    description: alert.description,
                    from: alert.from,
                    to: alert.to
                }));
            }

            features.push({
                id: `safeswim-${loc.slug}`,
                type: 'Feature',
                properties: {
                    callsign: `${loc.name}: ${qualityLabel}`,
                    type: 'a-o-X-i-e-h',
                    icon: getIcon(displayMode, quality, loc.patrolled, patrol, safety),
                    time: now,
                    start: now,
                    stale,
                    metadata,
                    remarks: [
                        `Water Quality: ${qualityLabel}`,
                        `Patrol: ${patrolLabel}`,
                        ...safetyLines,
                        `Location: ${loc.name}${altSuffix}`,
                        `More info: https://safeswim.org.nz/locations/${loc.slug}`
                    ].join('\n'),
                    links: [{
                        uid: `safeswim-${loc.slug}`,
                        relation: 'r-u',
                        mime: 'text/html',
                        url: `https://safeswim.org.nz/locations/${loc.slug}`,
                        remarks: 'Safeswim Details'
                    }]
                },
                geometry: {
                    type: 'Point',
                    coordinates: [lng, lat]
                }
            });
        }

        const fc = {
            type: 'FeatureCollection' as const,
            features
        };

        console.log(`ok - generated ${features.length} Safeswim features`);
        await this.submit(fc);
    }
}

await local(new Task(import.meta.url), import.meta.url);
export async function handler(event: Event = {}) {
    return await internal(new Task(import.meta.url), event);
}

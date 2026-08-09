import type { ActivityRow, Band, FormLocation, FormSpec } from "./types";

/**
 * Expands a format against the laboratory's configured locations.
 *
 * A format declared `locationScope: "rows"` — the temperature and humidity
 * form — carries one row pair per monitored location rather than the fixed
 * four the printed page provides. Everything downstream (the renderer, the
 * entry screen, the outstanding-work calculation) works from the resolved
 * spec, so they cannot disagree about how many rows a sheet has.
 */
export function resolveSpec(
  spec: FormSpec,
  locations: FormLocation[],
): FormSpec {
  if (spec.locationScope !== "rows") return spec;

  const applicable = applicableLocations(spec, locations);
  if (applicable.length === 0) return spec;

  return {
    ...spec,
    bands: spec.bands.map((band) =>
      band.layout === "dayGrid" ? withLocationRows(band, applicable) : band,
    ),
  };
}

/** Locations a format applies to, honouring any `locationKinds` restriction. */
export function applicableLocations(
  spec: FormSpec,
  locations: FormLocation[],
): FormLocation[] {
  if (!spec.locationKinds || spec.locationKinds.length === 0) return locations;
  return locations.filter((l) => spec.locationKinds!.includes(l.kind));
}

/**
 * Two rows per location — morning and evening — sharing a merged Location
 * cell, which is how the source page groups them.
 */
function withLocationRows(band: Band, locations: FormLocation[]): Band {
  const rows: ActivityRow[] = [];
  for (const loc of locations) {
    const range =
      loc.minC !== undefined || loc.maxC !== undefined
        ? { min: loc.minC, max: loc.maxC }
        : undefined;
    for (const period of ["M", "E"] as const) {
      rows.push({
        key: `${loc.key}:${period}`,
        label: `(${period})`,
        group: loc.key,
        groupLabel: loc.name,
        range,
      });
    }
  }
  return { ...band, rows };
}

/** True where a format keeps a separate sheet for each location. */
export function isPerLocation(spec: FormSpec): boolean {
  return spec.locationScope === "sheet";
}

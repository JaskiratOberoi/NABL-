import "server-only";
import { getSetting, setSetting } from "./db";

/**
 * Site and format configuration the laboratory controls.
 *
 * Three things live here rather than in the form specs: the monitored
 * locations on the temperature form, the activity lists for the maintenance
 * schedules the source document left blank, and the site details. All three
 * are decisions the laboratory has to make and record, not properties of the
 * printed format.
 */

export interface Site {
  key: string;
  name: string;
  address: string;
}

/**
 * NABL 112-B requires the collection centre to be covered by the same
 * controls as the main laboratory, so it is a first-class site here rather
 * than an afterthought.
 */
export const DEFAULT_SITES: Site[] = [
  {
    key: "main",
    name: "Noble Diagnostic Centre",
    address: "WZ-409C, Janak Park, Hari Nagar, New Delhi – 110064",
  },
  {
    key: "cc",
    name: "Collection Centre",
    address: "WZ-405A/A, Janak Park, Hari Nagar, New Delhi – 110064",
  },
];

export function sites(): Site[] {
  return getSetting<Site[]>("sites", DEFAULT_SITES);
}

export function setSites(value: Site[]) {
  setSetting("sites", value);
}

/**
 * A monitored location within the laboratory.
 *
 * Distinct from a site: a site is a licensed premises (WZ-409C or the
 * collection centre), a location is a place inside one where work is done or a
 * condition is monitored.
 */
export interface LabLocation {
  key: string;
  /** Printed name, e.g. "Fridge 1 – Freezer Area". */
  name: string;
  /** Which site the location belongs to. */
  site: string;
  /** What kind of condition applies, driving the acceptance range. */
  kind: "room" | "fridge" | "freezer" | "deepFreezer" | "incubator";
  /** Acceptance range for temperature, from the DI 6.3 page 10 criteria. */
  minC?: number;
  maxC?: number;
  /** Excluded from new sheets without deleting historical records. */
  retired?: boolean;
}

/**
 * The laboratory's monitored points.
 *
 * Note that this is six points, whereas the printed temperature form provides
 * only four Location rows — see finding S-03 in
 * docs/reference/DI6-source-defects.md. The platform renders one row pair per
 * configured location so that every point the acceptance criteria name can
 * actually be recorded.
 */
export const DEFAULT_LOCATIONS: LabLocation[] = [
  { key: "lab-1", name: "Lab 1", site: "main", kind: "room", minC: 22, maxC: 28 },
  { key: "lab-2", name: "Lab 2", site: "main", kind: "room", minC: 22, maxC: 28 },
  {
    key: "fridge-1-freezer",
    name: "Fridge 1 – Freezer Area",
    site: "main",
    kind: "freezer",
    minC: -20,
    maxC: -10,
  },
  {
    key: "fridge-1-fridge",
    name: "Fridge 1 – Fridge Area",
    site: "main",
    kind: "fridge",
    minC: 2,
    maxC: 8,
  },
  { key: "fridge-2", name: "Fridge 2", site: "main", kind: "fridge", minC: 2, maxC: 8 },
  {
    key: "sample-collection",
    name: "Sample Collection",
    site: "main",
    kind: "room",
    minC: 22,
    maxC: 28,
  },
];

export function locations(): LabLocation[] {
  return getSetting<LabLocation[]>("locations", DEFAULT_LOCATIONS);
}

/** Locations available for new entries, in configured order. */
export function activeLocations(site?: string): LabLocation[] {
  return locations().filter(
    (l) => !l.retired && (site === undefined || l.site === site),
  );
}

export function setLocations(value: LabLocation[]) {
  setSetting("locations", value);
}

export function locationName(key: string): string {
  return locations().find((l) => l.key === key)?.name ?? key;
}

/**
 * Row-label overrides, keyed `<formId>.<rowKey>`.
 *
 * Used for the Biolis 30i, Prolyte and Mindray BC-5380 schedules, whose
 * activity rows are blank in NDC-DI.
 */
export function formLabels(formId: string): Record<string, string> {
  return getSetting<Record<string, string>>(`labels.${formId}`, {});
}

export function setFormLabels(formId: string, labels: Record<string, string>) {
  setSetting(`labels.${formId}`, labels);
}

/** Forms whose activity rows the laboratory must define before use. */
export const FORMS_NEEDING_ACTIVITIES = [
  "maintenance-biolis-30i",
  "maintenance-prolyte",
  "maintenance-mindray-5380",
  "temperature-humidity-monitoring",
];

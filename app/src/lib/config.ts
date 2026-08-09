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
 * Row-label overrides, keyed `<formId>.<rowKey>`.
 *
 * Used for the temperature form's locations and for the Biolis 30i, Prolyte
 * and Mindray BC-5380 schedules, whose activity rows are blank in NDC-DI.
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

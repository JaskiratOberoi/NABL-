import "server-only";
import type { Band, EntryData, FormSpec } from "./forms/types";
import { dayKey } from "./forms/types";
import { ALL_FORMS } from "./forms/registry";
import { findSheet, periodKey } from "./sheets";

/**
 * Which records are outstanding.
 *
 * This is the part of the platform that addresses the gap NDC keeps falling
 * into: a format exists, but nobody notices that a fortnight of it was never
 * filled until an assessor turns the page. The dashboard answers "what has not
 * been recorded today" before it becomes a finding.
 */

export type BandState = "complete" | "partial" | "outstanding" | "notDue";

export interface BandStatus {
  bandKey: string;
  heading: string;
  cadence: Band["cadence"];
  state: BandState;
  /** Activity rows still blank for the current period. */
  missing: string[];
}

export interface FormStatus {
  spec: FormSpec;
  state: BandState;
  bands: BandStatus[];
  /** True where the format cannot be completed until activities are defined. */
  needsConfiguration: boolean;
}

/** Monday-based ISO week number, used to decide whether a weekly band is due. */
function isoWeek(d: Date): string {
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((t.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${t.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function periodBucket(cadence: Band["cadence"], d: Date): string | null {
  const y = d.getFullYear();
  const m = d.getMonth();
  switch (cadence) {
    case "weekly":
      return isoWeek(d);
    case "fortnightly":
      // Two buckets a month, matching how the source's five slot columns are used.
      return `${y}-${m}-${d.getDate() <= 15 ? "a" : "b"}`;
    case "monthly":
      return `${y}-${m}`;
    case "quarterly":
      return `${y}-Q${Math.floor(m / 3)}`;
    case "halfYearly":
      return `${y}-H${m < 6 ? 1 : 2}`;
    case "yearly":
      return `${y}`;
    default:
      return null;
  }
}

/** Does any slot in this band carry a date inside the current bucket? */
function slotBandSatisfied(
  band: Band,
  data: EntryData,
  when: Date,
): boolean {
  const bucket = periodBucket(band.cadence, when);
  if (!bucket) return true;

  const rows = band.rows.filter((r) => r.label || r.editableLabel);
  if (rows.length === 0) return true;

  return rows.every((row) => {
    for (let s = 1; s <= (band.slotCount ?? 5); s++) {
      const raw = data?.[band.key]?.[row.key]?.[`s${s}`];
      if (typeof raw !== "string" || !raw.includes("|")) continue;
      const [iso] = raw.split("|");
      if (!iso) continue;
      const d = new Date(`${iso}T00:00:00`);
      if (!Number.isNaN(d.getTime()) && periodBucket(band.cadence, d) === bucket) {
        return true;
      }
    }
    return false;
  });
}

function dayBandStatus(band: Band, data: EntryData, when: Date): BandStatus {
  const day = when.getDate();
  const from = band.dayFrom ?? 1;
  const to = band.dayTo ?? 31;

  // Only one of the two half-month grids covers today.
  if (day < from || day > to) {
    return {
      bandKey: band.key,
      heading: band.heading,
      cadence: band.cadence,
      state: "notDue",
      missing: [],
    };
  }

  const col = dayKey(day);
  const activities = band.rows.filter((r) => r.label || r.editableLabel);
  const missing = activities
    .filter((r) => {
      const v = data?.[band.key]?.[r.key]?.[col];
      return v === undefined || v === null || v === "" || v === false;
    })
    .map((r) => r.label || r.key);

  const doneBy = data?.[band.key]?.doneBy?.[col];
  const signed = band.attestation ? Boolean(doneBy) : true;

  // Complete needs every activity and, where the format has one, the
  // attestation. Outstanding means nothing at all has been recorded for the
  // day — anything in between is partial.
  const anyRecorded = missing.length < activities.length || Boolean(doneBy);
  const state: BandState =
    missing.length === 0 && signed
      ? "complete"
      : anyRecorded
        ? "partial"
        : "outstanding";

  return {
    bandKey: band.key,
    heading: band.heading,
    cadence: band.cadence,
    state,
    missing,
  };
}

/**
 * Daily status for the two formats that record a day per ledger line rather
 * than a day per grid column: the waste disposal record and the hypo solution
 * preparation form.
 */
function ledgerDayStatus(band: Band, data: EntryData, when: Date): BandStatus {
  const col = dayKey(when.getDate());
  const row = data?.[band.key]?.[col] ?? {};

  const keys =
    band.layout === "halfYearGrid"
      ? [monthAbbrev(when)]
      : (band.columns ?? []).map((c) => c.key);

  const filled = keys.filter((k) => {
    const v = row[k];
    return v !== undefined && v !== null && v !== "" && v !== false;
  }).length;

  return {
    bandKey: band.key,
    heading: band.heading,
    cadence: band.cadence,
    state:
      filled === 0 ? "outstanding" : filled === keys.length ? "complete" : "partial",
    missing: [],
  };
}

function monthAbbrev(d: Date): string {
  return ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JLY", "AUG", "SEP", "OCT", "NOV", "DEC"][
    d.getMonth()
  ];
}

export function formStatus(
  spec: FormSpec,
  when: Date,
  site = "main",
  configuredLabels: Record<string, string> = {},
): FormStatus {
  const sheet = findSheet(spec.id, periodKey(spec, when), site);
  const data = sheet?.data ?? {};

  const needsConfiguration = spec.bands.some((b) =>
    b.rows.some((r) => r.editableLabel && !configuredLabels[r.key]),
  );

  const bands: BandStatus[] = spec.bands.map((band) => {
    if (band.layout === "dayGrid" || band.layout === "fullMonthGrid") {
      return band.layout === "fullMonthGrid"
        ? dayBandStatus({ ...band, dayFrom: 1, dayTo: 31 }, data, when)
        : dayBandStatus(band, data, when);
    }
    if (band.layout === "slots") {
      const bucket = periodBucket(band.cadence, when);
      if (!bucket) {
        return {
          bandKey: band.key,
          heading: band.heading,
          cadence: band.cadence,
          state: "notDue" as BandState,
          missing: [],
        };
      }
      return {
        bandKey: band.key,
        heading: band.heading,
        cadence: band.cadence,
        state: slotBandSatisfied(band, data, when)
          ? ("complete" as BandState)
          : ("outstanding" as BandState),
        missing: [],
      };
    }
    // The waste disposal record and the hypo form are daily, but record one
    // ledger line per day rather than one grid column.
    if (band.layout === "halfYearGrid" || band.layout === "pairedLedger") {
      return ledgerDayStatus(band, data, when);
    }

    // A free ledger such as the autoclave form records events as they happen,
    // so it is never overdue on a given day.
    return {
      bandKey: band.key,
      heading: band.heading,
      cadence: band.cadence,
      state: "notDue" as BandState,
      missing: [],
    };
  });

  const due = bands.filter((b) => b.state !== "notDue");
  let state: BandState = "notDue";
  if (due.length > 0) {
    if (due.every((b) => b.state === "complete")) state = "complete";
    else if (due.every((b) => b.state === "outstanding")) state = "outstanding";
    else state = "partial";
  }

  return { spec, state, bands, needsConfiguration };
}

export function allStatuses(
  when: Date,
  site = "main",
  labelsFor: (formId: string) => Record<string, string> = () => ({}),
): FormStatus[] {
  return ALL_FORMS.map((spec) =>
    formStatus(spec, when, site, labelsFor(spec.id)),
  );
}

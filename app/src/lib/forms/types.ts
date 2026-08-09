/**
 * Declarative description of an NDC record format.
 *
 * Every form in NDC-DI is built from the same handful of primitives: a title
 * block, one or more banded tables, and the controlled-copy footer. Describing
 * them as data rather than as bespoke components means the print renderer and
 * the data-entry screen are generated from a single source, and adding the
 * remaining DI 6 formats (and later DI 7 and DI 8) is a matter of writing a
 * spec rather than writing a component.
 */

export type ClauseRef = "6.2" | "6.3" | "6.4" | "6.5" | "6.6" | "6.7" | "6.8";

export const CLAUSE_TITLES: Record<ClauseRef, string> = {
  "6.2": "Documented Information – Personnel",
  "6.3": "Documented Information – Facilities and environmental conditions",
  "6.4": "Documented Information – Handling equipment",
  "6.5":
    "Documented Information – Equipment Calibration & Metrological traceability",
  "6.6": "Documented Information – Handling Reagents and Consumables",
  "6.7": "Documented Information – Service Agreements",
  "6.8": "Documented Information – Externally provided products and services",
};

/**
 * How often a band is completed. Drives the dashboard's outstanding-work
 * calculation: a `daily` band is due every day, a `weekly` band once a week.
 */
export type Cadence =
  | "daily"
  | "twiceDaily"
  | "weekly"
  | "fortnightly"
  | "monthly"
  | "quarterly"
  | "halfYearly"
  | "yearly"
  | "asRequired";

/**
 * What a cell collects.
 *
 * `tick`        the routine case: the activity was performed
 * `initial`     a person attests; renders that person's signature image
 * `text`        free text, e.g. an autoclave load description
 * `number`      a measured value, optionally range-checked
 * `time`        a clock time, e.g. autoclave start/end
 * `dateInitial` the paired date-and-initial cell used by weekly and monthly bands
 */
export type CellKind =
  | "tick"
  | "initial"
  | "text"
  | "number"
  | "time"
  | "dateInitial"
  /** The row's own number, printed rather than entered. */
  | "serial";

export interface NumericRange {
  min?: number;
  max?: number;
  /** Printed acceptance-criteria text, verbatim from the source format. */
  label?: string;
}

/** A single activity line within a band. */
export interface ActivityRow {
  /** Stable key used to address the row in stored entry data. */
  key: string;
  /** Printed label. An empty string is legitimate — see `editableLabel`. */
  label: string;
  /**
   * Second line of the printed label. The source formats wrap long activity
   * names onto a fixed second line; reproducing the break keeps row heights
   * identical to the original page.
   */
  sublabel?: string;
  /**
   * True where the source format left the activity column blank and the
   * laboratory must define the activity itself. The label is then supplied
   * from equipment configuration rather than from this spec. Three of the
   * DI 6 maintenance schedules are in this state; see docs/reference.
   */
  editableLabel?: boolean;
  /** Overrides the band's default cell kind for this row. */
  cell?: CellKind;
  range?: NumericRange;
  /**
   * Merges this row's left-hand cell with adjacent rows carrying the same
   * group key, as the temperature form does for each location's (M)/(E) pair.
   */
  group?: string;
  /** Label printed in the merged group cell. Blank where lab-configurable. */
  groupLabel?: string;
  /** Frequency code printed in the FREQ column of the housekeeping schedule. */
  freq?: string;
  /** Marks the row as an attestation line rendered in the source's heavier style. */
  attestation?: boolean;
  /**
   * Renders as a full-width heading spanning the band, for the section breaks
   * the induction training format uses (INTRODUCTION, LAB PREMISES ROUND …).
   */
  sectionRow?: boolean;
  /**
   * Merges this row's value cell with adjacent rows carrying the same key, as
   * the induction format does for the Accompanied By column.
   */
  spanWith?: string;
  /** Value printed in a merged span cell. */
  spanValue?: string;
}

/**
 * A horizontal band of the format.
 *
 * `dayGrid`      the split-month grid, days `dayFrom`..`dayTo`
 * `fullMonthGrid` all 31 days in one band, used by the housekeeping schedule
 * `slots`        a fixed number of Date/Initial columns
 * `monthGrid`    twelve columns, JAN..DEC
 * `ledger`       free rows under named columns, e.g. the autoclave form
 * `pairedLedger` two identical day ledgers side by side, 1..16 and 17..31
 * `halfYearGrid` date rows 1..31 against six month/Done-By column pairs
 * `fields`       labelled free-text fields, for formats that are a record
 *                about one subject rather than a grid of days
 * `prose`        numbered or plain paragraphs, for the agreements and letters
 * `authGrid`     activities laid out as repeated activity/status column pairs
 */
export type BandLayout =
  | "dayGrid"
  | "fullMonthGrid"
  | "slots"
  | "monthGrid"
  | "ledger"
  | "pairedLedger"
  | "halfYearGrid"
  | "fields"
  | "prose"
  | "authGrid";

export interface LedgerColumn {
  key: string;
  label: string;
  cell: CellKind;
  /** Relative width; columns are laid out proportionally. */
  width?: number;
  range?: NumericRange;
  /** Groups adjacent columns under a spanning header, e.g. "Solid Waste Disposal". */
  group?: string;
}

export interface Band {
  key: string;
  /** Heading in the band's first column, e.g. "Daily", "WEEKLY", "MONTHLY". */
  heading: string;
  layout: BandLayout;
  cadence: Cadence;
  rows: ActivityRow[];
  /** Default cell kind for rows that do not override it. */
  cell?: CellKind;
  /** Day range for `dayGrid`. */
  dayFrom?: number;
  dayTo?: number;
  /** Number of Date/Initial columns for `slots` bands. */
  slotCount?: number;
  /**
   * Column headings for a `slots` band, where the source uses something other
   * than "Date/Initial" — the half-year columns of the outsourced lab
   * evaluation, or the named criteria of the supplier performance evaluation.
   */
  slotLabels?: string[];
  /** Field definitions for a `fields` band. */
  fields?: FormField[];
  /** Paragraphs for a `prose` band, verbatim from the source. */
  paragraphs?: string[];
  /** Numbers the paragraphs of a `prose` band, as the agreements do. */
  numbered?: boolean;
  /** How many activity/status column pairs an `authGrid` lays out. */
  pairColumns?: number;
  /** Column heading above each status column of an `authGrid`. */
  statusLabel?: string;
  /** Extra label columns printed before the data columns, e.g. ["Location","Date"]. */
  labelColumns?: string[];
  /** Column definitions for `ledger` and `pairedLedger` bands. */
  columns?: LedgerColumn[];
  /** Number of blank lines to print in a `ledger` band. */
  ledgerRows?: number;
  /** Height in millimetres of each `ledger` line, where the source is taller. */
  ledgerRowHeight?: number;
  /** Six months covered by a `halfYearGrid`, e.g. ["JAN",…,"JUN"]. */
  months?: string[];
  /** Appends the Done By / Verified By rows that close every dayGrid band. */
  attestation?: boolean;
  /** Printed immediately below the band, verbatim. */
  note?: string;
  /**
   * Renders this band in the right half of the page, level with the band
   * before it. The source pairs several bands this way — YEARLY beside
   * MONTHLY, REPLACEMENTS beside AS NEEDED.
   */
  beside?: boolean;
  /**
   * Continues the previous band's table rather than starting a new one: the
   * heading becomes a row within that table and the column headers are not
   * repeated. The source does this for FORTNIGHTLY under WEEKLY, and for
   * QUARTERLY and 6 MONTHLY under MONTHLY.
   */
  continues?: boolean;
}

/** A labelled entry on a `fields` band. */
export interface FormField {
  key: string;
  label: string;
  cell?: CellKind;
  /** Fraction of the row this field occupies; 1 is the full measure. */
  width?: 0.25 | 0.33 | 0.5 | 1;
  /** Renders as a block of lines rather than a single rule. */
  lines?: number;
  /** A numbered sub-list, as the supplier registration form uses. */
  listCount?: number;
  /** Renders the bordered "Please affix your photograph here" box. */
  photo?: boolean;
  /**
   * Prints the label alone with no rule to write on, for the caption lines the
   * source sets under a signature or as a standing sentence.
   */
  noRule?: boolean;
  /** Printed above the field as a section rule. */
  section?: string;
}

export interface FormSpec {
  /** Stable identifier, also the URL segment. */
  id: string;
  /** Printed title, verbatim and upper case as in the source. */
  title: string;
  /** The "(Recording schedule – …)" line, verbatim. */
  recordingSchedule: string;
  clause: ClauseRef;
  /** The "Page N of clause X" footer value. */
  pageOfClause: number;
  /** Page in docs/legacy/DI 6.pdf this format reproduces, for verification. */
  sourcePage: number;
  /**
   * Paper size of the source page. NDC-DI is inconsistent: every clause 6.3
   * format is US Letter and every clause 6.4 format is A4. The platform prints
   * all of them on A4, which is what the laboratory stocks; this field records
   * what the master document actually used.
   */
  sourcePageSize?: "A4" | "Letter";
  /** Footer strap line where it differs from CLAUSE_TITLES. */
  footerTitle?: string;
  /** Doc No. where the source prints it irregularly, e.g. "NDC / DI/ 6.3". */
  docNoOverride?: string;
  orientation: "portrait" | "landscape";
  /** One sheet per month, or one sheet per half year (the hypo form). */
  sheetPeriod: "month" | "halfYear";
  /** Binds the sheet to an equipment record so it can pull a configured activity list. */
  equipmentKey?: string;
  /**
   * How the laboratory's monitored locations apply to this format.
   *
   * `rows`  one row group per location, filling the format's Location column —
   *         the temperature and humidity form
   * `sheet` a separate sheet per location, so Lab 1 and Lab 2 each have their
   *         own monthly record
   * `none`  one sheet covering the whole laboratory (the default)
   */
  locationScope?: "rows" | "sheet" | "none";
  /**
   * Restricts which kinds of location the format applies to. A housekeeping
   * schedule belongs to a room, not to a refrigerator.
   */
  locationKinds?: string[];
  /** Prints the "MONTH" caption above the first band. */
  showMonthCaption?: boolean;
  bands: Band[];
  /** Footnotes printed below the last band, verbatim. */
  footnotes?: string[];
  /** Legend line, e.g. "D – Daily   W – Weekly   …". */
  legend?: string;
  /** Free-text header fields, e.g. "Equipment Name:". */
  headerFields?: { key: string; label: string }[];
}

/**
 * The subset of a configured location the renderer needs.
 *
 * Declared here rather than imported from the configuration module so that the
 * spec layer and the components stay free of server-only code.
 */
export interface FormLocation {
  key: string;
  name: string;
  kind: string;
  minC?: number;
  maxC?: number;
}

/** Stored entry payload, addressed as data[bandKey][rowKey][columnKey]. */
export type EntryData = Record<
  string,
  Record<string, Record<string, string | boolean | null>>
>;

/** Convenience: the column key used for a given day in a dayGrid band. */
export const dayKey = (day: number) => `d${day}`;

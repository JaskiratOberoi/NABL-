import type { ClauseRef, FormSpec } from "./types";
import { CLAUSE_TITLES } from "./types";
import { facilitiesForms } from "./specs/facilities";
import { equipmentForms } from "./specs/equipment";
import { supplyForms } from "./specs/supplies";

/**
 * Every record format the platform can produce.
 *
 * Ordered by sub-clause and then by the format's page within that clause, so
 * the navigation mirrors NDC-DI itself. An assessor reading a printed record
 * can go straight from the footer's "Page N of clause X" to the same place in
 * the master document.
 */
export const ALL_FORMS: FormSpec[] = [
  ...facilitiesForms,
  ...equipmentForms,
  ...supplyForms,
];

export interface ClauseGroup {
  clause: ClauseRef;
  /** e.g. "NDC/DI/6.3" */
  docNo: string;
  /** e.g. "Facilities and environmental conditions" */
  shortTitle: string;
  /** The full strap line printed in the footer. */
  title: string;
  forms: FormSpec[];
}

const SHORT_TITLES: Record<ClauseRef, string> = {
  "6.2": "Personnel",
  "6.3": "Facilities and environmental conditions",
  "6.4": "Handling equipment",
  "6.5": "Equipment calibration and metrological traceability",
  "6.6": "Handling reagents and consumables",
  "6.7": "Service agreements",
  "6.8": "Externally provided products and services",
};

/** Forms grouped by sub-clause, each group sorted by page within the clause. */
export function formsByClause(): ClauseGroup[] {
  const clauses = [...new Set(ALL_FORMS.map((f) => f.clause))].sort();
  return clauses.map((clause) => ({
    clause,
    docNo: `NDC/DI/${clause}`,
    shortTitle: SHORT_TITLES[clause],
    title: CLAUSE_TITLES[clause],
    forms: ALL_FORMS.filter((f) => f.clause === clause).sort(
      (a, b) => a.pageOfClause - b.pageOfClause,
    ),
  }));
}

export function getForm(id: string): FormSpec | undefined {
  return ALL_FORMS.find((f) => f.id === id);
}

export function clauseOf(id: string): ClauseRef | undefined {
  return getForm(id)?.clause;
}

/** Short title for a clause, for headings and breadcrumbs. */
export function clauseShortTitle(clause: ClauseRef): string {
  return SHORT_TITLES[clause];
}

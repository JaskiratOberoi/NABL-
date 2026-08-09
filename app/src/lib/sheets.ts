import "server-only";
import { db, all, one } from "./db";
import type { EntryData, FormSpec } from "./forms/types";

export interface Sheet {
  id: number;
  form_id: string;
  period_key: string;
  site: string;
  /** Empty for formats that keep one sheet for the whole laboratory. */
  location: string;
  data: EntryData;
  header: Record<string, string>;
  created_at: string;
  updated_at: string;
}

interface SheetRow {
  id: number;
  form_id: string;
  period_key: string;
  site: string;
  location: string;
  data: string;
  header: string;
  created_at: string;
  updated_at: string;
}

/** `2026-08` for monthly sheets, `2026-H1` for the half-yearly hypo form. */
export function periodKey(spec: FormSpec, when: Date): string {
  const y = when.getFullYear();
  if (spec.sheetPeriod === "halfYear") {
    return `${y}-H${when.getMonth() < 6 ? 1 : 2}`;
  }
  return `${y}-${String(when.getMonth() + 1).padStart(2, "0")}`;
}

/** Human label for a period key, e.g. "August 2026" or "Jan–Jun 2026". */
export function periodLabel(key: string): string {
  const [year, part] = key.split("-");
  if (part?.startsWith("H")) {
    return part === "H1" ? `Jan–Jun ${year}` : `Jul–Dec ${year}`;
  }
  const month = Number(part) - 1;
  const names = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  return `${names[month]} ${year}`;
}

function parse(row: SheetRow): Sheet {
  return {
    ...row,
    data: JSON.parse(row.data) as EntryData,
    header: JSON.parse(row.header) as Record<string, string>,
  };
}

/** Fetches the sheet for a period, creating an empty one if it does not exist. */
export function getOrCreateSheet(
  formId: string,
  period: string,
  site = "main",
  location = "",
): Sheet {
  const existing = findSheet(formId, period, site, location);
  if (existing) return existing;

  db()
    .prepare(
      "INSERT INTO sheets (form_id, period_key, site, location) VALUES (?, ?, ?, ?)",
    )
    .run(formId, period, site, location);

  return findSheet(formId, period, site, location)!;
}

export function findSheet(
  formId: string,
  period: string,
  site = "main",
  location = "",
): Sheet | null {
  const row = one<SheetRow>(
    `SELECT * FROM sheets
     WHERE form_id = ? AND period_key = ? AND site = ? AND location = ?`,
    formId,
    period,
    site,
    location,
  );
  return row ? parse(row) : null;
}

export function listPeriods(
  formId: string,
  site = "main",
  location = "",
): string[] {
  return all<{ period_key: string }>(
    `SELECT period_key FROM sheets
     WHERE form_id = ? AND site = ? AND location = ?
     ORDER BY period_key DESC`,
    formId,
    site,
    location,
  ).map((r) => r.period_key);
}

/**
 * Writes cell values and records who did it.
 *
 * The data blob is the working state the screen reads back; the audit rows are
 * the permanent account of the change. Both are written in one transaction so
 * a saved value can never exist without its attribution.
 */
export function applyCellUpdates(
  sheetId: number,
  staffId: number,
  updates: { band: string; row: string; col: string; value: string | boolean | null }[],
  action = "cell-update",
): Sheet {
  const conn = db();
  const readSheet = conn.prepare("SELECT * FROM sheets WHERE id = ?");

  conn.exec("BEGIN IMMEDIATE");
  try {
    const current = parse(readSheet.get(sheetId) as unknown as SheetRow);
    const data = current.data;

    for (const u of updates) {
      data[u.band] ??= {};
      data[u.band][u.row] ??= {};
      data[u.band][u.row][u.col] = u.value;
    }

    conn
      .prepare(
        "UPDATE sheets SET data = ?, updated_at = datetime('now') WHERE id = ?",
      )
      .run(JSON.stringify(data), sheetId);

    conn
      .prepare(
        "INSERT INTO audit_log (sheet_id, staff_id, action, detail) VALUES (?, ?, ?, ?)",
      )
      .run(sheetId, staffId, action, JSON.stringify({ updates }));

    conn.exec("COMMIT");
    return parse(readSheet.get(sheetId) as unknown as SheetRow);
  } catch (err) {
    conn.exec("ROLLBACK");
    throw err;
  }
}

export function setHeader(
  sheetId: number,
  staffId: number,
  header: Record<string, string>,
): void {
  const conn = db();
  conn.exec("BEGIN IMMEDIATE");
  try {
    conn
      .prepare(
        "UPDATE sheets SET header = ?, updated_at = datetime('now') WHERE id = ?",
      )
      .run(JSON.stringify(header), sheetId);
    conn
      .prepare(
        "INSERT INTO audit_log (sheet_id, staff_id, action, detail) VALUES (?, ?, ?, ?)",
      )
      .run(sheetId, staffId, "header-update", JSON.stringify(header));
    conn.exec("COMMIT");
  } catch (err) {
    conn.exec("ROLLBACK");
    throw err;
  }
}

export interface AuditEntry {
  id: number;
  staff_name: string;
  staff_code: string;
  action: string;
  detail: string;
  at: string;
}

export function sheetAudit(sheetId: number, limit = 200): AuditEntry[] {
  return all<AuditEntry>(
    `SELECT a.id, s.name AS staff_name, s.code AS staff_code,
            a.action, a.detail, a.at
     FROM audit_log a JOIN staff s ON s.id = a.staff_id
     WHERE a.sheet_id = ? ORDER BY a.id DESC LIMIT ?`,
    sheetId,
    limit,
  );
}

import "server-only";
import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import path from "node:path";

/**
 * SQLite via Node's built-in driver.
 *
 * The platform runs on one machine on the laboratory network, so a single
 * embedded database file is the right storage. Using `node:sqlite` rather than
 * a compiled binding means deployment needs nothing beyond Node 22+, which
 * matters for a site with no IT staff to rebuild native modules.
 */

const DATA_DIR = process.env.NDC_DATA_DIR ?? path.join(process.cwd(), "data");
const DB_PATH = path.join(DATA_DIR, "ndc-qms.db");

let instance: DatabaseSync | null = null;

export function db(): DatabaseSync {
  if (instance) return instance;
  mkdirSync(DATA_DIR, { recursive: true });
  const conn = new DatabaseSync(DB_PATH);
  // WAL keeps readers from blocking the bench terminal that is writing.
  conn.exec("PRAGMA journal_mode = WAL");
  conn.exec("PRAGMA foreign_keys = ON");
  conn.exec("PRAGMA busy_timeout = 5000");
  migrate(conn);
  instance = conn;
  return conn;
}

function migrate(conn: DatabaseSync) {
  conn.exec(`
    CREATE TABLE IF NOT EXISTS staff (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      code          TEXT NOT NULL UNIQUE,
      name          TEXT NOT NULL,
      designation   TEXT NOT NULL DEFAULT '',
      department    TEXT NOT NULL DEFAULT '',
      initials      TEXT NOT NULL DEFAULT '',
      signature     TEXT,               -- data URL of the uploaded signature
      password_hash TEXT NOT NULL,
      role          TEXT NOT NULL DEFAULT 'technician',
      active        INTEGER NOT NULL DEFAULT 1,
      created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS sessions (
      id         TEXT PRIMARY KEY,
      staff_id   INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
      expires_at TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- One sheet per record format per period, e.g. facility-round-checklist / 2026-08.
    CREATE TABLE IF NOT EXISTS sheets (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      form_id     TEXT NOT NULL,
      period_key  TEXT NOT NULL,
      site        TEXT NOT NULL DEFAULT 'main',
      data        TEXT NOT NULL DEFAULT '{}',
      header      TEXT NOT NULL DEFAULT '{}',
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (form_id, period_key, site)
    );

    /*
     * Append-only record of who set what and when. Nothing in the application
     * updates or deletes from this table; it is the evidence that a printed
     * record was keyed by a named person on a given date, which a stored
     * signature image on its own cannot show.
     */
    CREATE TABLE IF NOT EXISTS audit_log (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      sheet_id  INTEGER NOT NULL REFERENCES sheets(id) ON DELETE CASCADE,
      staff_id  INTEGER NOT NULL REFERENCES staff(id),
      action    TEXT NOT NULL,
      detail    TEXT NOT NULL DEFAULT '{}',
      at        TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_audit_sheet ON audit_log(sheet_id);
    CREATE INDEX IF NOT EXISTS idx_sheets_form ON sheets(form_id, period_key);

    -- Lab-configurable values: monitored locations, per-instrument activity
    -- lists for the schedules the source document left blank, site details.
    CREATE TABLE IF NOT EXISTS settings (
      key   TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
  `);
}

type Param = string | number | bigint | null | Uint8Array;

/**
 * Typed query helpers.
 *
 * `node:sqlite` returns rows as `Record<string, SQLOutputValue>`. Rather than
 * casting at every call site, the shape is asserted once here.
 */
export function one<T>(sql: string, ...params: Param[]): T | undefined {
  return db().prepare(sql).get(...params) as T | undefined;
}

export function all<T>(sql: string, ...params: Param[]): T[] {
  return db().prepare(sql).all(...params) as T[];
}

export function run(sql: string, ...params: Param[]) {
  return db().prepare(sql).run(...params);
}

export function getSetting<T>(key: string, fallback: T): T {
  const row = one<{ value: string }>(
    "SELECT value FROM settings WHERE key = ?",
    key,
  );
  if (!row) return fallback;
  try {
    return JSON.parse(row.value) as T;
  } catch {
    return fallback;
  }
}

export function setSetting(key: string, value: unknown): void {
  run(
    `INSERT INTO settings (key, value) VALUES (?, ?)
     ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
    key,
    JSON.stringify(value),
  );
}

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
  conn.exec("PRAGMA busy_timeout = 5000");

  // Migrations run before foreign keys are enforced. A table rebuild has to
  // drop and recreate `sheets`, and with enforcement on that cascades into
  // `audit_log` and destroys the attribution trail.
  migrate(conn);

  conn.exec("PRAGMA foreign_keys = ON");
  instance = conn;
  return conn;
}

/**
 * Schema migrations.
 *
 * Stepped on `PRAGMA user_version` so an installed laboratory database is
 * upgraded in place rather than needing to be rebuilt — quality records are
 * the one thing here that cannot be recreated.
 */
function migrate(conn: DatabaseSync) {
  const version = (
    conn.prepare("PRAGMA user_version").get() as { user_version: number }
  ).user_version;

  if (version < 1) migrateV1(conn);
  if (version < 2) migrateV2(conn);

  conn.exec("PRAGMA user_version = 2");
}

/**
 * Adds the location dimension to a sheet.
 *
 * A format such as the housekeeping schedule keeps one sheet per room, so the
 * sheet's identity becomes form + period + site + location. SQLite cannot drop
 * an inline UNIQUE constraint, so the table is rebuilt and the constraint moved
 * to a named index.
 */
function migrateV2(conn: DatabaseSync) {
  const columns = conn.prepare("PRAGMA table_info(sheets)").all() as {
    name: string;
  }[];
  if (columns.some((c) => c.name === "location")) return;

  // Belt and braces: `db()` defers enabling foreign keys until migrations are
  // done, but this asserts it here too, because getting it wrong silently
  // deletes every audit row via ON DELETE CASCADE when `sheets` is dropped.
  conn.exec("PRAGMA foreign_keys = OFF");

  conn.exec(`
    BEGIN IMMEDIATE;

    CREATE TABLE sheets_new (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      form_id     TEXT NOT NULL,
      period_key  TEXT NOT NULL,
      site        TEXT NOT NULL DEFAULT 'main',
      location    TEXT NOT NULL DEFAULT '',
      data        TEXT NOT NULL DEFAULT '{}',
      header      TEXT NOT NULL DEFAULT '{}',
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    INSERT INTO sheets_new (id, form_id, period_key, site, data, header, created_at, updated_at)
      SELECT id, form_id, period_key,
             COALESCE(site, 'main'),
             COALESCE(data, '{}'),
             COALESCE(header, '{}'),
             COALESCE(created_at, datetime('now')),
             COALESCE(updated_at, datetime('now'))
      FROM sheets;

    DROP TABLE sheets;
    ALTER TABLE sheets_new RENAME TO sheets;

    CREATE UNIQUE INDEX idx_sheets_identity
      ON sheets(form_id, period_key, site, location);
    CREATE INDEX idx_sheets_form ON sheets(form_id, period_key);

    COMMIT;
  `);
}

function migrateV1(conn: DatabaseSync) {
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

    /*
     * One sheet per record format per period, per site, per location — for
     * example facility-round-checklist / 2026-08 / main / (no location), or
     * housekeeping-schedule / 2026-08 / main / lab-1.
     */
    CREATE TABLE IF NOT EXISTS sheets (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      form_id     TEXT NOT NULL,
      period_key  TEXT NOT NULL,
      site        TEXT NOT NULL DEFAULT 'main',
      location    TEXT NOT NULL DEFAULT '',
      data        TEXT NOT NULL DEFAULT '{}',
      header      TEXT NOT NULL DEFAULT '{}',
      created_at  TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_sheets_identity
      ON sheets(form_id, period_key, site, location);

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

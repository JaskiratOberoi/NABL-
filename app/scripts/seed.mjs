/**
 * Creates the database and the first administrator account.
 *
 * Run once after installing:  npm run seed
 *
 * Deliberately creates only one account, with a password that must be changed
 * on first sign-in. Staff records are added through the application so that
 * each person's signature image is captured against their own account rather
 * than assigned to them by someone else.
 */
import { DatabaseSync } from "node:sqlite";
import { randomBytes, scryptSync } from "node:crypto";
import { mkdirSync } from "node:fs";
import path from "node:path";

const DATA_DIR = process.env.NDC_DATA_DIR ?? path.join(process.cwd(), "data");
mkdirSync(DATA_DIR, { recursive: true });
const db = new DatabaseSync(path.join(DATA_DIR, "ndc-qms.db"));

db.exec("PRAGMA journal_mode = WAL");
db.exec("PRAGMA foreign_keys = ON");

db.exec(`
  CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    designation TEXT NOT NULL DEFAULT '',
    department TEXT NOT NULL DEFAULT '',
    initials TEXT NOT NULL DEFAULT '',
    signature TEXT,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'technician',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    staff_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE TABLE IF NOT EXISTS sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    form_id TEXT NOT NULL,
    period_key TEXT NOT NULL,
    site TEXT NOT NULL DEFAULT 'main',
    location TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL DEFAULT '{}',
    header TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE UNIQUE INDEX IF NOT EXISTS idx_sheets_identity
    ON sheets(form_id, period_key, site, location);
  CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_id INTEGER NOT NULL REFERENCES sheets(id) ON DELETE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES staff(id),
    action TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}',
    at TEXT NOT NULL DEFAULT (datetime('now'))
  );
  CREATE INDEX IF NOT EXISTS idx_audit_sheet ON audit_log(sheet_id);
  CREATE INDEX IF NOT EXISTS idx_sheets_form ON sheets(form_id, period_key);
  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  );
`);

function hash(password) {
  const salt = randomBytes(16);
  return `scrypt:${salt.toString("hex")}:${scryptSync(password, salt, 64).toString("hex")}`;
}

const existing = db.prepare("SELECT COUNT(*) AS n FROM staff").get();
if (existing.n > 0) {
  console.log(`Database already has ${existing.n} staff record(s); nothing to do.`);
} else {
  const password = process.env.NDC_ADMIN_PASSWORD ?? "change-me-now";
  db.prepare(
    `INSERT INTO staff (code, name, designation, department, initials, password_hash, role)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
  ).run(
    "QM",
    "Quality Manager",
    "Quality Manager",
    "Quality",
    "QM",
    hash(password),
    "quality-manager",
  );
  console.log("Created the initial account:");
  console.log("  staff code: QM");
  console.log(`  password:   ${password}`);
  console.log("\nSign in and change this password before anyone else uses the system.");
}

db.close();

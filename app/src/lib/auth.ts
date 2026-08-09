import "server-only";
import { cookies } from "next/headers";
import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";
import { db } from "./db";

/**
 * Session handling.
 *
 * Password hashing uses Node's built-in scrypt rather than an argon2 binding,
 * so the platform installs on any machine with Node and no build toolchain.
 */

const COOKIE = "ndc_session";
const SESSION_DAYS = 14;

export interface Staff {
  id: number;
  code: string;
  name: string;
  designation: string;
  department: string;
  initials: string;
  signature: string | null;
  role: "technician" | "supervisor" | "quality-manager" | "director";
  active: number;
}

export function hashPassword(password: string): string {
  const salt = randomBytes(16);
  const derived = scryptSync(password, salt, 64);
  return `scrypt:${salt.toString("hex")}:${derived.toString("hex")}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [scheme, saltHex, hashHex] = stored.split(":");
  if (scheme !== "scrypt" || !saltHex || !hashHex) return false;
  const derived = scryptSync(password, Buffer.from(saltHex, "hex"), 64);
  const expected = Buffer.from(hashHex, "hex");
  return (
    derived.length === expected.length && timingSafeEqual(derived, expected)
  );
}

export function createSession(staffId: number): {
  id: string;
  expiresAt: Date;
} {
  const id = randomBytes(32).toString("hex");
  const expiresAt = new Date(Date.now() + SESSION_DAYS * 86400_000);
  db()
    .prepare("INSERT INTO sessions (id, staff_id, expires_at) VALUES (?, ?, ?)")
    .run(id, staffId, expiresAt.toISOString());
  return { id, expiresAt };
}

export async function currentStaff(): Promise<Staff | null> {
  const jar = await cookies();
  const sid = jar.get(COOKIE)?.value;
  if (!sid) return null;

  const row = db()
    .prepare(
      `SELECT s.* FROM staff s
       JOIN sessions ss ON ss.staff_id = s.id
       WHERE ss.id = ? AND ss.expires_at > datetime('now') AND s.active = 1`,
    )
    .get(sid) as Staff | undefined;

  return row ?? null;
}

/** Throws where a page or action requires a signed-in user. */
export async function requireStaff(): Promise<Staff> {
  const staff = await currentStaff();
  if (!staff) throw new Error("UNAUTHENTICATED");
  return staff;
}

export async function setSessionCookie(id: string, expiresAt: Date) {
  const jar = await cookies();
  jar.set(COOKIE, id, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    expires: expiresAt,
    // The platform is served over plain HTTP on the laboratory network, so the
    // Secure attribute would prevent the cookie being set at all.
    secure: false,
  });
}

export async function clearSession() {
  const jar = await cookies();
  const sid = jar.get(COOKIE)?.value;
  if (sid) db().prepare("DELETE FROM sessions WHERE id = ?").run(sid);
  jar.delete(COOKIE);
}

export const SESSION_COOKIE = COOKIE;

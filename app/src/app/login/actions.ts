"use server";

import { redirect } from "next/navigation";
import { db } from "@/lib/db";
import {
  createSession,
  setSessionCookie,
  verifyPassword,
  clearSession,
} from "@/lib/auth";

export async function signIn(
  _prev: { error?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string }> {
  const code = String(formData.get("code") ?? "").trim().toUpperCase();
  const password = String(formData.get("password") ?? "");

  if (!code || !password) {
    return { error: "Enter your staff code and password." };
  }

  const row = db()
    .prepare("SELECT id, password_hash FROM staff WHERE code = ? AND active = 1")
    .get(code) as { id: number; password_hash: string } | undefined;

  // The same message for an unknown code and a wrong password, so the form
  // cannot be used to discover who has an account.
  if (!row || !verifyPassword(password, row.password_hash)) {
    return { error: "Staff code or password not recognised." };
  }

  const session = createSession(row.id);
  await setSessionCookie(session.id, session.expiresAt);
  redirect("/");
}

export async function signOut() {
  await clearSession();
  redirect("/login");
}

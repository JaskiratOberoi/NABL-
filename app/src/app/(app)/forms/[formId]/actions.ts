"use server";

import { revalidatePath } from "next/cache";
import { requireStaff } from "@/lib/auth";
import { getForm } from "@/lib/forms/registry";
import { applyCellUpdates, getOrCreateSheet } from "@/lib/sheets";
import { formLabels } from "@/lib/config";
import { dayKey } from "@/lib/forms/types";

/**
 * Records one day's entries for a daily band.
 *
 * The signed-in user is the person the entry is attributed to. The action does
 * not accept a staff identifier from the client, so a sheet cannot be signed in
 * someone else's name from a terminal they are not logged in at.
 */
export async function saveDay(formData: FormData) {
  const staff = await requireStaff();

  const formId = String(formData.get("formId"));
  const period = String(formData.get("period"));
  const site = String(formData.get("site") ?? "main");
  const bandKey = String(formData.get("bandKey"));
  const day = Number(formData.get("day"));

  const spec = getForm(formId);
  if (!spec) throw new Error(`Unknown format: ${formId}`);
  const band = spec.bands.find((b) => b.key === bandKey);
  if (!band) throw new Error(`Unknown band: ${bandKey}`);

  const sheet = getOrCreateSheet(formId, period, site);
  const col = dayKey(day);

  const updates: {
    band: string;
    row: string;
    col: string;
    value: string | boolean | null;
  }[] = [];

  for (const row of band.rows) {
    const raw = formData.get(`r_${row.key}`);
    const kind = row.cell ?? band.cell ?? "tick";
    if (kind === "tick") {
      updates.push({ band: bandKey, row: row.key, col, value: raw === "on" });
    } else {
      const value = raw === null ? null : String(raw).trim();
      updates.push({
        band: bandKey,
        row: row.key,
        col,
        value: value === "" ? null : value,
      });
    }
  }

  // The attestation is the signed-in user's own mark, taken from the session.
  if (band.attestation) {
    updates.push({
      band: bandKey,
      row: "doneBy",
      col,
      value: staff.code,
    });
  }

  applyCellUpdates(sheet.id, staff.id, updates, `day-entry:${bandKey}:${day}`);
  revalidatePath(`/forms/${formId}`);
  revalidatePath("/");
}

/**
 * Verifies a day's entries.
 *
 * Kept separate from `saveDay` so that verification is a distinct act by a
 * second person, which is what the Verified By column on the paper form means.
 */
export async function verifyDay(formData: FormData) {
  const staff = await requireStaff();

  const formId = String(formData.get("formId"));
  const period = String(formData.get("period"));
  const site = String(formData.get("site") ?? "main");
  const bandKey = String(formData.get("bandKey"));
  const day = Number(formData.get("day"));

  const sheet = getOrCreateSheet(formId, period, site);
  applyCellUpdates(
    sheet.id,
    staff.id,
    [
      {
        band: bandKey,
        row: "verifiedBy",
        col: dayKey(day),
        value: staff.code,
      },
    ],
    `verify:${bandKey}:${day}`,
  );
  revalidatePath(`/forms/${formId}`);
  revalidatePath("/");
}

/**
 * Carry-forward.
 *
 * Copies the previous day's ticks into today. This is a convenience, not an
 * assertion: it still requires the user to press the button today, it is
 * attributed to them, and it is written to the audit log under its own action
 * name so that a reviewer can see which days were entered this way.
 */
export async function carryForward(formData: FormData) {
  const staff = await requireStaff();

  const formId = String(formData.get("formId"));
  const period = String(formData.get("period"));
  const site = String(formData.get("site") ?? "main");
  const bandKey = String(formData.get("bandKey"));
  const day = Number(formData.get("day"));

  const spec = getForm(formId);
  if (!spec) throw new Error(`Unknown format: ${formId}`);
  const band = spec.bands.find((b) => b.key === bandKey);
  if (!band) throw new Error(`Unknown band: ${bandKey}`);
  if (day <= 1) throw new Error("There is no previous day on this sheet.");

  const sheet = getOrCreateSheet(formId, period, site);
  const prev = dayKey(day - 1);
  const col = dayKey(day);

  const updates = band.rows.map((row) => ({
    band: bandKey,
    row: row.key,
    col,
    value: sheet.data?.[bandKey]?.[row.key]?.[prev] ?? null,
  }));

  if (band.attestation) {
    updates.push({ band: bandKey, row: "doneBy", col, value: staff.code });
  }

  applyCellUpdates(
    sheet.id,
    staff.id,
    updates,
    `carry-forward:${bandKey}:${day}`,
  );
  revalidatePath(`/forms/${formId}`);
  revalidatePath("/");
}

/** Records a slot entry on a weekly, monthly or yearly band. */
export async function saveSlot(formData: FormData) {
  const staff = await requireStaff();

  const formId = String(formData.get("formId"));
  const period = String(formData.get("period"));
  const site = String(formData.get("site") ?? "main");
  const bandKey = String(formData.get("bandKey"));
  const rowKey = String(formData.get("rowKey"));
  const slot = String(formData.get("slot"));
  const date = String(formData.get("date"));

  const sheet = getOrCreateSheet(formId, period, site);
  applyCellUpdates(
    sheet.id,
    staff.id,
    [
      {
        band: bandKey,
        row: rowKey,
        col: `s${slot}`,
        value: date ? `${date}|${staff.code}` : null,
      },
    ],
    `slot-entry:${bandKey}:${rowKey}`,
  );
  revalidatePath(`/forms/${formId}`);
  revalidatePath("/");
}

/** Reads the configured activity labels for a format. */
export async function labelsFor(formId: string) {
  return formLabels(formId);
}

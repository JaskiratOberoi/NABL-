"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db } from "@/lib/db";
import { hashPassword, requireStaff } from "@/lib/auth";

const StaffInput = z.object({
  code: z.string().trim().min(1).max(12).toUpperCase(),
  name: z.string().trim().min(1).max(120),
  designation: z.string().trim().max(120).default(""),
  department: z.string().trim().max(120).default(""),
  initials: z.string().trim().max(8).default(""),
  role: z.enum(["technician", "supervisor", "quality-manager", "director"]),
  password: z.string().min(8).max(200),
});

/** Only these roles may manage the staff register. */
function assertManager(role: string) {
  if (role !== "quality-manager" && role !== "director") {
    throw new Error("Only the Quality Manager or Lab Director may do this.");
  }
}

export async function addStaff(
  _prev: { error?: string; ok?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string; ok?: string }> {
  const actor = await requireStaff();
  assertManager(actor.role);

  const parsed = StaffInput.safeParse({
    code: formData.get("code"),
    name: formData.get("name"),
    designation: formData.get("designation") ?? "",
    department: formData.get("department") ?? "",
    initials: formData.get("initials") ?? "",
    role: formData.get("role"),
    password: formData.get("password"),
  });

  if (!parsed.success) {
    return {
      error:
        "Check the entries: a staff code, a name, a role and a password of at least 8 characters are required.",
    };
  }
  const v = parsed.data;

  const clash = db()
    .prepare("SELECT 1 FROM staff WHERE code = ?")
    .get(v.code);
  if (clash) return { error: `Staff code ${v.code} is already in use.` };

  db()
    .prepare(
      `INSERT INTO staff (code, name, designation, department, initials, password_hash, role)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
    )
    .run(
      v.code,
      v.name,
      v.designation,
      v.department,
      v.initials || v.code,
      hashPassword(v.password),
      v.role,
    );

  revalidatePath("/settings/staff");
  return { ok: `Added ${v.name}.` };
}

/**
 * Stores a staff member's signature image.
 *
 * A person may only upload their own signature: it is the mark that will
 * appear against their name on a controlled record, so it should not be
 * possible for one member of staff to install another's.
 */
export async function uploadSignature(formData: FormData) {
  const actor = await requireStaff();
  const file = formData.get("signature");

  if (!(file instanceof File) || file.size === 0) {
    throw new Error("Choose a signature image to upload.");
  }
  if (file.size > 512 * 1024) {
    throw new Error("The signature image must be under 512 KB.");
  }
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    throw new Error("The signature must be a PNG, JPEG or WebP image.");
  }

  const buf = Buffer.from(await file.arrayBuffer());
  const dataUrl = `data:${file.type};base64,${buf.toString("base64")}`;

  db()
    .prepare("UPDATE staff SET signature = ? WHERE id = ?")
    .run(dataUrl, actor.id);

  revalidatePath("/settings/staff");
}

export async function changePassword(
  _prev: { error?: string; ok?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string; ok?: string }> {
  const actor = await requireStaff();
  const next = String(formData.get("password") ?? "");
  const confirm = String(formData.get("confirm") ?? "");

  if (next.length < 8) {
    return { error: "Choose a password of at least 8 characters." };
  }
  if (next !== confirm) return { error: "The two passwords do not match." };

  db()
    .prepare("UPDATE staff SET password_hash = ? WHERE id = ?")
    .run(hashPassword(next), actor.id);

  return { ok: "Password changed." };
}

export async function setActive(formData: FormData) {
  const actor = await requireStaff();
  assertManager(actor.role);

  const id = Number(formData.get("id"));
  const active = formData.get("active") === "1" ? 1 : 0;

  if (id === actor.id && active === 0) {
    throw new Error("You cannot deactivate your own account.");
  }

  // Records already signed keep that person's name; deactivating only stops
  // further sign-ins, so the audit trail on past sheets stays intact.
  db().prepare("UPDATE staff SET active = ? WHERE id = ?").run(active, id);
  revalidatePath("/settings/staff");
}

"use server";

import { revalidatePath } from "next/cache";
import { requireStaff } from "@/lib/auth";
import { setFormLabels, formLabels } from "@/lib/config";
import { getForm } from "@/lib/forms/registry";

export async function saveLabels(formData: FormData) {
  const actor = await requireStaff();
  if (actor.role !== "quality-manager" && actor.role !== "director") {
    throw new Error(
      "Only the Quality Manager or Lab Director may change a record format.",
    );
  }

  const formId = String(formData.get("formId"));
  const spec = getForm(formId);
  if (!spec) throw new Error(`Unknown format: ${formId}`);

  const next: Record<string, string> = { ...formLabels(formId) };
  for (const [key, value] of formData.entries()) {
    if (!key.startsWith("label_")) continue;
    const rowKey = key.slice("label_".length);
    const text = String(value).trim();
    if (text) next[rowKey] = text;
    else delete next[rowKey];
  }

  setFormLabels(formId, next);
  revalidatePath("/settings/formats");
  revalidatePath(`/forms/${formId}`);
  revalidatePath("/");
}

"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireStaff } from "@/lib/auth";
import { locations, setLocations, type LabLocation } from "@/lib/config";

const KIND = z.enum(["room", "fridge", "freezer", "deepFreezer", "incubator"]);

/** Default acceptance ranges, from the DI 6.3 page 10 criteria. */
const RANGES: Record<z.infer<typeof KIND>, { minC: number; maxC: number }> = {
  room: { minC: 22, maxC: 28 },
  fridge: { minC: 2, maxC: 8 },
  freezer: { minC: -20, maxC: -10 },
  deepFreezer: { minC: -80, maxC: -60 },
  incubator: { minC: 35, maxC: 39 },
};

function assertManager(role: string) {
  if (role !== "quality-manager" && role !== "director") {
    throw new Error(
      "Only the Quality Manager or Lab Director may change the monitored locations.",
    );
  }
}

/** Turns a name into a stable key, kept unique against the existing set. */
function keyFor(name: string, taken: Set<string>): string {
  const base =
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "location";
  let key = base;
  let n = 2;
  while (taken.has(key)) key = `${base}-${n++}`;
  return key;
}

export async function addLocation(
  _prev: { error?: string; ok?: string } | undefined,
  formData: FormData,
): Promise<{ error?: string; ok?: string }> {
  const actor = await requireStaff();
  assertManager(actor.role);

  const parsed = z
    .object({
      name: z.string().trim().min(1).max(80),
      site: z.string().trim().min(1),
      kind: KIND,
      minC: z.coerce.number().optional(),
      maxC: z.coerce.number().optional(),
    })
    .safeParse({
      name: formData.get("name"),
      site: formData.get("site") ?? "main",
      kind: formData.get("kind"),
      minC: formData.get("minC") || undefined,
      maxC: formData.get("maxC") || undefined,
    });

  if (!parsed.success) return { error: "Enter a name and choose a kind." };
  const v = parsed.data;

  const current = locations();
  if (
    current.some(
      (l) => l.name.toLowerCase() === v.name.toLowerCase() && l.site === v.site,
    )
  ) {
    return { error: `${v.name} is already a monitored location.` };
  }

  const fallback = RANGES[v.kind];
  const next: LabLocation = {
    key: keyFor(v.name, new Set(current.map((l) => l.key))),
    name: v.name,
    site: v.site,
    kind: v.kind,
    minC: v.minC ?? fallback.minC,
    maxC: v.maxC ?? fallback.maxC,
  };

  setLocations([...current, next]);
  revalidateAll();
  return { ok: `Added ${v.name}.` };
}

/**
 * Retires a location rather than deleting it.
 *
 * Sheets already recorded against it keep their rows and stay printable; the
 * location simply stops appearing on new ones. Deleting outright would orphan
 * historical quality records.
 */
export async function setRetired(formData: FormData) {
  const actor = await requireStaff();
  assertManager(actor.role);

  const key = String(formData.get("key"));
  const retired = formData.get("retired") === "1";

  setLocations(
    locations().map((l) => (l.key === key ? { ...l, retired } : l)),
  );
  revalidateAll();
}

export async function updateRanges(formData: FormData) {
  const actor = await requireStaff();
  assertManager(actor.role);

  const next = locations().map((l) => {
    const min = formData.get(`min_${l.key}`);
    const max = formData.get(`max_${l.key}`);
    return {
      ...l,
      minC: min === null || min === "" ? undefined : Number(min),
      maxC: max === null || max === "" ? undefined : Number(max),
    };
  });

  setLocations(next);
  revalidateAll();
}

function revalidateAll() {
  revalidatePath("/settings/locations");
  revalidatePath("/forms/temperature-humidity-monitoring");
  revalidatePath("/");
}

import { notFound } from "next/navigation";
import { requireStaff } from "@/lib/auth";
import { db } from "@/lib/db";
import { activeLocations, formLabels, locationName } from "@/lib/config";
import { getForm } from "@/lib/forms/registry";
import { resolveSpec } from "@/lib/forms/resolve";
import { FormSheet } from "@/components/form/sheet";
import type { SignatureLookup } from "@/components/form/cells";
import { findSheet, periodLabel } from "@/lib/sheets";
import { PrintButton } from "./print-button";

/**
 * The printable sheet.
 *
 * Everything on this page other than the sheet itself is hidden by the print
 * stylesheet, so printing from the browser produces the record and nothing
 * else.
 */
export default async function PrintPage({
  params,
  searchParams,
}: {
  params: Promise<{ formId: string; period: string }>;
  searchParams: Promise<{ site?: string; location?: string }>;
}) {
  await requireStaff();
  const { formId, period } = await params;
  const { site = "main", location = "" } = await searchParams;

  const base = getForm(formId);
  if (!base) notFound();

  const spec = resolveSpec(base, activeLocations(site));
  const sheet = findSheet(spec.id, period, site, location);
  const labels = formLabels(spec.id);

  const rows = db()
    .prepare("SELECT code, name, initials, signature FROM staff")
    .all() as {
    code: string;
    name: string;
    initials: string;
    signature: string | null;
  }[];
  const signatures: SignatureLookup = Object.fromEntries(
    rows.map((r) => [
      r.code,
      { name: r.name, signature: r.signature, initials: r.initials || r.code },
    ]),
  );

  return (
    <>
      {/* Landscape formats need the page box rotated for printing. */}
      {spec.orientation === "landscape" && (
        <style>{"@page { size: A4 landscape; margin: 0 }"}</style>
      )}

      <div className="no-print flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
        <div>
          <div className="text-sm font-semibold text-slate-900">
            {spec.title}
          </div>
          <div className="text-xs text-slate-500">
            NDC/DI/{spec.clause} · Page {spec.pageOfClause} of clause{" "}
            {spec.clause} · {periodLabel(period)}
            {location && ` · ${locationName(location)}`}
          </div>
        </div>
        <PrintButton />
      </div>

      <div className="print-root sheet-preview">
        <FormSheet
          spec={spec}
          data={sheet?.data ?? {}}
          header={{
            ...(sheet?.header ?? {}),
            monthLabel: periodLabel(period),
            ...(location ? { location: locationName(location) } : {}),
          }}
          signatures={signatures}
          labels={labels}
        />
      </div>
    </>
  );
}

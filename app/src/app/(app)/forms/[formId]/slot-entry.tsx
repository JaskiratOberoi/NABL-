"use client";

import type { Band, EntryData } from "@/lib/forms/types";
import { saveSlot } from "./actions";

/**
 * Weekly, monthly, quarterly and yearly bands.
 *
 * These record a date and a signature into one of a fixed number of columns,
 * exactly as the paper form does, so the printed sheet fills left to right in
 * the order the work was actually done.
 */
export function SlotEntry({
  formId,
  period,
  site,
  band,
  data,
  labels,
  staffNames,
  today,
}: {
  formId: string;
  period: string;
  site: string;
  band: Band;
  data: EntryData;
  labels: Record<string, string>;
  staffNames: Record<string, string>;
  today: string;
}) {
  const slots = Array.from({ length: band.slotCount ?? 5 }, (_, i) => i + 1);
  const rows = band.rows.filter((r) => r.label || r.editableLabel);
  if (rows.length === 0) return null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">{band.heading}</h3>
        <p className="mt-0.5 text-xs text-slate-500">
          {cadenceHint(band.cadence)}
        </p>
      </div>

      <div className="divide-y divide-slate-100">
        {rows.map((row) => {
          const label =
            labels[row.key] ??
            [row.label, row.sublabel].filter(Boolean).join(" ");
          return (
            <div key={row.key} className="px-4 py-3">
              <div className="mb-2 text-sm text-slate-800">
                {label || (
                  <span className="italic text-amber-700">
                    Activity not yet defined
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {slots.map((slot) => {
                  const raw = data?.[band.key]?.[row.key]?.[`s${slot}`];
                  const [date, code] =
                    typeof raw === "string" ? raw.split("|") : [];
                  return (
                    <form
                      key={slot}
                      action={saveSlot}
                      className="flex items-center gap-1.5 rounded-md border border-slate-200 px-2 py-1.5"
                    >
                      <input type="hidden" name="formId" value={formId} />
                      <input type="hidden" name="period" value={period} />
                      <input type="hidden" name="site" value={site} />
                      <input type="hidden" name="bandKey" value={band.key} />
                      <input type="hidden" name="rowKey" value={row.key} />
                      <input type="hidden" name="slot" value={slot} />
                      <input
                        type="date"
                        name="date"
                        defaultValue={date || ""}
                        className="rounded border border-slate-300 px-1.5 py-1 text-xs outline-none focus:border-slate-900"
                      />
                      <button
                        type="submit"
                        className="rounded bg-slate-900 px-2 py-1 text-xs text-white hover:bg-slate-800"
                      >
                        {date ? "Update" : "Sign"}
                      </button>
                      {code && (
                        <span className="text-xs text-slate-500">
                          {staffNames[code] ?? code}
                        </span>
                      )}
                    </form>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400">
        Today is {today}.
      </p>
    </div>
  );
}

function cadenceHint(cadence: Band["cadence"]): string {
  switch (cadence) {
    case "weekly":
      return "Due once each week. Five columns cover the month.";
    case "fortnightly":
      return "Due twice each month.";
    case "monthly":
      return "Due once each month.";
    case "quarterly":
      return "Due once each quarter.";
    case "halfYearly":
      return "Due twice each year.";
    case "yearly":
      return "Due once each year.";
    case "asRequired":
      return "Recorded when the work is carried out.";
    default:
      return "";
  }
}

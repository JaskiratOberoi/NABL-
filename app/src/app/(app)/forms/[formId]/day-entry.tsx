"use client";

import { useState } from "react";
import type { Band, EntryData } from "@/lib/forms/types";
import { dayKey } from "@/lib/forms/types";
import { carryForward, saveDay, verifyDay } from "./actions";

/**
 * One day's entry for a daily band.
 *
 * Deliberately shows a single day rather than the whole month grid: the person
 * at the bench is recording what they did now, and a 31-column grid on a
 * touchscreen invites ticking the wrong column. The month grid is on the
 * printed sheet, where it belongs.
 */
export function DayEntry({
  formId,
  period,
  site,
  band,
  day,
  data,
  labels,
  currentStaffCode,
  staffNames,
}: {
  formId: string;
  period: string;
  site: string;
  band: Band;
  day: number;
  data: EntryData;
  labels: Record<string, string>;
  currentStaffCode: string;
  staffNames: Record<string, string>;
}) {
  const col = dayKey(day);
  const cell = (rowKey: string) => data?.[band.key]?.[rowKey]?.[col];
  const kind = band.cell ?? "tick";

  const [dirty, setDirty] = useState(false);

  const doneBy = cell("doneBy");
  const verifiedBy = cell("verifiedBy");
  const activities = band.rows;
  const canVerify = Boolean(doneBy) && doneBy !== currentStaffCode;

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">
          {band.heading} — day {day}
        </h3>
        {doneBy ? (
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
            Recorded by {staffNames[String(doneBy)] ?? doneBy}
          </span>
        ) : (
          <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
            Not recorded
          </span>
        )}
      </div>

      <form action={saveDay} onChange={() => setDirty(true)} className="p-4">
        <input type="hidden" name="formId" value={formId} />
        <input type="hidden" name="period" value={period} />
        <input type="hidden" name="site" value={site} />
        <input type="hidden" name="bandKey" value={band.key} />
        <input type="hidden" name="day" value={day} />

        <ul className="space-y-1">
          {activities.map((row) => {
            // The spec stores the source's line break; the entry screen wants
            // the activity as one readable phrase.
            const label =
              labels[row.key] ??
              [row.label, row.sublabel].filter(Boolean).join(" ");
            const value = cell(row.key);
            const rowKind = row.cell ?? kind;

            if (!label && !row.editableLabel) return null;

            return (
              <li key={row.key}>
                {rowKind === "tick" ? (
                  <label className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 hover:bg-slate-50">
                    <input
                      type="checkbox"
                      name={`r_${row.key}`}
                      defaultChecked={value === true}
                      className="h-5 w-5 rounded border-slate-300 text-slate-900 focus:ring-slate-900"
                    />
                    <span className="text-sm text-slate-800">
                      {label || (
                        <span className="italic text-amber-700">
                          Activity not yet defined
                        </span>
                      )}
                    </span>
                  </label>
                ) : (
                  <label className="flex items-center gap-3 rounded-md px-2 py-1.5">
                    <span className="flex-1 text-sm text-slate-800">
                      {label}
                    </span>
                    <input
                      type={rowKind === "number" ? "number" : "text"}
                      step="any"
                      name={`r_${row.key}`}
                      defaultValue={
                        typeof value === "string" ? value : ""
                      }
                      className="w-28 rounded-md border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                    />
                  </label>
                )}
              </li>
            );
          })}
        </ul>

        <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4">
          <button
            type="submit"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            {dirty || !doneBy ? "Record and sign" : "Re-record and sign"}
          </button>
          <span className="text-xs text-slate-500">
            Signed as {staffNames[currentStaffCode] ?? currentStaffCode}
          </span>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 px-4 py-3">
        {day > 1 && (
          <form action={carryForward}>
            <input type="hidden" name="formId" value={formId} />
            <input type="hidden" name="period" value={period} />
            <input type="hidden" name="site" value={site} />
            <input type="hidden" name="bandKey" value={band.key} />
            <input type="hidden" name="day" value={day} />
            <button
              type="submit"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              title="Copies yesterday's entries into today. Recorded in the audit log as a carry-forward."
            >
              Same as day {day - 1}
            </button>
          </form>
        )}

        {verifiedBy ? (
          <span className="text-xs text-slate-500">
            Verified by {staffNames[String(verifiedBy)] ?? verifiedBy}
          </span>
        ) : (
          band.attestation && (
            <form action={verifyDay}>
              <input type="hidden" name="formId" value={formId} />
              <input type="hidden" name="period" value={period} />
              <input type="hidden" name="site" value={site} />
              <input type="hidden" name="bandKey" value={band.key} />
              <input type="hidden" name="day" value={day} />
              <button
                type="submit"
                disabled={!canVerify}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                title={
                  doneBy
                    ? doneBy === currentStaffCode
                      ? "Verification is a second person's check; you recorded this entry."
                      : "Confirm you have checked this entry"
                    : "Nothing recorded to verify yet"
                }
              >
                Verify
              </button>
            </form>
          )
        )}
      </div>
    </div>
  );
}

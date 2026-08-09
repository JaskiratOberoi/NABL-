"use client";

import { saveLabels } from "./actions";

export function LabelEditor({
  formId,
  rows,
}: {
  formId: string;
  rows: {
    key: string;
    band: string;
    placeholder: string;
    current: string;
  }[];
}) {
  // Group by band so the editor reads in the same order as the printed sheet.
  const bands = rows.reduce<Record<string, typeof rows>>((acc, row) => {
    (acc[row.band] ??= []).push(row);
    return acc;
  }, {});

  return (
    <form action={saveLabels} className="p-4">
      <input type="hidden" name="formId" value={formId} />
      <div className="space-y-5">
        {Object.entries(bands).map(([band, bandRows]) => (
          <div key={band}>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
              {band}
            </div>
            <div className="space-y-2">
              {bandRows.map((row, i) => (
                <div key={row.key} className="flex items-center gap-3">
                  <span className="w-6 shrink-0 text-right font-mono text-xs text-slate-400">
                    {i + 1}
                  </span>
                  <input
                    name={`label_${row.key}`}
                    defaultValue={row.current}
                    placeholder={row.placeholder}
                    className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4">
        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Save
        </button>
        <span className="text-xs text-slate-500">
          Leave a row blank to keep it empty on the printed sheet.
        </span>
      </div>
    </form>
  );
}

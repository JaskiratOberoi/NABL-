"use client";

import { useActionState } from "react";
import { addLocation, updateRanges } from "./actions";

const field =
  "rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900";
const label = "block text-xs font-medium text-slate-700";

export function RangeEditor({
  rows,
}: {
  rows: {
    key: string;
    name: string;
    site: string;
    kind: string;
    minC?: number;
    maxC?: number;
    retired: boolean;
  }[];
}) {
  return (
    <form action={updateRanges}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-2.5 font-semibold">Location</th>
            <th className="px-4 py-2.5 font-semibold">Site</th>
            <th className="px-4 py-2.5 font-semibold">Kind</th>
            <th className="px-4 py-2.5 font-semibold">Min °C</th>
            <th className="px-4 py-2.5 font-semibold">Max °C</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => (
            <tr key={r.key} className={r.retired ? "opacity-50" : ""}>
              <td className="px-4 py-2 font-medium text-slate-900">{r.name}</td>
              <td className="px-4 py-2 text-slate-600">{r.site}</td>
              <td className="px-4 py-2 text-slate-600">{r.kind}</td>
              <td className="px-4 py-2">
                <input
                  type="number"
                  step="any"
                  name={`min_${r.key}`}
                  defaultValue={r.minC ?? ""}
                  className={`${field} w-24`}
                />
              </td>
              <td className="px-4 py-2">
                <input
                  type="number"
                  step="any"
                  name={`max_${r.key}`}
                  defaultValue={r.maxC ?? ""}
                  className={`${field} w-24`}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="border-t border-slate-100 px-4 py-3">
        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Save ranges
        </button>
      </div>
    </form>
  );
}

export function AddLocationForm({
  sites,
}: {
  sites: { key: string; name: string }[];
}) {
  const [state, action, pending] = useActionState(addLocation, {});
  return (
    <form action={action} className="grid grid-cols-4 gap-3">
      <div className="col-span-2">
        <label htmlFor="name" className={label}>
          Name
        </label>
        <input
          id="name"
          name="name"
          placeholder="e.g. Fridge 3 – Fridge Area"
          className={`${field} mt-1 w-full`}
        />
      </div>
      <div>
        <label htmlFor="site" className={label}>
          Site
        </label>
        <select id="site" name="site" className={`${field} mt-1 w-full`}>
          {sites.map((s) => (
            <option key={s.key} value={s.key}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="kind" className={label}>
          Kind
        </label>
        <select
          id="kind"
          name="kind"
          defaultValue="room"
          className={`${field} mt-1 w-full`}
        >
          <option value="room">Room</option>
          <option value="fridge">Refrigerator</option>
          <option value="freezer">Freezer</option>
          <option value="deepFreezer">Ultra deep freezer</option>
          <option value="incubator">Incubator</option>
        </select>
      </div>
      <div>
        <label htmlFor="minC" className={label}>
          Min °C (optional)
        </label>
        <input
          id="minC"
          name="minC"
          type="number"
          step="any"
          className={`${field} mt-1 w-full`}
        />
      </div>
      <div>
        <label htmlFor="maxC" className={label}>
          Max °C (optional)
        </label>
        <input
          id="maxC"
          name="maxC"
          type="number"
          step="any"
          className={`${field} mt-1 w-full`}
        />
      </div>
      <div className="col-span-2 flex items-end">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
        >
          Add location
        </button>
      </div>
      {state?.error && (
        <p className="col-span-4 text-sm text-red-700">{state.error}</p>
      )}
      {state?.ok && (
        <p className="col-span-4 text-sm text-emerald-700">{state.ok}</p>
      )}
      <p className="col-span-4 text-xs text-slate-500">
        Leave the range blank to use the default for that kind, taken from the
        acceptance criteria printed on the temperature form.
      </p>
    </form>
  );
}

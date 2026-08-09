import { requireStaff } from "@/lib/auth";
import { locations, sites } from "@/lib/config";
import { ALL_FORMS } from "@/lib/forms/registry";
import { AddLocationForm, RangeEditor } from "./forms";
import { setRetired } from "./actions";

const KIND_LABELS: Record<string, string> = {
  room: "Room",
  fridge: "Refrigerator",
  freezer: "Freezer",
  deepFreezer: "Ultra deep freezer",
  incubator: "Incubator",
};

/**
 * Monitored locations.
 *
 * These drive two things: the row pairs on the temperature and humidity form,
 * and the separate sheets kept by formats that are recorded per room.
 */
export default async function LocationSettingsPage() {
  await requireStaff();

  const all = locations();
  const siteList = sites();

  const rowScoped = ALL_FORMS.filter((f) => f.locationScope === "rows");
  const sheetScoped = ALL_FORMS.filter((f) => f.locationScope === "sheet");

  return (
    <div className="max-w-4xl p-6">
      <h1 className="text-2xl font-semibold text-slate-900">
        Monitored locations
      </h1>
      <p className="mt-1 text-sm text-slate-600">
        The places inside the laboratory where a condition is monitored or work
        is recorded separately.
      </p>

      <div className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4">
        <h2 className="text-sm font-semibold text-amber-900">
          The printed form has fewer rows than you have locations
        </h2>
        <p className="mt-1 text-sm text-amber-800">
          NDC/DI/6.3 page 10 provides four Location rows. You have{" "}
          {all.filter((l) => !l.retired).length} monitored points, so the format
          as issued cannot record everything its own acceptance criteria name.
          The platform prints one row pair per location instead. Correct the
          master format at Issue V — recorded as S-03 in the source defects
          note.
        </p>
      </div>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Locations and acceptance ranges
        </h2>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <RangeEditor
            rows={all.map((l) => ({
              key: l.key,
              name: l.name,
              site: siteList.find((s) => s.key === l.site)?.name ?? l.site,
              kind: KIND_LABELS[l.kind] ?? l.kind,
              minC: l.minC,
              maxC: l.maxC,
              retired: Boolean(l.retired),
            }))}
          />
        </div>
        <p className="mt-2 text-xs text-slate-500">
          A reading outside its range is flagged on the entry screen and
          underlined on the printed sheet.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Retire or restore
        </h2>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <ul className="divide-y divide-slate-100">
            {all.map((l) => (
              <li
                key={l.key}
                className="flex items-center justify-between px-4 py-2.5 text-sm"
              >
                <span className={l.retired ? "text-slate-400" : "text-slate-800"}>
                  {l.name}
                  {l.retired && " — retired"}
                </span>
                <form action={setRetired}>
                  <input type="hidden" name="key" value={l.key} />
                  <input
                    type="hidden"
                    name="retired"
                    value={l.retired ? "0" : "1"}
                  />
                  <button
                    type="submit"
                    className="text-xs text-slate-600 underline underline-offset-2 hover:text-slate-900"
                  >
                    {l.retired ? "Restore" : "Retire"}
                  </button>
                </form>
              </li>
            ))}
          </ul>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Retiring keeps every sheet already recorded against a location intact
          and printable; it only stops the location appearing on new ones.
        </p>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Add a location
        </h2>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <AddLocationForm sites={siteList} />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Where locations apply
        </h2>
        <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
          <p className="text-slate-700">
            <span className="font-medium">One row per location:</span>{" "}
            {rowScoped.map((f) => f.title).join(", ") || "none"}
          </p>
          <p className="mt-2 text-slate-700">
            <span className="font-medium">A separate sheet per location:</span>{" "}
            {sheetScoped.map((f) => f.title).join(", ") || "none"}
          </p>
          <p className="mt-3 text-xs text-slate-500">
            Every other format covers the laboratory as a whole and keeps a
            single sheet, which is how NDC-DI defines them.
          </p>
        </div>
      </section>
    </div>
  );
}

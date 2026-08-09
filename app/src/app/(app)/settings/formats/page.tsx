import { requireStaff } from "@/lib/auth";
import { ALL_FORMS } from "@/lib/forms/registry";
import { formLabels } from "@/lib/config";
import { LabelEditor } from "./label-editor";

/**
 * Format configuration.
 *
 * Three of the DI 6 maintenance schedules and the temperature form are printed
 * with blank rows in the master document — no activity is named, so there is
 * nothing for a technician to record against. The laboratory has to decide
 * what those rows say. This screen is where that decision is captured, and it
 * is deliberately visible rather than hidden in a configuration file, because
 * the decision is itself a quality record.
 */
export default async function FormatSettingsPage() {
  await requireStaff();

  const configurable = ALL_FORMS.map((spec) => {
    const editable = spec.bands.flatMap((band) =>
      band.rows
        .filter((r) => r.editableLabel)
        .map((r) => ({ band: band.heading, bandKey: band.key, row: r })),
    );
    return { spec, editable, labels: formLabels(spec.id) };
  }).filter((x) => x.editable.length > 0);

  return (
    <div className="max-w-4xl p-6">
      <h1 className="text-2xl font-semibold text-slate-900">
        Format configuration
      </h1>
      <p className="mt-1 text-sm text-slate-600">
        These formats are printed in NDC-DI Issue IV with rows but no activity
        names. Define what each row records; the text you enter appears on the
        printed sheet in the position the blank row occupies.
      </p>

      <div className="mt-8 space-y-6">
        {configurable.map(({ spec, editable, labels }) => {
          const undefinedCount = editable.filter(
            (e) => !labels[e.row.key],
          ).length;
          return (
            <section
              key={spec.id}
              id={spec.id}
              className="scroll-mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white"
            >
              <div className="flex items-start justify-between gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">
                    {spec.title}
                  </h2>
                  <p className="mt-0.5 text-xs text-slate-500">
                    NDC/DI/{spec.clause} · Page {spec.pageOfClause} of clause{" "}
                    {spec.clause} · source page {spec.sourcePage}
                  </p>
                </div>
                {undefinedCount > 0 ? (
                  <span className="shrink-0 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
                    {undefinedCount} undefined
                  </span>
                ) : (
                  <span className="shrink-0 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                    Defined
                  </span>
                )}
              </div>
              <LabelEditor
                formId={spec.id}
                rows={editable.map((e) => ({
                  key: e.row.key,
                  band: e.band,
                  placeholder:
                    e.row.label ||
                    (spec.id === "temperature-humidity-monitoring"
                      ? "e.g. Reagent fridge, Room, Deep freezer"
                      : "e.g. Surface cleaning"),
                  current: labels[e.row.key] ?? "",
                }))}
              />
            </section>
          );
        })}
      </div>
    </div>
  );
}

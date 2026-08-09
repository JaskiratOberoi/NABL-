import Link from "next/link";
import { formsByClause } from "@/lib/forms/registry";
import { formStatus, type BandState } from "@/lib/status";
import { formLabels } from "@/lib/config";
import { periodKey } from "@/lib/sheets";

/**
 * Today.
 *
 * The outstanding-work view, grouped by sub-clause so it reads the same way as
 * the master document and the rest of the platform.
 */
export default async function TodayPage() {
  const now = new Date();
  const groups = formsByClause().map((group) => ({
    ...group,
    items: group.forms.map((spec) =>
      formStatus(spec, now, "main", formLabels(spec.id)),
    ),
  }));

  const all = groups.flatMap((g) => g.items);
  const outstanding = all.filter((s) => s.state === "outstanding").length;
  const partial = all.filter((s) => s.state === "partial").length;
  const complete = all.filter((s) => s.state === "complete").length;
  const unconfigured = all.filter((s) => s.needsConfiguration);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-slate-900">Today</h1>
        <p className="mt-1 text-sm text-slate-600">
          Records due on{" "}
          {now.toLocaleDateString("en-GB", {
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
          , grouped by sub-clause of NDC-DI.
        </p>
      </div>

      <div className="mb-6 grid grid-cols-3 gap-4">
        <Stat label="Outstanding" value={outstanding} tone="outstanding" />
        <Stat label="Part complete" value={partial} tone="partial" />
        <Stat label="Complete" value={complete} tone="complete" />
      </div>

      {unconfigured.length > 0 && (
        <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4">
          <h2 className="text-sm font-semibold text-amber-900">
            {unconfigured.length} format
            {unconfigured.length === 1 ? "" : "s"} cannot be completed yet
          </h2>
          <p className="mt-1 text-sm text-amber-800">
            NDC-DI prints these schedules with no activities named, so there is
            nothing for staff to record against. Define the activities before
            the format goes into use.
          </p>
          <ul className="mt-3 space-y-1">
            {unconfigured.map((s) => (
              <li key={s.spec.id}>
                <Link
                  href={`/settings/formats#${s.spec.id}`}
                  className="text-sm font-medium text-amber-900 underline underline-offset-2"
                >
                  {s.spec.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="space-y-6">
        {groups.map((group) => (
          <section
            key={group.clause}
            className="overflow-hidden rounded-lg border border-slate-200 bg-white"
          >
            <div className="flex items-baseline gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-900">
                {group.docNo}
              </h2>
              <span className="text-sm text-slate-600">{group.shortTitle}</span>
            </div>
            <ul className="divide-y divide-slate-100">
              {group.items.map((status) => (
                <li key={status.spec.id}>
                  <Link
                    href={`/forms/${status.spec.id}`}
                    className="flex items-center gap-4 px-4 py-3 hover:bg-slate-50"
                  >
                    <StateDot state={status.state} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-slate-900">
                        {status.spec.title}
                      </div>
                      <div className="mt-0.5 text-xs text-slate-500">
                        Page {status.spec.pageOfClause} of clause{" "}
                        {status.spec.clause} · {periodKey(status.spec, now)}
                        {status.state === "partial" &&
                          summariseMissing(status.bands)}
                      </div>
                    </div>
                    <StateLabel state={status.state} />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

function summariseMissing(
  bands: { state: BandState; missing: string[] }[],
): string {
  const missing = bands.flatMap((b) => b.missing);
  if (missing.length === 0) return "";
  const shown = missing.slice(0, 2).join(", ");
  const more = missing.length > 2 ? ` and ${missing.length - 2} more` : "";
  return ` · outstanding: ${shown}${more}`;
}

const TONES: Record<BandState, { dot: string; text: string; label: string }> = {
  outstanding: {
    dot: "bg-red-500",
    text: "text-red-700 bg-red-50",
    label: "Outstanding",
  },
  partial: {
    dot: "bg-amber-500",
    text: "text-amber-800 bg-amber-50",
    label: "Part complete",
  },
  complete: {
    dot: "bg-emerald-500",
    text: "text-emerald-700 bg-emerald-50",
    label: "Complete",
  },
  notDue: {
    dot: "bg-slate-300",
    text: "text-slate-500 bg-slate-50",
    label: "Not due today",
  },
};

function StateDot({ state }: { state: BandState }) {
  return (
    <span
      className={`h-2.5 w-2.5 shrink-0 rounded-full ${TONES[state].dot}`}
      aria-hidden
    />
  );
}

function StateLabel({ state }: { state: BandState }) {
  return (
    <span
      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${TONES[state].text}`}
    >
      {TONES[state].label}
    </span>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: BandState;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-2">
        <StateDot state={tone} />
        <span className="text-sm text-slate-600">{label}</span>
      </div>
      <div className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">
        {value}
      </div>
    </div>
  );
}

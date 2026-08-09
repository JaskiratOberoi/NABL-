import Link from "next/link";
import { notFound } from "next/navigation";
import { requireStaff } from "@/lib/auth";
import { db } from "@/lib/db";
import { formLabels } from "@/lib/config";
import { clauseShortTitle, getForm } from "@/lib/forms/registry";
import { FormSheet } from "@/components/form/sheet";
import type { SignatureLookup } from "@/components/form/cells";
import {
  getOrCreateSheet,
  listPeriods,
  periodKey,
  periodLabel,
  sheetAudit,
} from "@/lib/sheets";
import { DayEntry } from "./day-entry";
import { SlotEntry } from "./slot-entry";

export default async function FormPage({
  params,
  searchParams,
}: {
  params: Promise<{ formId: string }>;
  searchParams: Promise<{ period?: string; site?: string; day?: string }>;
}) {
  const staff = await requireStaff();
  const { formId } = await params;
  const query = await searchParams;

  const spec = getForm(formId);
  if (!spec) notFound();

  const now = new Date();
  const period = query.period ?? periodKey(spec, now);
  const site = query.site ?? "main";
  const day = query.day ? Number(query.day) : now.getDate();

  const sheet = getOrCreateSheet(spec.id, period, site);
  const labels = formLabels(spec.id);
  const { lookup, names } = staffDirectory();
  const audit = sheetAudit(sheet.id, 12);
  const periods = listPeriods(spec.id, site);

  const dailyBands = spec.bands.filter(
    (b) => b.layout === "dayGrid" || b.layout === "fullMonthGrid",
  );
  const slotBands = spec.bands.filter((b) => b.layout === "slots");
  const ledgerBands = spec.bands.filter(
    (b) => b.layout === "ledger" || b.layout === "pairedLedger",
  );

  // Only the half of the month that contains the selected day is being filled.
  const activeDaily = dailyBands.filter(
    (b) => day >= (b.dayFrom ?? 1) && day <= (b.dayTo ?? 31),
  );

  return (
    <div className="flex min-w-0">
      <div className="min-w-0 flex-1 p-6">
        <nav className="mb-2 text-xs text-slate-500">
          <Link
            href={`/clause/${spec.clause}`}
            className="hover:text-slate-900 hover:underline"
          >
            NDC/DI/{spec.clause} — {clauseShortTitle(spec.clause)}
          </Link>
          <span className="mx-1.5">/</span>
          <span>
            Page {spec.pageOfClause} of clause {spec.clause}
          </span>
        </nav>

        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">
              {spec.title}
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              {spec.recordingSchedule}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <PeriodPicker
              formId={spec.id}
              current={period}
              periods={periods}
              site={site}
            />
            <Link
              href={`/print/${spec.id}/${period}?site=${site}`}
              target="_blank"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Print sheet
            </Link>
          </div>
        </div>

        {spec.bands.some((b) =>
          b.rows.some((r) => r.editableLabel && !labels[r.key]),
        ) && (
          <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
            NDC-DI prints this schedule with its activity rows blank.{" "}
            <Link
              href={`/settings/formats#${spec.id}`}
              className="font-medium underline underline-offset-2"
            >
              Define the activities
            </Link>{" "}
            before staff record against it.
          </div>
        )}

        {activeDaily.length > 0 && (
          <section className="mb-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900">
                Daily entry
              </h2>
              <DayPicker formId={spec.id} period={period} site={site} day={day} />
            </div>
            <div className="space-y-4">
              {activeDaily.map((band) => (
                <DayEntry
                  key={band.key}
                  formId={spec.id}
                  period={period}
                  site={site}
                  band={band}
                  day={day}
                  data={sheet.data}
                  labels={labels}
                  currentStaffCode={staff.code}
                  staffNames={names}
                />
              ))}
            </div>
          </section>
        )}

        {slotBands.length > 0 && (
          <section className="mb-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Periodic activities
            </h2>
            {slotBands.map((band) => (
              <SlotEntry
                key={band.key}
                formId={spec.id}
                period={period}
                site={site}
                band={band}
                data={sheet.data}
                labels={labels}
                staffNames={names}
                today={now.toLocaleDateString("en-GB")}
              />
            ))}
          </section>
        )}

        {ledgerBands.length > 0 && (
          <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
            This format is an event ledger. Entries are added as the work
            happens; use the printed sheet for the month and record each run as
            a line.
          </section>
        )}

        <section>
          <h2 className="mb-3 text-sm font-semibold text-slate-900">
            Recent activity on this sheet
          </h2>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            {audit.length === 0 ? (
              <p className="px-4 py-6 text-sm text-slate-500">
                Nothing recorded on this sheet yet.
              </p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {audit.map((entry) => (
                  <li
                    key={entry.id}
                    className="flex items-baseline gap-3 px-4 py-2 text-sm"
                  >
                    <span className="w-36 shrink-0 font-mono text-xs text-slate-500">
                      {entry.at}
                    </span>
                    <span className="w-40 shrink-0 truncate text-slate-800">
                      {entry.staff_name}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-slate-500">
                      {describe(entry.action)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      {/* Live preview of the sheet the entries produce. */}
      <aside className="no-print hidden w-[480px] shrink-0 border-l border-slate-200 bg-slate-700 xl:block">
        <div className="sticky top-0 max-h-dvh overflow-auto">
          <div className="flex items-center justify-between bg-slate-800 px-4 py-2 text-xs text-slate-300">
            <span>Sheet preview — {periodLabel(period)}</span>
            <span>{spec.orientation}</span>
          </div>
          <div
            className="origin-top-left"
            style={{
              transform: "scale(0.55)",
              width: spec.orientation === "landscape" ? "1123px" : "794px",
            }}
          >
            <FormSheet
              spec={spec}
              data={sheet.data}
              header={{ monthLabel: periodLabel(period) }}
              signatures={lookup}
              labels={labels}
            />
          </div>
        </div>
      </aside>
    </div>
  );
}

/** Staff signature images, keyed by code, for rendering the sheet. */
function staffDirectory(): {
  lookup: SignatureLookup;
  names: Record<string, string>;
} {
  const rows = db()
    .prepare("SELECT code, name, initials, signature FROM staff WHERE active = 1")
    .all() as {
    code: string;
    name: string;
    initials: string;
    signature: string | null;
  }[];

  const lookup: SignatureLookup = {};
  const names: Record<string, string> = {};
  for (const r of rows) {
    lookup[r.code] = {
      name: r.name,
      signature: r.signature,
      initials: r.initials || r.code,
    };
    names[r.code] = r.name;
  }
  return { lookup, names };
}

function describe(action: string): string {
  const [kind, band, day] = action.split(":");
  switch (kind) {
    case "day-entry":
      return `Recorded day ${day} (${band})`;
    case "carry-forward":
      return `Carried forward to day ${day} (${band})`;
    case "verify":
      return `Verified day ${day} (${band})`;
    case "slot-entry":
      return `Recorded periodic activity (${band})`;
    case "header-update":
      return "Updated sheet header";
    default:
      return action;
  }
}

function DayPicker({
  formId,
  period,
  site,
  day,
}: {
  formId: string;
  period: string;
  site: string;
  day: number;
}) {
  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  return (
    <form className="flex items-center gap-2" action={`/forms/${formId}`}>
      <input type="hidden" name="period" value={period} />
      <input type="hidden" name="site" value={site} />
      <label htmlFor="day" className="text-xs text-slate-500">
        Day
      </label>
      <select
        id="day"
        name="day"
        defaultValue={day}
        className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
      >
        {days.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
      >
        Go
      </button>
    </form>
  );
}

function PeriodPicker({
  formId,
  current,
  periods,
  site,
}: {
  formId: string;
  current: string;
  periods: string[];
  site: string;
}) {
  const options = periods.includes(current) ? periods : [current, ...periods];
  return (
    <form action={`/forms/${formId}`} className="flex items-center gap-2">
      <input type="hidden" name="site" value={site} />
      <select
        name="period"
        defaultValue={current}
        className="rounded-md border border-slate-300 px-2 py-2 text-sm"
      >
        {options.map((p) => (
          <option key={p} value={p}>
            {periodLabel(p)}
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="rounded-md border border-slate-300 px-2.5 py-2 text-sm text-slate-700 hover:bg-slate-50"
      >
        Open
      </button>
    </form>
  );
}

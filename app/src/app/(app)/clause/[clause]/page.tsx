import Link from "next/link";
import { notFound } from "next/navigation";
import { formsByClause } from "@/lib/forms/registry";
import { formLabels } from "@/lib/config";
import { formStatus } from "@/lib/status";
import { periodKey, periodLabel } from "@/lib/sheets";
import type { ClauseRef } from "@/lib/forms/types";

/**
 * All formats belonging to one sub-clause.
 *
 * This is the view to open in front of an assessor: it lists the sub-clause's
 * record formats in the order they appear in NDC-DI, with the page reference
 * printed on each sheet, and links straight to the filled records.
 */
export default async function ClausePage({
  params,
}: {
  params: Promise<{ clause: string }>;
}) {
  const { clause } = await params;
  const group = formsByClause().find((g) => g.clause === clause);
  if (!group) notFound();

  const now = new Date();

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="text-sm font-medium text-slate-500">{group.docNo}</div>
        <h1 className="mt-0.5 text-2xl font-semibold text-slate-900">
          {group.shortTitle}
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          {group.title} · {group.forms.length} record format
          {group.forms.length === 1 ? "" : "s"} in the platform
        </p>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="px-4 py-2.5 font-semibold">Page</th>
              <th className="px-4 py-2.5 font-semibold">Format</th>
              <th className="px-4 py-2.5 font-semibold">Recording schedule</th>
              <th className="px-4 py-2.5 font-semibold">Current sheet</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {group.forms.map((spec) => {
              const status = formStatus(
                spec,
                now,
                "main",
                formLabels(spec.id),
              );
              const period = periodKey(spec, now);
              return (
                <tr key={spec.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {spec.pageOfClause}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/forms/${spec.id}`}
                      className="font-medium text-slate-900 hover:underline"
                    >
                      {spec.title}
                    </Link>
                    <div className="mt-0.5 text-xs text-slate-400">
                      Source: DI 6 page {spec.sourcePage} ·{" "}
                      {spec.sourcePageSize} original
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {spec.recordingSchedule.replace(/^\(|\)$/g, "")}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {periodLabel(period)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        status.state === "complete"
                          ? "bg-emerald-50 text-emerald-700"
                          : status.state === "partial"
                            ? "bg-amber-50 text-amber-800"
                            : status.state === "outstanding"
                              ? "bg-red-50 text-red-700"
                              : "bg-slate-50 text-slate-500"
                      }`}
                    >
                      {status.state === "notDue" ? "Not due today" : status.state}
                    </span>
                    <Link
                      href={`/print/${spec.id}/${period}`}
                      target="_blank"
                      className="ml-3 text-xs text-slate-600 underline underline-offset-2 hover:text-slate-900"
                    >
                      Print
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function generateStaticParams(): { clause: ClauseRef }[] {
  return formsByClause().map((g) => ({ clause: g.clause }));
}

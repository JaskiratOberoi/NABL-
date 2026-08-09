import Link from "next/link";
import { redirect } from "next/navigation";
import { currentStaff } from "@/lib/auth";
import { formsByClause } from "@/lib/forms/registry";
import { signOut } from "../login/actions";

/**
 * Application shell.
 *
 * Navigation is organised by sub-clause of NDC-DI, not by how often a form is
 * filled, so that the platform mirrors the master document. An assessor asked
 * to see the records behind clause 6.4 finds one heading with everything
 * beneath it, in the order the document itself uses.
 */
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const staff = await currentStaff();
  if (!staff) redirect("/login");

  const groups = formsByClause();

  return (
    <div className="flex min-h-dvh">
      <aside className="no-print w-72 shrink-0 border-r border-slate-200 bg-white">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/ndc-logo.png" alt="" className="h-8 w-8" />
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold leading-tight">
              Noble Diagnostic Centre
            </div>
            <div className="text-xs text-slate-500">Quality Records</div>
          </div>
        </div>

        <nav className="px-3 py-4">
          <Link
            href="/"
            className="mb-4 block rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Today
          </Link>

          <div className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            NDC-DI Issue IV — Clause 6
          </div>

          {groups.map((group) => (
            <div key={group.clause} className="mb-5">
              <Link
                href={`/clause/${group.clause}`}
                className="block rounded-md px-3 py-1.5 hover:bg-slate-100"
              >
                <div className="text-sm font-semibold text-slate-900">
                  {group.docNo}
                </div>
                <div className="text-xs leading-snug text-slate-500">
                  {group.shortTitle}
                </div>
              </Link>
              <ul className="mt-1 space-y-0.5">
                {group.forms.map((form) => (
                  <li key={form.id}>
                    <Link
                      href={`/forms/${form.id}`}
                      className="flex items-baseline gap-2 rounded px-3 py-1 text-[13px] text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    >
                      <span className="w-6 shrink-0 text-right font-mono text-[11px] text-slate-400">
                        {form.pageOfClause}
                      </span>
                      <span className="min-w-0 flex-1 leading-snug">
                        {titleCase(form.title)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div className="mt-6 border-t border-slate-200 pt-4">
            <Link
              href="/settings/staff"
              className="block rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
            >
              Staff and signatures
            </Link>
            <Link
              href="/settings/locations"
              className="block rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
            >
              Monitored locations
            </Link>
            <Link
              href="/settings/formats"
              className="block rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
            >
              Format configuration
            </Link>
          </div>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="no-print flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
          <div className="text-sm text-slate-500">
            {new Date().toLocaleDateString("en-GB", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium text-slate-900">
                {staff.name}
              </div>
              <div className="text-xs text-slate-500">
                {staff.designation || staff.code}
              </div>
            </div>
            <form action={signOut}>
              <button
                type="submit"
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
              >
                Sign out
              </button>
            </form>
          </div>
        </header>

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}

/** "FACILITY ROUND CHECKLIST" reads better in the sidebar as sentence case. */
function titleCase(s: string): string {
  return s
    .toLowerCase()
    .replace(/(^|[\s–\-/])([a-z])/g, (_, p, c) => p + c.toUpperCase())
    .replace(/\bCfx\b/i, "CFX")
    .replace(/\bBiolis 30i\b/i, "Biolis 30i")
    .replace(/\bX3\b/i, "X3");
}

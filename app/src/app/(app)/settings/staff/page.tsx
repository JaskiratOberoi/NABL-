import { requireStaff } from "@/lib/auth";
import { db } from "@/lib/db";
import { AddStaffForm, ChangePasswordForm, SignatureUpload } from "./forms";
import { setActive } from "./actions";

export default async function StaffSettingsPage() {
  const actor = await requireStaff();
  const canManage =
    actor.role === "quality-manager" || actor.role === "director";

  const staff = db()
    .prepare(
      `SELECT id, code, name, designation, department, initials, role, active,
              signature IS NOT NULL AS has_signature
       FROM staff ORDER BY active DESC, name`,
    )
    .all() as {
    id: number;
    code: string;
    name: string;
    designation: string;
    department: string;
    initials: string;
    role: string;
    active: number;
    has_signature: number;
  }[];

  const me = db()
    .prepare("SELECT signature FROM staff WHERE id = ?")
    .get(actor.id) as { signature: string | null };

  return (
    <div className="max-w-4xl p-6">
      <h1 className="text-2xl font-semibold text-slate-900">
        Staff and signatures
      </h1>
      <p className="mt-1 text-sm text-slate-600">
        The signature stored against an account is the mark printed in the Done
        By and Verified By columns of every record that account signs.
      </p>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Your signature
        </h2>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-4 flex items-center gap-6">
            <div className="flex h-16 w-44 items-center justify-center rounded border border-dashed border-slate-300 bg-slate-50">
              {me.signature ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={me.signature}
                  alt="Your stored signature"
                  className="max-h-14 max-w-40 object-contain"
                />
              ) : (
                <span className="text-xs text-slate-400">None stored</span>
              )}
            </div>
            <p className="flex-1 text-sm text-slate-600">
              Sign a sheet of white paper, photograph or scan it, and crop
              closely. PNG with a transparent or white background works best.
              Under 512 KB.
            </p>
          </div>
          <SignatureUpload />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Your password
        </h2>
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <ChangePasswordForm />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">
          Staff register
        </h2>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-2.5 font-semibold">Code</th>
                <th className="px-4 py-2.5 font-semibold">Name</th>
                <th className="px-4 py-2.5 font-semibold">Designation</th>
                <th className="px-4 py-2.5 font-semibold">Role</th>
                <th className="px-4 py-2.5 font-semibold">Signature</th>
                {canManage && <th className="px-4 py-2.5" />}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {staff.map((s) => (
                <tr key={s.id} className={s.active ? "" : "opacity-50"}>
                  <td className="px-4 py-2.5 font-mono text-xs">{s.code}</td>
                  <td className="px-4 py-2.5 font-medium text-slate-900">
                    {s.name}
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">
                    {s.designation || "—"}
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">{s.role}</td>
                  <td className="px-4 py-2.5">
                    {s.has_signature ? (
                      <span className="text-emerald-700">Stored</span>
                    ) : (
                      <span className="text-amber-700">Not captured</span>
                    )}
                  </td>
                  {canManage && (
                    <td className="px-4 py-2.5 text-right">
                      <form action={setActive}>
                        <input type="hidden" name="id" value={s.id} />
                        <input
                          type="hidden"
                          name="active"
                          value={s.active ? "0" : "1"}
                        />
                        <button
                          type="submit"
                          className="text-xs text-slate-600 underline underline-offset-2 hover:text-slate-900"
                        >
                          {s.active ? "Deactivate" : "Reactivate"}
                        </button>
                      </form>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {canManage && (
        <section className="mt-8">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">
            Add a staff member
          </h2>
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <AddStaffForm />
            <p className="mt-4 text-xs text-slate-500">
              Give the person their staff code and initial password directly.
              They sign in and upload their own signature.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}

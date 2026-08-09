"use client";

import { useActionState } from "react";
import { addStaff, changePassword, uploadSignature } from "./actions";

const field =
  "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900";
const label = "block text-xs font-medium text-slate-700";

export function SignatureUpload() {
  return (
    <form action={uploadSignature} className="flex items-center gap-3">
      <input
        type="file"
        name="signature"
        accept="image/png,image/jpeg,image/webp"
        required
        className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:text-white hover:file:bg-slate-800"
      />
      <button
        type="submit"
        className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
      >
        Upload
      </button>
    </form>
  );
}

export function ChangePasswordForm() {
  const [state, action, pending] = useActionState(changePassword, {});
  return (
    <form action={action} className="flex flex-wrap items-end gap-3">
      <div className="w-56">
        <label htmlFor="password" className={label}>
          New password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          className={field}
        />
      </div>
      <div className="w-56">
        <label htmlFor="confirm" className={label}>
          Confirm
        </label>
        <input
          id="confirm"
          name="confirm"
          type="password"
          autoComplete="new-password"
          className={field}
        />
      </div>
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
      >
        Change
      </button>
      {state?.error && (
        <p className="w-full text-sm text-red-700">{state.error}</p>
      )}
      {state?.ok && (
        <p className="w-full text-sm text-emerald-700">{state.ok}</p>
      )}
    </form>
  );
}

export function AddStaffForm() {
  const [state, action, pending] = useActionState(addStaff, {});
  return (
    <form action={action} className="grid grid-cols-3 gap-3">
      <div>
        <label htmlFor="code" className={label}>
          Staff code
        </label>
        <input id="code" name="code" className={`${field} uppercase`} />
      </div>
      <div className="col-span-2">
        <label htmlFor="name" className={label}>
          Full name
        </label>
        <input id="name" name="name" className={field} />
      </div>
      <div>
        <label htmlFor="initials" className={label}>
          Initials
        </label>
        <input id="initials" name="initials" className={field} />
      </div>
      <div>
        <label htmlFor="designation" className={label}>
          Designation
        </label>
        <input id="designation" name="designation" className={field} />
      </div>
      <div>
        <label htmlFor="department" className={label}>
          Department
        </label>
        <input id="department" name="department" className={field} />
      </div>
      <div>
        <label htmlFor="role" className={label}>
          Role
        </label>
        <select id="role" name="role" className={field} defaultValue="technician">
          <option value="technician">Technician</option>
          <option value="supervisor">Supervisor</option>
          <option value="quality-manager">Quality Manager</option>
          <option value="director">Lab Director</option>
        </select>
      </div>
      <div>
        <label htmlFor="newpass" className={label}>
          Initial password
        </label>
        <input
          id="newpass"
          name="password"
          type="text"
          autoComplete="off"
          className={field}
        />
      </div>
      <div className="flex items-end">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
        >
          Add
        </button>
      </div>
      {state?.error && (
        <p className="col-span-3 text-sm text-red-700">{state.error}</p>
      )}
      {state?.ok && (
        <p className="col-span-3 text-sm text-emerald-700">{state.ok}</p>
      )}
    </form>
  );
}

"use client";

import { useActionState } from "react";
import { signIn } from "./actions";

export default function LoginPage() {
  const [state, action, pending] = useActionState(signIn, {});

  return (
    <main className="flex min-h-dvh items-center justify-center bg-slate-100 p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/brand/ndc-logo.png"
            alt=""
            className="mx-auto mb-4 h-14 w-14"
          />
          <h1 className="text-xl font-semibold text-slate-900">
            Noble Diagnostic Centre
          </h1>
          <p className="mt-1 text-sm text-slate-600">Quality Records</p>
        </div>

        <form
          action={action}
          className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
        >
          <label
            htmlFor="code"
            className="block text-sm font-medium text-slate-700"
          >
            Staff code
          </label>
          <input
            id="code"
            name="code"
            autoComplete="username"
            autoCapitalize="characters"
            autoFocus
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm uppercase outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
          />

          <label
            htmlFor="password"
            className="mt-4 block text-sm font-medium text-slate-700"
          >
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900"
          />

          {state?.error && (
            <p
              role="alert"
              className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {state.error}
            </p>
          )}

          <button
            type="submit"
            disabled={pending}
            className="mt-6 w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-60"
          >
            {pending ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">
          Entries are recorded against your account. Do not sign in on behalf of
          a colleague.
        </p>
      </div>
    </main>
  );
}

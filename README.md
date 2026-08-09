# NABL 2026 — Noble Diagnostic Centre

Reassessment preparation for the September 2026 NABL renewal, and the quality
record platform built from the laboratory's own documented information.

## Layout

```
CLAUDE.md                      project brief
README.md                      this file
assets/brand/                  logo and approval signatures lifted from NDC-DI
docs/legacy/                   NDC-DI Issue IV as supplied — DI 1–5, 6, 7, 8
docs/reference/                findings, NABL criteria, source defects
docs/tracker/                  the live audit readiness workbook
app/                           the quality record platform
```

## The platform

A web application that captures the daily quality records required by
`NDC/DI/6` and prints them as controlled copies indistinguishable in format
from the pages of NDC-DI they replace.

**Covers all 43 record formats in DI 6**, across all seven sub-clauses:

| Sub-clause | Formats |
|---|---|
| NDC/DI/6.2 — Personnel | 14 of 14 |
| NDC/DI/6.3 — Facilities and environmental conditions | 7 of 7 |
| NDC/DI/6.4 — Handling equipment | 13 of 13 |
| NDC/DI/6.5 — Equipment calibration | 1 of 1 |
| NDC/DI/6.6 — Reagents and consumables | 2 of 2 |
| NDC/DI/6.7 — Service agreements | 1 of 1 |
| NDC/DI/6.8 — Externally provided products and services | 5 of 5 |

Navigation is organised by sub-clause and each format carries its
"Page N of clause X" reference, so a printed record traces directly back to the
master document.

### Running it

Requires **Node.js 22 or later**. Nothing else — no database server, no native
modules to compile.

```bash
cd app && npm install && npm run seed
```

The seed prints the initial staff code and password. Then:

```bash
cd app && npm run build && npm start
```

The server listens on all interfaces on port 3000, so bench terminals reach it
at `http://<server-ip>:3000`. For day-to-day development use `npm run dev`.

Data lives in `app/data/ndc-qms.db`, a single SQLite file. **Back it up**: it
holds every quality record the laboratory has entered. Set `NDC_DATA_DIR` to
put it somewhere else, such as a mapped drive that is already backed up.

### First-run checklist

1. Sign in as `QM` and change the password immediately.
2. Upload your signature under **Staff and signatures**.
3. Add each member of staff; they sign in and upload their own signature.
4. Work through **Format configuration** — four formats print with blank
   activity rows in NDC-DI and cannot be used until the laboratory defines
   what they record. See `docs/reference/DI6-source-defects.md`.

### How it works

- **`app/src/lib/forms/specs/`** — each record format described as data: page
  geometry, bands, rows, columns, footer references. Adding the remaining DI 6
  formats, or DI 7 and DI 8, means writing a spec rather than a component.
- **`app/src/components/form/`** — one renderer drives both the on-screen
  preview and the printed page, so what a user approves is what prints.
- **`app/src/lib/status.ts`** — works out what has not been recorded today.
- **`app/src/lib/sheets.ts`** — writes entries and their attribution in one
  transaction, so a saved value cannot exist without a record of who set it.

### Records and attribution

Every entry is attributed to the signed-in user and written to an append-only
audit log with a timestamp. The staff signature image printed in the Done By
column is the visible mark; the audit log is the evidence behind it.

Carry-forward ("same as yesterday") copies the previous day's entries but still
requires a person to press the button, is attributed to them, and is written to
the audit log under its own action name so a reviewer can see which days were
entered that way.

The Quality Manager and Lab Director signatures in the footer attest to the
*format*, not to any day's entries — the same as on the paper original.

### Before the assessment

The footer prints **Issue No. IV, Issue Date 01 04 2024, Rev No. 00**. When the
set is re-issued as Issue V — finding X-01, the highest-leverage action
available — update the issue block in
`app/src/components/form/footer.tsx` and the affected specs, or the platform
will keep printing superseded document control data onto live records.

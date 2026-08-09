# Defects found in NDC/DI/6 while transcribing the record formats

Recorded 09 August 2026, while building the quality record platform from
`docs/legacy/DI 6.pdf`. These are properties of the master document itself, not
of the software. Each is a finding an assessor could raise against NDC-DI Issue
IV, and each should be resolved when the set is re-issued as Issue V.

None of these appear in `NABL-2026-findings.md`; they are additional.

---

## S-01 — Three maintenance schedules name no maintenance activities (MAJOR)

`NDC/DI/6.4` pages 36, 38 and 39 print a maintenance schedule with a full day
grid, Done By and Verified By rows, and WEEKLY / MONTHLY / 6 MONTHLY bands — but
**every activity row is blank**. No task is specified, so there is nothing for a
technician to perform or record.

| Page | Format | Instrument | Blank rows |
|---|---|---|---|
| 36 | MAINTENANCE SCHEDULE – BIOLIS 30i | Agappe/Tokyo Biolis 30i, clinical chemistry | 7 daily, 4 weekly, 1 yearly |
| 38 | MAINTENANCE SCHEDULE – PROLYTE | Prolyte, electrolytes | 5 daily, 3 weekly, 2 monthly, 2 yearly |
| 39 | MAINTENANCE SCHEDULE – MINDRAY 5380 | Mindray BC-5380, haematology | 5 daily, 4 weekly, 6 monthly, 6 six-monthly |

These are three of the laboratory's four principal analysers. A schedule that
specifies no activity cannot be complied with, and a completed sheet would show
ticks against nothing.

`NDC/DI/6.4` clause 5.4 A states the laboratory follows manufacturer preventive
maintenance schedules; the activity lists should be taken from each
instrument's operator manual and entered against these rows.

**Handled in the platform:** these rows are configurable under Format
configuration, and the affected formats are flagged on the dashboard as unable
to be completed until the activities are defined.

## S-02 — Haematology acceptance limits printed on the electrolyte analyser schedule (MINOR)

`NDC/DI/6.4` page 38, MAINTENANCE SCHEDULE – PROLYTE, carries the footnote:

> Background Check: WBC: < 0.03 X 10³ /µL, RBC: < 0.03 X 10⁶ /µL, Hb: < 0.3 g/dl, PLT: < 7 X 10³ /µL

These are haematology background-count limits and belong to the Mindray
BC-5380, not to an electrolyte analyser measuring Na⁺/K⁺/Cl⁻. The footnote has
been copied onto the wrong format. The Prolyte schedule carries no acceptance
criteria of its own.

## S-03 — Temperature form does not name the locations it monitors (MAJOR)

`NDC/DI/6.3` page 10, TEMPERATURE/ HUMIDITY MONITORING FORM, provides four
Location rows, each split morning and evening — but the Location column is
blank on the master format. The acceptance-criteria footnote names six distinct
storage conditions (fridge, freezer, room, incubator, humidity, ultra deep
freezer), which is more conditions than the form has rows.

The laboratory holds at minimum: reagent fridge, two −20 °C freezers, a −80 °C
deep freezer, incubator, and ambient room. That is six monitored points against
four available rows, so the format cannot record everything the criteria
require, even once the locations are named.

**Recommendation:** state the monitored locations on the format and add rows so
that every point named in the acceptance criteria has one. Relates to the
continuous-logging finding already recorded in `NABL-2026-findings.md`.

## S-04 — Record formats are not on a consistent paper size (OFI)

Every clause 6.3 format is US Letter (612 × 792 pt); every clause 6.4 format is
A4 (595 × 842 pt).

| Clause | Pages | Size |
|---|---|---|
| 6.3 | 33–40 | US Letter |
| 6.4 | 73, 75–84 | A4 |

Almost certainly an artefact of the authoring template rather than a decision.
Printing the set on the A4 stock an Indian laboratory holds will scale or clip
the clause 6.3 formats. Standardise on A4 at Issue V.

**Handled in the platform:** all formats render A4. The original size is
recorded against each format for traceability.

## S-05 — Footer strap line is inconsistent within a clause (MINOR)

Most pages read "Documented Information – …". Three do not:

| Page | Strap line printed |
|---|---|
| 6.2 p16 | Policy and procedure – Personnel |
| 6.4 p36 | Policy and procedure – Handling equipment |
| 6.4 p37 | Policy and procedure – Handling equipment |

`NDC/DI/6.3` page 12 additionally prints the document number as
`NDC / DI/ 6.3` rather than `NDC / DI / 6.3`.

Trivial individually, but a document-control observation: it shows the pages
were edited separately rather than generated from one controlled template.

**Handled in the platform:** reproduced verbatim, so a printed sheet matches the
page it replaces. Correct these at Issue V and the specs should be updated to
match.

## S-06 — Recording schedule lines have unclosed brackets (OFI)

`NDC/DI/6.3` page 7: `(Recording schedule – Daily, Weekly, Monthly, Quarterly, 6 Monthly`
`NDC/DI/6.3` page 12: `(Recording schedule – Daily, Weekly, Fortnightly, Monthly`

Both are missing the closing parenthesis. Reproduced verbatim in the platform.

## S-07 — Every page carries Rev No. 00 and a null revision date (MAJOR — already recorded)

Consistent with finding X-01. Noted here only because it is visible on all 18
formats reproduced, and because the platform prints Issue IV / 01 04 2024 /
Rev 00 on every sheet. **When the set is re-issued as Issue V, the issue block
in `src/components/form/footer.tsx` must be updated**, or the platform will keep
printing superseded document control data onto live records.

## S-08 — A record format carries another organisation's document number (MAJOR)

`NDC/DI/6.7` page 6, SERVICE AGREEMENT DEVIATION FORM, prints:

> Doc No. **MMD / P&P / 6.7**

Every other page in the set reads `NDC / DI / <clause>`. This one carries a
different organisation's prefix and a different document-type code (`P&P`
rather than `DI`), which is direct evidence that the format was copied from
another laboratory's manual and never renumbered.

An assessor who spots this will reasonably ask what else in the set was adopted
without review — and given X-02, the answer is not comfortable. Correct at
Issue V.

**Handled in the platform:** reproduced verbatim, so the printed sheet matches
the controlled format. Change the spec's `docNoOverride` once corrected.

## S-09 — The outside collection slip is referenced but does not exist (MAJOR)

`NDC/DI/6.7` page 3 states:

> All sample received from home / hospital accompany the outside collection slip
> as given in section 6

Section 6 of `NDC/DI/6.7` lists exactly one format — the Service Agreement
Deviation Form. There is no outside collection slip anywhere in the document.

This is the same failure mode as finding C-01 (`NDC/DI/7.4.2` listed in the
contents but absent): a procedure requires a record for which no format exists,
so the requirement cannot be met as written. Given the collection centre at
WZ-405A/A and finding X-03, a collection slip is exactly the record an assessor
will ask to see.

The same section's table gives the deviation form as "Page No. 5" while the
page itself is footed "Page 6 of clause 6.7".

---

## What this means for the platform

The platform reproduces the formats as they stand in Issue IV, including the
defects above, so that a sheet it prints is the same controlled document the
laboratory is currently accredited against. Where a defect makes a format
unusable (S-01, S-03) the missing content is configurable rather than invented.

Once Issue V is drafted, the specs in `app/src/lib/forms/specs/` and the issue
block in the footer component are the two places to update.

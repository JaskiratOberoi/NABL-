import type {
  ActivityRow,
  Band,
  CellKind,
  EntryData,
  LedgerColumn,
} from "@/lib/forms/types";
import { dayKey } from "@/lib/forms/types";
import { CellValue, type SignatureLookup } from "./cells";

const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JLY", "AUG", "SEP", "OCT", "NOV", "DEC",
];

export interface BandProps {
  band: Band;
  data: EntryData;
  signatures: SignatureLookup;
  /** Overrides for rows whose labels the laboratory configures. */
  labels?: Record<string, string>;
}

/**
 * Renders one table.
 *
 * A run is a lead band plus any bands marked `continues`, which the source
 * prints as further heading rows inside the same table rather than as new
 * tables of their own.
 */
export interface BandRunProps extends Omit<BandProps, "band"> {
  bands: Band[];
}

export function BandTable({ bands, ...rest }: BandRunProps) {
  const lead = bands[0];
  switch (lead.layout) {
    case "dayGrid":
      return <DayGrid band={lead} {...rest} />;
    case "fullMonthGrid":
      return <FullMonthGrid band={lead} {...rest} />;
    case "slots":
      return <SlotBand bands={bands} {...rest} />;
    case "monthGrid":
      return <MonthGrid bands={bands} {...rest} />;
    case "ledger":
      return <Ledger band={lead} {...rest} />;
    case "pairedLedger":
      return <PairedLedger band={lead} {...rest} />;
    case "halfYearGrid":
      return <HalfYearGrid band={lead} {...rest} />;
    case "fields":
      return <Fields band={lead} {...rest} />;
    case "prose":
      return <Prose band={lead} />;
    case "authGrid":
      return <AuthGrid band={lead} {...rest} />;
  }
}

/** Numbered or plain paragraphs, reproduced verbatim from the source. */
function Prose({ band }: { band: Band }) {
  const paragraphs = band.paragraphs ?? [];
  const Tag = band.numbered ? "ol" : "div";
  return (
    <Tag
      className={band.numbered ? "prose prose--numbered" : "prose"}
      style={
        band.listStyle ? { listStyleType: band.listStyle } : undefined
      }
    >
      {paragraphs.map((text, i) =>
        band.numbered ? (
          <li key={i}>{text}</li>
        ) : (
          <p key={i}>{text}</p>
        ),
      )}
    </Tag>
  );
}

/**
 * The authorization forms.
 *
 * The source lays a long list of activities out as three activity/status
 * column pairs read down each column in turn, which is what this reproduces.
 */
function AuthGrid({ band, data, signatures }: BandProps) {
  const pairs = band.pairColumns ?? 3;
  const rows = band.rows;
  const perColumn = Math.ceil(rows.length / pairs);
  const columns = Array.from({ length: pairs }, (_, c) =>
    rows.slice(c * perColumn, (c + 1) * perColumn),
  );

  return (
    <table className="band">
      <thead>
        <tr>
          {columns.map((_, c) => (
            <Fragmented key={c}>
              <th className="lbl">Activities authorized for</th>
              <th className="lbl">{band.statusLabel ?? "Status"}</th>
            </Fragmented>
          ))}
        </tr>
      </thead>
      <tbody>
        {range(0, perColumn - 1).map((i) => (
          <tr key={i} className="row">
            {columns.map((col, c) => {
              const row = col[i];
              return (
                <Fragmented key={c}>
                  <td className="lbl">{row?.label ?? ""}</td>
                  <td>
                    {row ? (
                      <CellValue
                        kind={row.cell ?? band.cell ?? "text"}
                        value={get(data, band.key, row.key, "v")}
                        signatures={signatures}
                      />
                    ) : null}
                  </td>
                </Fragmented>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/**
 * Labelled fields.
 *
 * Used by the formats that record one subject rather than a month of days —
 * a supplier's registration details, an outsourced laboratory's onsite visit.
 * Blank fields print as a rule, matching the paper form that gets written on.
 */
function Fields({ band, data, signatures }: BandProps) {
  const fields = band.fields ?? [];

  // Consecutive part-width fields share a line, which is how the source sets
  // Phone / Fax / E Mail and Date / Person Visited / Person Contacted.
  const lines: (typeof fields)[] = [];
  for (const f of fields) {
    const last = lines[lines.length - 1];
    const partial = (f.width ?? 1) < 1;
    const lastPartial = last && (last[0].width ?? 1) < 1;
    if (partial && lastPartial && !f.section) {
      const used = last.reduce((sum, x) => sum + (x.width ?? 1), 0);
      if (used + (f.width ?? 1) <= 1.001) {
        last.push(f);
        continue;
      }
    }
    lines.push([f]);
  }

  return (
    <div className="fields">
      {lines.map((line, i) =>
        line[0].photo ? (
          <div key={i} className="fields__photo">
            Please affix your
            <br />
            photograph here
          </div>
        ) : (
        <div key={i} className="fields__item">
          {line[0].section && (
            <div className="fields__section">{line[0].section}</div>
          )}
          {/* A section rule with no label of its own is a heading, not an
              entry, so it draws no line to write on. */}
          {!(line[0].section && !line[0].label) && (
            <div className="fields__row">
              {line.map((f) => (
                <div
                  key={f.key}
                  className="fields__cell"
                  style={{ flexBasis: `${(f.width ?? 1) * 100}%` }}
                >
                  {f.label && <span className="fields__label">{f.label}</span>}
                  {!f.noRule && (
                    <span className="fields__value">
                      <CellValue
                        kind={f.cell ?? "text"}
                        value={get(data, band.key, f.key, "v")}
                        signatures={signatures}
                      />
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
          {line[0].listCount ? (
            <ol className="fields__list">
              {range(1, line[0].listCount).map((n) => (
                <li key={n}>
                  <span className="fields__value">
                    <CellValue
                      kind="text"
                      value={get(data, band.key, line[0].key, `i${n}`)}
                      signatures={signatures}
                    />
                  </span>
                </li>
              ))}
            </ol>
          ) : null}
          {line[0].lines
            ? range(1, line[0].lines).map((n) => (
                <div key={n} className="fields__line">
                  <CellValue
                    kind="text"
                    value={get(data, band.key, line[0].key, `l${n}`)}
                    signatures={signatures}
                  />
                </div>
              ))
            : null}
        </div>
        ),
      )}
    </div>
  );
}

/** Resolves a row's printed label, preferring a lab-configured override. */
function labelOf(row: ActivityRow, labels?: Record<string, string>): string {
  return labels?.[row.key] ?? row.label;
}

function cellOf(band: Band, row: ActivityRow): CellKind {
  return row.cell ?? band.cell ?? "tick";
}

function get(
  data: EntryData,
  band: string,
  row: string,
  col: string,
): string | boolean | null | undefined {
  return data?.[band]?.[row]?.[col];
}

/** Label cell, spanning where a row belongs to a merged group. */
function LabelCells({
  band,
  row,
  index,
  labels,
}: {
  band: Band;
  row: ActivityRow;
  index: number;
  labels?: Record<string, string>;
}) {
  const label = labelOf(row, labels);
  const cells = [];

  if (band.labelColumns && band.labelColumns.length > 1) {
    // Done By and Verified By run across the whole label area, as in the source.
    if (row.attestation) {
      return (
        <td className="lbl att" colSpan={band.labelColumns.length}>
          {label}
        </td>
      );
    }

    // First label column carries the group name, merged across its rows.
    const rows = band.rows;
    const isGroupStart =
      !row.group || index === 0 || rows[index - 1]?.group !== row.group;
    if (isGroupStart) {
      const span = row.group
        ? rows.filter((r) => r.group === row.group).length
        : 1;
      cells.push(
        <td key="g" className="lbl" rowSpan={span}>
          {labels?.[row.group ?? ""] ?? row.groupLabel ?? ""}
        </td>,
      );
    }
    cells.push(
      <td key="l" className="lbl">
        {label}
      </td>,
    );
    if (band.labelColumns.includes("FREQ")) {
      cells.push(
        <td key="f" className="lbl">
          {row.freq ?? ""}
        </td>,
      );
    }
    return <>{cells}</>;
  }

  return (
    <td className={row.attestation ? "lbl att" : "lbl"}>
      {label}
      {row.sublabel ? (
        <>
          <br />
          {row.sublabel}
        </>
      ) : null}
    </td>
  );
}

/** The split-month grid: a label column then days `dayFrom`..`dayTo`. */
function DayGrid({ band, data, signatures, labels }: BandProps) {
  const from = band.dayFrom ?? 1;
  const to = band.dayTo ?? 16;
  const days = range(from, to);
  // The second half of the month is one day short; the source keeps a trailing
  // blank column so both grids line up.
  const pad = 16 - days.length;
  const rows = band.attestation
    ? [...band.rows, ...ATTESTATION_ROWS]
    : band.rows;

  return (
    <table className="band">
      <colgroup>
        {band.labelColumns ? (
          band.labelColumns.map((c, i) => (
            <col key={c} style={{ width: i === 0 ? "9%" : "6%" }} />
          ))
        ) : (
          <col style={{ width: "27%" }} />
        )}
        {range(1, 16).map((d) => (
          <col key={d} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {band.labelColumns ? (
            band.labelColumns.map((c) => (
              <th key={c} className="lbl">
                {c}
              </th>
            ))
          ) : (
            <th className="lbl">{band.heading}</th>
          )}
          {days.map((d) => (
            <th key={d} className="dayhead">
              {d}
            </th>
          ))}
          {pad > 0 && <th colSpan={pad} />}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr
            key={row.key}
            className={row.sublabel ? "row row--tall" : "row"}
          >
            <LabelCells band={band} row={row} index={i} labels={labels} />
            {days.map((d) => (
              <td key={d} className="daycell">
                <CellValue
                  kind={cellOf(band, row)}
                  value={get(data, band.key, row.key, dayKey(d))}
                  range={row.range}
                  signatures={signatures}
                />
              </td>
            ))}
            {pad > 0 && <td colSpan={pad} />}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** All 31 days in a single band, with ACTIVITY and FREQ label columns. */
function FullMonthGrid({ band, data, signatures, labels }: BandProps) {
  const days = range(1, 31);
  const rows = band.attestation
    ? [
        ...band.rows,
        { key: "doneBy", label: "DONE BY", cell: "initial" as CellKind, attestation: true },
        { key: "verifiedBy", label: "VERIFIED BY", cell: "initial" as CellKind, attestation: true },
      ]
    : band.rows;

  return (
    <table className="band">
      <colgroup>
        <col style={{ width: "13%" }} />
        <col style={{ width: "6%" }} />
        {days.map((d) => (
          <col key={d} />
        ))}
      </colgroup>
      <thead>
        <tr>
          <th className="lbl">ACTIVITY</th>
          <th className="lbl">FREQ</th>
          {days.map((d) => (
            <th key={d} className="dayhead">
              {d}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.key} className="row">
            <td className={row.attestation ? "lbl att" : "lbl"}>
              {labelOf(row, labels)}
            </td>
            <td className="lbl">{row.freq ?? ""}</td>
            {days.map((d) => (
              <td key={d} className="daycell">
                <CellValue
                  kind={cellOf(band, row)}
                  value={get(data, band.key, row.key, dayKey(d))}
                  signatures={signatures}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** A heading column then N "Date/Initial" columns. */
function SlotBand({ bands, data, signatures, labels }: BandRunProps) {
  const lead = bands[0];
  const headings = lead.slotLabels;
  const slots = range(1, headings?.length ?? lead.slotCount ?? 5);
  return (
    <table className="band">
      <colgroup>
        <col style={{ width: "34%" }} />
        {slots.map((s) => (
          <col key={s} />
        ))}
      </colgroup>
      <thead>
        <tr>
          <th className="lbl bandhead">{lead.heading}</th>
          {slots.map((s) => (
            <th key={s} className="lbl">
              {headings ? headings[s - 1] : "Date/Initial"}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {bands.map((band, bi) => (
          <Fragmented key={band.key}>
            {bi > 0 && (
              <tr className="row row--slot">
                <td className="lbl bandhead">{band.heading}</td>
                {slots.map((s) => (
                  <td key={s} />
                ))}
              </tr>
            )}
            {band.rows.map((row, ri) => {
              if (row.sectionRow) {
                return (
                  <tr key={`${band.key}-${row.key}`} className="row">
                    <td className="lbl bandhead" colSpan={slots.length + 1}>
                      {labelOf(row, labels)}
                    </td>
                  </tr>
                );
              }
              // A span cell is drawn once and merged down its run of rows.
              const spanRun = row.spanWith
                ? band.rows.filter((r) => r.spanWith === row.spanWith)
                : null;
              const spanStart =
                !row.spanWith ||
                band.rows[ri - 1]?.spanWith !== row.spanWith;
              return (
                <tr key={`${band.key}-${row.key}`} className="row row--slot">
                  <td className="lbl">
                    {labelOf(row, labels)}
                    {row.sublabel ? (
                      <>
                        <br />
                        {row.sublabel}
                      </>
                    ) : null}
                  </td>
                  {slots.map((s) => {
                    const isSpanCol = row.spanWith && s === slots.length - 1;
                    if (isSpanCol && !spanStart) return null;
                    return (
                      <td
                        key={s}
                        rowSpan={isSpanCol ? spanRun!.length : undefined}
                      >
                        {isSpanCol ? (
                          row.spanValue
                        ) : (
                          <CellValue
                            kind={cellOf(band, row)}
                            value={get(data, band.key, row.key, `s${s}`)}
                            signatures={signatures}
                          />
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </Fragmented>
        ))}
      </tbody>
    </table>
  );
}

/** A heading column then the twelve months. */
function MonthGrid({ bands, data, signatures, labels }: BandRunProps) {
  const lead = bands[0];
  return (
    <table className="band">
      <colgroup>
        <col style={{ width: "24%" }} />
        {MONTHS.map((m) => (
          <col key={m} />
        ))}
      </colgroup>
      <thead>
        <tr>
          <th className="lbl bandhead">{lead.heading}</th>
          {MONTHS.map((m) => (
            <th key={m}>{m}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {bands.map((band, bi) => (
          <Fragmented key={band.key}>
            {bi > 0 && (
              <tr className="row">
                <td className="lbl bandhead">{band.heading}</td>
                {MONTHS.map((m) => (
                  <td key={m} />
                ))}
              </tr>
            )}
            {band.rows.map((row) => (
              <tr key={`${band.key}-${row.key}`} className="row">
                <td className="lbl">{labelOf(row, labels)}</td>
                {MONTHS.map((m, i) => (
                  <td key={m}>
                    <CellValue
                      kind={cellOf(band, row)}
                      value={get(data, band.key, row.key, `m${i + 1}`)}
                      signatures={signatures}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </Fragmented>
        ))}
      </tbody>
    </table>
  );
}

/** Named columns over a fixed number of blank lines. */
function Ledger({ band, data, signatures }: BandProps) {
  const cols = band.columns ?? [];
  const lines = range(1, band.ledgerRows ?? 15);
  return (
    <table className="band">
      <colgroup>
        {cols.map((c) => (
          <col key={c.key} style={{ width: `${c.width ?? 10}%` }} />
        ))}
      </colgroup>
      <thead>
        <tr>
          {cols.map((c) => (
            <th key={c.key} className="lbl">
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {lines.map((n) => (
          <tr
            key={n}
            className="row row--slot"
            style={
              band.ledgerRowHeight
                ? { height: `${band.ledgerRowHeight}mm` }
                : undefined
            }
          >
            {cols.map((c) => (
              <td key={c.key}>
                {c.cell === "serial" ? (
                  n
                ) : (
                  <CellValue
                    kind={c.cell}
                    value={get(data, band.key, `r${n}`, c.key)}
                    range={c.range}
                    signatures={signatures}
                  />
                )}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Two identical day ledgers side by side: days 1–16 and 17–31. */
function PairedLedger({ band, data, signatures }: BandProps) {
  const cols = band.columns ?? [];
  const left = range(1, 16);
  const right = range(17, 31);
  const groups = columnGroups(cols);

  return (
    <table className="band">
      <thead>
        {groups.length > 0 && (
          <tr>
            {[0, 1].map((half) => (
              <Fragmented key={half}>
                <th className="lbl" />
                {groups.map((g) => (
                  <th key={`${half}-${g.label}`} colSpan={g.span} className="lbl">
                    {g.label}
                  </th>
                ))}
              </Fragmented>
            ))}
          </tr>
        )}
        <tr>
          {[0, 1].map((half) => (
            <Fragmented key={half}>
              <th className="lbl">Date</th>
              {cols.map((c) => (
                <th key={`${half}-${c.key}`} className="lbl">
                  {c.label}
                </th>
              ))}
            </Fragmented>
          ))}
        </tr>
      </thead>
      <tbody>
        {left.map((day, i) => {
          const pair = right[i];
          return (
            <tr key={day} className="row row--ledger">
              <td className="daycell">{day}</td>
              {cols.map((c) => (
                <td key={`l-${c.key}`}>
                  <CellValue
                    kind={c.cell}
                    value={get(data, band.key, dayKey(day), c.key)}
                    range={c.range}
                    signatures={signatures}
                  />
                </td>
              ))}
              <td className="daycell">{pair ?? ""}</td>
              {cols.map((c) => (
                <td key={`r-${c.key}`}>
                  {pair ? (
                    <CellValue
                      kind={c.cell}
                      value={get(data, band.key, dayKey(pair), c.key)}
                      range={c.range}
                      signatures={signatures}
                    />
                  ) : null}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/** Dates 1–31 against six month/Done-By column pairs. */
function HalfYearGrid({ band, data, signatures }: BandProps) {
  const months = band.months ?? MONTHS.slice(0, 6);
  const days = range(1, 31);
  return (
    <table className="band">
      <colgroup>
        <col style={{ width: "8%" }} />
        {months.flatMap((m) => [
          <col key={`${m}-v`} />,
          <col key={`${m}-d`} />,
        ])}
      </colgroup>
      <thead>
        <tr>
          <th className="lbl">Date</th>
          {months.map((m) => (
            <Fragmented key={m}>
              <th>{m}</th>
              <th className="lbl">Done By</th>
            </Fragmented>
          ))}
        </tr>
      </thead>
      <tbody>
        {days.map((d) => (
          <tr key={d} className="row">
            <td className="daycell">{d}</td>
            {months.map((m) => (
              <Fragmented key={m}>
                <td>
                  <CellValue
                    kind="tick"
                    value={get(data, band.key, dayKey(d), `${m}`)}
                    signatures={signatures}
                  />
                </td>
                <td>
                  <CellValue
                    kind="initial"
                    value={get(data, band.key, dayKey(d), `${m}-by`)}
                    signatures={signatures}
                  />
                </td>
              </Fragmented>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const ATTESTATION_ROWS: ActivityRow[] = [
  { key: "doneBy", label: "Done By", cell: "initial", attestation: true },
  { key: "verifiedBy", label: "Verified By", cell: "initial", attestation: true },
];

function columnGroups(cols: LedgerColumn[]) {
  const groups: { label: string; span: number }[] = [];
  for (const c of cols) {
    const label = c.group ?? "";
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.span += 1;
    else groups.push({ label, span: 1 });
  }
  return groups.some((g) => g.label) ? groups : [];
}

function range(from: number, to: number): number[] {
  return Array.from({ length: to - from + 1 }, (_, i) => from + i);
}

/** Table rows cannot take a wrapper element, so cells are spread inline. */
function Fragmented({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

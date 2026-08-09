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
  }
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
  const slots = range(1, lead.slotCount ?? 5);
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
              Date/Initial
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
            {band.rows.map((row) => (
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
                {slots.map((s) => (
                  <td key={s}>
                    <CellValue
                      kind={cellOf(band, row)}
                      value={get(data, band.key, row.key, `s${s}`)}
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
          <tr key={n} className="row row--slot">
            {cols.map((c) => (
              <td key={c.key}>
                <CellValue
                  kind={c.cell}
                  value={get(data, band.key, `r${n}`, c.key)}
                  range={c.range}
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

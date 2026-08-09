import type { CellKind, NumericRange } from "@/lib/forms/types";

export interface SignatureLookup {
  /** Maps a staff code to that person's uploaded signature image. */
  [code: string]: { name: string; signature: string | null; initials: string };
}

/** Renders a stored value in the face the source format uses. */
export function CellValue({
  kind,
  value,
  range,
  signatures,
}: {
  kind: CellKind;
  value: string | boolean | null | undefined;
  range?: NumericRange;
  signatures: SignatureLookup;
}) {
  if (value === null || value === undefined || value === "" || value === false) {
    return null;
  }

  switch (kind) {
    case "tick":
      return <span className="tick">✓</span>;

    case "initial":
      return <Initial code={String(value)} signatures={signatures} />;

    case "dateInitial": {
      // Stored as "YYYY-MM-DD|STAFFCODE".
      const [date, code] = String(value).split("|");
      return (
        <span className="dateinit">
          {date ? <span className="dateinit__date">{formatDate(date)}</span> : null}
          {code ? <Initial code={code} signatures={signatures} /> : null}
        </span>
      );
    }

    case "number": {
      const n = Number(value);
      const out =
        range &&
        Number.isFinite(n) &&
        ((range.min !== undefined && n < range.min) ||
          (range.max !== undefined && n > range.max));
      return (
        <span className={out ? "val val--out" : "val"}>{String(value)}</span>
      );
    }

    default:
      return <span className="val">{String(value)}</span>;
  }
}

/**
 * A person's mark.
 *
 * Renders the uploaded signature image where one exists, falling back to typed
 * initials so a sheet is never silently blank for a staff member whose image
 * has not been captured yet.
 */
function Initial({
  code,
  signatures,
}: {
  code: string;
  signatures: SignatureLookup;
}) {
  const staff = signatures[code];
  if (staff?.signature) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img className="sig" src={staff.signature} alt={staff.name} />;
  }
  return <span className="val">{staff?.initials || code}</span>;
}

/** "12/08" — the compact form the source uses in Date/Initial cells. */
function formatDate(iso: string): string {
  const [, m, d] = iso.split("-");
  return m && d ? `${d}/${m}` : iso;
}

import type { EntryData, FormSpec } from "@/lib/forms/types";
import { BandTable } from "./bands";
import type { SignatureLookup } from "./cells";
import { ControlledCopyFooter } from "./footer";
import "./form-print.css";

/**
 * A single printable sheet.
 *
 * This is the only renderer: the preview on the entry screen and the page that
 * goes to the printer are the same component with the same stylesheet, so a
 * user who approves what they see on screen gets exactly that on paper.
 */
export function FormSheet({
  spec,
  data,
  header = {},
  signatures,
  labels,
}: {
  spec: FormSpec;
  data: EntryData;
  header?: Record<string, string>;
  signatures: SignatureLookup;
  labels?: Record<string, string>;
}) {
  // First collapse each run of continued bands into one table, then group
  // tables that the source prints side by side.
  const runs: (typeof spec.bands)[] = [];
  for (const band of spec.bands) {
    if (band.continues && runs.length > 0) runs[runs.length - 1].push(band);
    else runs.push([band]);
  }

  const groups: (typeof runs)[] = [];
  for (const run of runs) {
    if (run[0].beside && groups.length > 0) groups[groups.length - 1].push(run);
    else groups.push([run]);
  }

  return (
    <div
      className={
        spec.orientation === "landscape" ? "sheet sheet--landscape" : "sheet"
      }
    >
      <div className="sheet__frame">
        <h1 className="sheet__title">{spec.title}</h1>
        <div className="sheet__subtitle">{spec.recordingSchedule}</div>

        {spec.headerFields?.map((f) => (
          <div key={f.key} className="sheet__headerfields">
            {f.label} {header[f.key] ?? ""}
          </div>
        ))}

        {(spec.showMonthCaption || header.location) && (
          <div className="sheet__monthcaption">
            {spec.showMonthCaption && <>MONTH {header.monthLabel ?? ""}</>}
            {header.location && (
              <span className="sheet__location">
                LOCATION {header.location}
              </span>
            )}
          </div>
        )}

        <div className="sheet__body">
          {groups.map((group, i) => {
            const content = group.map((run) => {
              const note = run.find((b) => b.note)?.note;
              return (
                <div key={run[0].key}>
                  <BandTable
                    bands={run}
                    data={data}
                    signatures={signatures}
                    labels={labels}
                  />
                  {note && <div className="sheet__note">{note}</div>}
                </div>
              );
            });
            return group.length > 1 ? (
              <div key={i} className="band-pair">
                {content}
              </div>
            ) : (
              <div key={i}>{content}</div>
            );
          })}

          {spec.legend && <div className="sheet__legend">{spec.legend}</div>}
          {spec.footnotes?.map((note, i) => (
            <div key={i} className="sheet__footnote">
              {note}
            </div>
          ))}
        </div>

        <ControlledCopyFooter spec={spec} />
      </div>
    </div>
  );
}

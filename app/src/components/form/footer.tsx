import type { FormSpec } from "@/lib/forms/types";
import { CLAUSE_TITLES } from "@/lib/forms/types";

/**
 * The controlled-copy footer.
 *
 * The Noble device and the two approval signatures are the images lifted from
 * the source PDF, unaltered. They attest that the *format* was prepared by the
 * Quality Manager and approved by the Lab Director — which is a property of
 * the blank form, not of any particular day's entries — so they belong here
 * on every sheet exactly as they appear in NDC-DI.
 */
export function ControlledCopyFooter({
  spec,
  issueNo = "IV",
  issueDate = "01 04 2024",
  revNo = "00",
  revisionDate = "--",
}: {
  spec: FormSpec;
  issueNo?: string;
  issueDate?: string;
  revNo?: string;
  revisionDate?: string;
}) {
  const strap = spec.footerTitle ?? CLAUSE_TITLES[spec.clause];
  const docNo = spec.docNoOverride ?? `NDC / DI / ${spec.clause}`;

  // The footer occupies roughly two thirds of the measure on portrait pages,
  // matching the source, with the logo cell closing it on the right.
  return (
    <div className="sheet__footer">
      <table className="footer" style={{ width: "82%" }}>
        <colgroup>
          <col style={{ width: "21%" }} />
          <col style={{ width: "21%" }} />
          <col style={{ width: "15%" }} />
          <col style={{ width: "28%" }} />
          <col style={{ width: "15%" }} />
        </colgroup>
        <tbody>
          <tr>
            <td className="f-org" colSpan={3}>
              NOBLE DIAGNOSTIC CENTRE
            </td>
            <td className="f-docno">Doc No. {docNo}</td>
            <td className="f-logo" rowSpan={4}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/brand/ndc-logo.png" alt="" />
            </td>
          </tr>
          <tr>
            <td className="f-strap" colSpan={3}>
              {strap}
            </td>
            <td className="f-page">
              Page {spec.pageOfClause} of clause {spec.clause}
            </td>
          </tr>
          <tr>
            <td className="f-meta">Issue No. {issueNo}</td>
            <td className="f-meta">Issue Date: {issueDate}</td>
            <td className="f-meta">Rev No. {revNo}</td>
            <td className="f-meta">Revision Date: {revisionDate}</td>
          </tr>
          <tr>
            <td className="f-sign">
              <ApprovalSignature
                src="/brand/sign-quality-manager.png"
                caption="Prepared By Quality Manager"
              />
            </td>
            <td className="f-sign" colSpan={2}>
              <ApprovalSignature
                src="/brand/sign-lab-director.png"
                caption="Approved By Lab Director"
              />
            </td>
            <td className="f-controlled">CONTROLLED COPY</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function ApprovalSignature({
  src,
  caption,
}: {
  src: string;
  caption: string;
}) {
  return (
    <div>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="f-sign__img" src={src} alt="" />
      <div className="f-sign__caption">{caption}</div>
    </div>
  );
}

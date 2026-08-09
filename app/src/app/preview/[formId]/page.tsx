import { notFound } from "next/navigation";
import { FormSheet } from "@/components/form/sheet";
import { getForm } from "@/lib/forms/registry";
import { resolveSpec } from "@/lib/forms/resolve";
import { activeLocations } from "@/lib/config";

/**
 * Blank-format preview.
 *
 * Renders a format with no entries, which is the state to compare against the
 * corresponding page of NDC-DI when checking that the reproduction is faithful.
 */
export default async function PreviewPage({
  params,
}: {
  params: Promise<{ formId: string }>;
}) {
  const { formId } = await params;
  const base = getForm(formId);
  if (!base) notFound();

  // Resolved against the configured locations, so the preview shows the sheet
  // the laboratory will actually print rather than the source's blank rows.
  const spec = resolveSpec(base, activeLocations("main"));

  return (
    <div className="print-root sheet-preview">
      {spec.orientation === "landscape" && (
        <style>{"@page { size: A4 landscape; margin: 0 }"}</style>
      )}
      <FormSheet spec={spec} data={{}} signatures={{}} />
    </div>
  );
}

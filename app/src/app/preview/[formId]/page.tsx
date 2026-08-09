import { notFound } from "next/navigation";
import { FormSheet } from "@/components/form/sheet";
import { getForm } from "@/lib/forms/registry";

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
  const spec = getForm(formId);
  if (!spec) notFound();

  return (
    <div className="print-root sheet-preview">
      {spec.orientation === "landscape" && (
        <style>{"@page { size: A4 landscape; margin: 0 }"}</style>
      )}
      <FormSheet spec={spec} data={{}} signatures={{}} />
    </div>
  );
}

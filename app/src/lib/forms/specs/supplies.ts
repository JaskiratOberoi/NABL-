import type { FormSpec } from "../types";

/**
 * Clause 6.5, 6.6, 6.7 and 6.8 record formats.
 *
 * Unlike the clause 6.3 and 6.4 schedules, these are event ledgers and subject
 * records: a line per purchase, a sheet per supplier. They share the same
 * controlled-copy footer and page references.
 */

/** NDC/DI/6.5 page 3 — source page 88. */
export const phBufferMonitoring: FormSpec = {
  id: "ph-buffer-monitoring",
  title: "pH BUFFER MONITORING FORM",
  recordingSchedule: "(Recording schedule – Weekly)",
  clause: "6.5",
  pageOfClause: 3,
  sourcePage: 88,
  sourcePageSize: "A4",
  footerTitle:
    "Documented Information–Equipment calibration & metrological traceability",
  orientation: "portrait",
  sheetPeriod: "month",
  bands: [
    {
      key: "ledger",
      heading: "",
      layout: "ledger",
      cadence: "weekly",
      rows: [],
      ledgerRows: 26,
      // The source lays this out as two identical sets of columns side by side.
      columns: [
        { key: "dateA", label: "Date", cell: "text", width: 14 },
        {
          key: "phA",
          label: "pH of Buffer",
          cell: "number",
          width: 18,
          range: { min: 6.8, max: 7.2, label: "6.8 – 7.2" },
        },
        { key: "doneByA", label: "Done By", cell: "initial", width: 18 },
        { key: "dateB", label: "Date", cell: "text", width: 14 },
        {
          key: "phB",
          label: "pH of Buffer",
          cell: "number",
          width: 18,
          range: { min: 6.8, max: 7.2, label: "6.8 – 7.2" },
        },
        { key: "doneByB", label: "Done By", cell: "initial", width: 18 },
      ],
    },
  ],
  footnotes: ["Acceptance criteria: pH should be between 6.8 – 7.2"],
};

/** NDC/DI/6.6 page 6 — source page 95. */
export const purchaseOrderForm: FormSpec = {
  id: "purchase-order-form",
  title: "PURCHASE ORDER FORM",
  recordingSchedule:
    "(Recording schedule – For every purchase done in the lab)",
  clause: "6.6",
  pageOfClause: 6,
  sourcePage: 95,
  sourcePageSize: "Letter",
  footerTitle: "Documented Information – Handling reagents and consumables",
  orientation: "landscape",
  sheetPeriod: "month",
  bands: [
    {
      key: "ledger",
      heading: "",
      layout: "ledger",
      cadence: "asRequired",
      rows: [],
      ledgerRows: 20,
      columns: [
        { key: "date", label: "Date", cell: "text", width: 9 },
        {
          key: "item",
          label: "Item orders with specifications",
          cell: "text",
          width: 30,
        },
        { key: "makeModel", label: "Make / Model", cell: "text", width: 15 },
        { key: "qty", label: "Qty", cell: "number", width: 7 },
        { key: "supplier", label: "Supplier", cell: "text", width: 15 },
        {
          key: "orderGivenBy",
          label: "Order Given By",
          cell: "initial",
          width: 12,
        },
        { key: "approvedBy", label: "Approved By", cell: "initial", width: 12 },
      ],
    },
  ],
};

/** NDC/DI/6.6 page 7 — source page 96. */
export const stockItemsForm: FormSpec = {
  id: "stock-items-form",
  title: "STOCK ITEMS FORM",
  recordingSchedule:
    "(Recording schedule – For every item received / issued)",
  clause: "6.6",
  pageOfClause: 7,
  sourcePage: 96,
  sourcePageSize: "Letter",
  footerTitle: "Documented Information – Handling reagents and consumables",
  orientation: "landscape",
  sheetPeriod: "month",
  headerFields: [
    { key: "item", label: "ITEM" },
    { key: "minimumStockLevel", label: "MINIMUM STOCK LEVEL" },
  ],
  bands: [
    {
      key: "ledger",
      heading: "",
      layout: "ledger",
      cadence: "asRequired",
      rows: [],
      ledgerRows: 20,
      columns: [
        { key: "date", label: "Date", cell: "text", width: 8 },
        { key: "supplier", label: "Supplier", cell: "text", width: 13 },
        {
          key: "billChallanNo",
          label: "Bill / Challan No.",
          cell: "text",
          width: 10,
        },
        {
          key: "inspectionBy",
          label: "Incoming inspection done by",
          cell: "initial",
          width: 10,
        },
        { key: "qtyRecd", label: "Qty Recd", cell: "number", width: 7 },
        { key: "company", label: "Company", cell: "text", width: 10 },
        { key: "expiry", label: "Expiry", cell: "text", width: 8 },
        {
          key: "lotBatchNo",
          label: "Lot / Batch No.",
          cell: "text",
          width: 10,
        },
        { key: "qtyIssued", label: "Qty. Issued", cell: "number", width: 7 },
        { key: "issuedTo", label: "Issued to", cell: "text", width: 8 },
        { key: "balance", label: "Balance", cell: "number", width: 9 },
      ],
    },
  ],
};

/**
 * NDC/DI/6.7 page 6 — source page 102.
 *
 * The source prints this page's document number as "MMD / P&P / 6.7", which is
 * another organisation's prefix. Reproduced verbatim; see S-08 in
 * docs/reference/DI6-source-defects.md.
 */
export const serviceAgreementDeviation: FormSpec = {
  id: "service-agreement-deviation",
  title: "SERVICE AGREEMENT DEVIATION FORM",
  recordingSchedule:
    "(Recording schedule – Whenever there is change in original agreement)",
  clause: "6.7",
  pageOfClause: 6,
  sourcePage: 102,
  sourcePageSize: "Letter",
  docNoOverride: "MMD / P&P / 6.7",
  footerTitle: "Documented Information – Service agreements",
  orientation: "landscape",
  sheetPeriod: "month",
  bands: [
    {
      key: "ledger",
      heading: "",
      layout: "ledger",
      cadence: "asRequired",
      rows: [],
      ledgerRows: 18,
      columns: [
        { key: "date", label: "Date", cell: "text", width: 8 },
        { key: "patientId", label: "Patient ID", cell: "text", width: 9 },
        {
          key: "eqpt",
          label: "Eqpt",
          cell: "tick",
          width: 6,
          group: "Reason for Deviation",
        },
        {
          key: "method",
          label: "Method",
          cell: "tick",
          width: 6,
          group: "Reason for Deviation",
        },
        {
          key: "kit",
          label: "Kit",
          cell: "tick",
          width: 5,
          group: "Reason for Deviation",
        },
        {
          key: "sample",
          label: "Sample",
          cell: "tick",
          width: 6,
          group: "Reason for Deviation",
        },
        {
          key: "usersRequest",
          label: "User’s Request",
          cell: "tick",
          width: 8,
          group: "Reason for Deviation",
        },
        {
          key: "others",
          label: "Others",
          cell: "tick",
          width: 6,
          group: "Reason for Deviation",
        },
        {
          key: "details",
          label: "Details of Deviation",
          cell: "text",
          width: 16,
        },
        { key: "actionTaken", label: "Action Taken", cell: "text", width: 14 },
        { key: "approvedBy", label: "Approved By", cell: "initial", width: 10 },
      ],
    },
  ],
};

const EXT_FOOTER = "Documented Information – Externally provided products & services";

/** NDC/DI/6.8 page 7 — source page 110. */
export const supplierRegistration: FormSpec = {
  id: "supplier-registration",
  title: "SUPPLIER REGISTRATION FORM",
  recordingSchedule: "(Recording schedule – For every new supplier)",
  clause: "6.8",
  pageOfClause: 7,
  sourcePage: 110,
  sourcePageSize: "A4",
  footerTitle: EXT_FOOTER,
  orientation: "portrait",
  sheetPeriod: "month",
  bands: [
    {
      key: "details",
      heading: "",
      layout: "fields",
      cadence: "asRequired",
      rows: [],
      fields: [
        { key: "company", label: "Name of the company" },
        { key: "address", label: "Address", lines: 1 },
        { key: "phone", label: "Phone", width: 0.33 },
        { key: "fax", label: "Fax", width: 0.33 },
        { key: "email", label: "E Mail", width: 0.33 },
        { key: "contactPerson", label: "Name of the Contact Person" },
        {
          key: "distributorships",
          label:
            "The Company is having distributorship of the following companies",
          listCount: 5,
        },
        { key: "creditLimit", label: "Credit Limit offered" },
        { key: "deliverySchedule", label: "Delivery schedule of various items" },
        { key: "clients", label: "Clients of repute", listCount: 5 },
        { key: "experience", label: "Past experience in medical industry" },
        {
          key: "discounts",
          label: "Details of discounts / schemes offered",
        },
      ],
    },
    {
      key: "officeHeader",
      heading: "",
      layout: "fields",
      cadence: "asRequired",
      rows: [],
      fields: [{ key: "officeUse", label: "", section: "For office use only" }],
    },
    {
      key: "office",
      heading: "Criteria for approval",
      layout: "slots",
      cadence: "asRequired",
      slotLabels: ["Assessment"],
      cell: "text",
      rows: [
        { key: "pastExperience", label: "1  Past Experience" },
        {
          key: "recommendation",
          label: "2  Recommendation from present clients",
        },
        { key: "proximity", label: "3  Proximity to our Laboratory" },
        { key: "isoCertified", label: "4  ISO Certified Company" },
        { key: "creditLimit", label: "5  Credit Limit" },
        { key: "discounts", label: "6  Discounts / Schemes offered" },
        { key: "remarks", label: "Remarks" },
      ],

    },
    {
      key: "sign",
      heading: "",
      layout: "fields",
      cadence: "asRequired",
      rows: [],
      fields: [
        { key: "date", label: "Date:", width: 0.5 },
        { key: "signature", label: "Signature", cell: "initial", width: 0.5 },
        { key: "nameDesignation", label: "Name & Designation", width: 0.5 },
      ],
    },
  ],
};

/** NDC/DI/6.8 page 8 — source page 111. */
export const supplierPerformanceEvaluation: FormSpec = {
  id: "supplier-performance-evaluation",
  title: "SUPPLIER PERFORMANCE EVALUATION FORM",
  recordingSchedule: "(Recording schedule – Yearly)",
  clause: "6.8",
  pageOfClause: 8,
  sourcePage: 111,
  sourcePageSize: "Letter",
  footerTitle: EXT_FOOTER,
  orientation: "landscape",
  sheetPeriod: "month",
  headerFields: [
    { key: "supplierName", label: "Supplier Name" },
    { key: "duration", label: "Duration" },
    { key: "challansReceived", label: "Total Number of challan / bills received" },
  ],
  bands: [
    {
      key: "evaluation",
      heading: "Criteria for evaluation",
      layout: "slots",
      cadence: "yearly",
      cell: "text",
      slotLabels: [
        "Wrong Item were supplied",
        "Wrong Brand /Specifications was supplied",
        "Supply was Delayed",
        "Items were rejected due to leakage, breakage, packing, transportation method, Short Expiry",
        "Wrong Billing was done",
        "Total Violation",
      ],
      rows: [
        { key: "noOfBills", label: "No. of Bills/Challans where" },
        { key: "billNoDate", label: "Bill / Challan No & Date" },
        { key: "reason", label: "Reason for violation" },
        { key: "accepted", label: "Reason Accepted/ Rejected" },
        { key: "overallGrade", label: "Overall Grade" },
        { key: "doneBy", label: "Done By", cell: "initial", attestation: true },
        {
          key: "verifiedBy",
          label: "Verified By",
          cell: "initial",
          attestation: true,
        },
      ],
    },
  ],
  footnotes: [
    "Performance Evaluation Criteria: A – Less than 5 violations,   B – Between 5 – 10 violations,   C - More than 10 violations",
    "Action to be taken: A – Recommendation   B – Request for improving the services   C – Warning",
  ],
};

/** NDC/DI/6.8 page 9 — source page 112. */
export const supplierOnsiteVisit: FormSpec = {
  id: "supplier-onsite-visit",
  title: "SUPPLIER ONSITE VISIT FORM",
  recordingSchedule: "(Recording schedule – Yearly)",
  clause: "6.8",
  pageOfClause: 9,
  sourcePage: 112,
  sourcePageSize: "A4",
  footerTitle: EXT_FOOTER,
  orientation: "portrait",
  sheetPeriod: "month",
  bands: [
    {
      key: "header",
      heading: "",
      layout: "fields",
      cadence: "asRequired",
      rows: [],
      fields: [
        { key: "date", label: "Date", width: 0.5 },
        {
          key: "visitedBy",
          label: "Name / Sign of the Person who visited the premises.",
          width: 0.5,
        },
        { key: "supplierName", label: "Supplier’s Name", width: 0.5 },
        {
          key: "personContacted",
          label: "Person contacted during inspection:",
          width: 0.5,
        },
      ],
    },
    {
      key: "ratingsLeft",
      heading: "VERIFICATION DETAILS",
      layout: "slots",
      cadence: "yearly",
      slotLabels: ["RATING X / 10"],
      cell: "number",
      rows: [
        { key: "spaceAdequacy", label: "Space adequacy w.r.to items stored" },
        { key: "environment", label: "Environment condition" },
        { key: "cleanliness", label: "Cleanliness" },
        { key: "billing", label: "Billing Procedure" },
        { key: "transportation", label: "Transportation of items" },
        { key: "expiredItems", label: "Handling expired item" },
      ],
    },
    {
      key: "ratingsRight",
      heading: "VERIFICATION DETAILS",
      layout: "slots",
      cadence: "yearly",
      beside: true,
      slotLabels: ["RATING X / 10"],
      cell: "number",
      rows: [
        { key: "coldChain", label: "Cold chain maintained" },
        { key: "storage", label: "Storage condition" },
        { key: "inventory", label: "Inventory management" },
        { key: "packaging", label: "Packaging of items" },
        { key: "rejections", label: "Handling rejections" },
        { key: "staffCompetence", label: "Staff competence" },
      ],
    },
    {
      key: "overall",
      heading: "",
      layout: "fields",
      cadence: "yearly",
      rows: [],
      fields: [
        { key: "overallRating", label: "OVERALL RATING: X / 120", width: 0.5 },
      ],
    },
  ],
  footnotes: [
    "Performance Evaluation Criteria: A:> 100,   B: Between 90 – 100 violations,   C:< 90",
    "Action to be taken: A – Recommendation   B – Request for improving the services   C - Warning",
  ],
};

/** NDC/DI/6.8 page 11 — source page 114. Carries two formats on one page. */
export const outsourcedLabEvaluation: FormSpec = {
  id: "outsourced-lab-evaluation",
  title: "OUTSOURCED LAB EVALUATION FORM",
  recordingSchedule: "(Recording schedule – 6 monthly)",
  clause: "6.8",
  pageOfClause: 11,
  sourcePage: 114,
  sourcePageSize: "A4",
  footerTitle: EXT_FOOTER,
  orientation: "portrait",
  sheetPeriod: "month",
  headerFields: [
    { key: "evaluationYear", label: "Performance Evaluation Year:" },
    { key: "refLabName", label: "Name of Ref Lab:" },
  ],
  bands: [
    {
      key: "complaints",
      heading: "COMPLAINTS AGAINST",
      layout: "slots",
      cadence: "halfYearly",
      slotLabels: ["Jan - June", "July - December"],
      cell: "text",
      rows: [
        { key: "pickupDelay", label: "1  Delay in Pick up of Samples" },
        {
          key: "transport",
          label: "2  Non standard method of transportation",
        },
        { key: "wrongEntry", label: "3  Wrong Patient / Test Entry" },
        { key: "reportDelay", label: "4  Delay in Delivery of Reports" },
        { key: "behaviour", label: "5  Behavior of Ref Lab Staff" },
        { key: "billingErrors", label: "6  Errors in billing" },
        { key: "communication", label: "7  Improper Communication" },
        {
          key: "urgentReports",
          label: "8  Refusal to give alert /urgent reports over phone",
        },
        { key: "overallRating", label: "Overall Rating" },
        {
          key: "doneBy",
          label: "Evaluation Done By",
          cell: "initial",
          attestation: true,
        },
        {
          key: "verifiedBy",
          label: "Verified By",
          cell: "initial",
          attestation: true,
        },
        { key: "yearlyRating", label: "Yearly Performance Rating" },
      ],
    },
    {
      key: "criteria",
      heading: "CRITERIA OF EVALUATION",
      layout: "slots",
      cadence: "asRequired",
      slotLabels: ["RATING", "ACTION TAKEN"],
      cell: "text",
      rows: [
        { key: "c10", label: "10 or more complaints" },
        { key: "c5", label: "5 or more complaints" },
        { key: "cLess", label: "Less than 5 complaints" },
      ],
    },
    {
      key: "visitHeader",
      heading: "",
      layout: "fields",
      cadence: "yearly",
      rows: [],
      fields: [
        {
          key: "visitTitle",
          label: "",
          section: "ONSITE VISIT RECORD  (Recording schedule – Yearly)",
        },
        { key: "date", label: "Date", width: 0.33 },
        { key: "personVisited", label: "Person Visited", width: 0.33 },
        { key: "personContacted", label: "Person Contacted", width: 0.33 },
      ],
    },
    {
      key: "visit",
      heading: "VERIFICATION DETAILS",
      layout: "slots",
      cadence: "yearly",
      slotLabels: ["STATUS", "REMARKS"],
      cell: "text",
      rows: [
        {
          key: "environment",
          label: "Work Environment / Facilities / Storage",
        },
        { key: "infrastructure", label: "Lab Infrastructure / Space" },
        { key: "procedures", label: "Lab Procedures followed as per NABL" },
        { key: "records", label: "Lab Records available as per NABL" },
        { key: "pathologist", label: "Availability of Pathologist" },
        { key: "manpower", label: "Manpower strength & competence" },
        { key: "qc", label: "QC/EQAS/ Verification etc done" },
        { key: "equipment", label: "Equipment PM / Calibration records" },
        { key: "reporting", label: "Reporting System" },
      ],
    },
  ],
  footnotes: [
    "Rating C: Warning (Discontinue if the supplier gets C rating for 2 consecutive years).  Rating B: Suggestion for improvement.  Rating A: Recommend for continuation.",
  ],
};

export const supplyForms: FormSpec[] = [
  phBufferMonitoring,
  purchaseOrderForm,
  stockItemsForm,
  serviceAgreementDeviation,
  supplierRegistration,
  supplierPerformanceEvaluation,
  supplierOnsiteVisit,
  outsourcedLabEvaluation,
];

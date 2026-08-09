import type { FormSpec, ActivityRow } from "../types";

/** The Done By / Verified By pair that closes every daily band in DI 6. */
export const attestationRows: ActivityRow[] = [
  { key: "doneBy", label: "Done By", cell: "initial", attestation: true },
  { key: "verifiedBy", label: "Verified By", cell: "initial", attestation: true },
];

/** NDC/DI/6.3 page 7 — source page 33. */
export const facilityRoundChecklist: FormSpec = {
  id: "facility-round-checklist",
  title: "FACILITY ROUND CHECKLIST",
  recordingSchedule:
    "(Recording schedule – Daily, Weekly, Monthly, Quarterly, 6 Monthly",
  clause: "6.3",
  pageOfClause: 7,
  sourcePage: 33,
  sourcePageSize: "Letter",
  orientation: "portrait",
  sheetPeriod: "month",
  bands: [
    {
      key: "daily1",
      heading: "Daily",
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 1,
      dayTo: 16,
      cell: "tick",
      attestation: true,
      rows: [
        {
          key: "dgSet",
          label: "Check DG set coolant, engine oil",
          sublabel: "and fuel level",
        },
        { key: "safetyDevices", label: "Check all safety devices working" },
        { key: "generatorLeak", label: "Check generator oil leakage" },
        { key: "earthing", label: "Check lab earthing" },
        { key: "fireExtinguisher", label: "Check Fire Extinguisher status" },
        { key: "housekeeping", label: "Check Housekeeping" },
      ],
    },
    {
      key: "daily2",
      heading: "Daily",
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 17,
      dayTo: 31,
      cell: "tick",
      attestation: true,
      note: "* Add fuel if level less than 30 liter mark",
      rows: [
        {
          key: "dgSet",
          label: "Check DG set coolant, engine oil",
          sublabel: "and fuel level",
        },
        { key: "safetyDevices", label: "Check all safety devices working" },
        { key: "generatorLeak", label: "Check generator oil leakage" },
        { key: "earthing", label: "Check lab earthing" },
        { key: "fireExtinguisher", label: "Check Fire Extinguisher status" },
        { key: "housekeeping", label: "Check Housekeeping" },
      ],
    },
    {
      key: "weekly",
      heading: "WEEKLY",
      layout: "slots",
      cadence: "weekly",
      slotCount: 5,
      cell: "dateInitial",
      rows: [
        { key: "batteryTerminals", label: "Clean all battery terminals" },
        { key: "surfaceGenerator", label: "Surface cleaning – Generator" },
        { key: "surfaceAC", label: "Surface cleaning – A/C" },
      ],
    },
    {
      key: "fortnightly",
      continues: true,
      heading: "FORTNIGHTLY",
      layout: "slots",
      cadence: "fortnightly",
      slotCount: 5,
      cell: "dateInitial",
      rows: [{ key: "acFilter", label: "A/C Filter cleaning" }],
    },
    {
      key: "monthly",
      heading: "MONTHLY",
      layout: "monthGrid",
      cadence: "monthly",
      cell: "dateInitial",
      rows: [{ key: "generatorServicing", label: "Generator Servicing" }],
    },
    {
      key: "quarterly",
      continues: true,
      heading: "QUARTERLY",
      layout: "monthGrid",
      cadence: "quarterly",
      cell: "dateInitial",
      rows: [
        { key: "overheadTank", label: "Clean overhead tank" },
        { key: "roReservoir", label: "Clean RO Water reservoir" },
      ],
    },
    {
      key: "halfYearly",
      continues: true,
      heading: "6 MONTHLY",
      layout: "monthGrid",
      cadence: "halfYearly",
      cell: "dateInitial",
      rows: [
        { key: "acServicing", label: "A/ C servicing" },
        { key: "fireAlarm", label: "Fire Alarm Working" },
      ],
    },
  ],
  footnotes: [
    "Safety devices include: Fire Alarm, Fire extinguishers, Grab Rail, Anti Skid tapes, PPE",
  ],
};

/**
 * NDC/DI/6.3 pages 8 and 9 — source pages 34 and 35.
 * One sheet per half year; the source prints JAN–JUN and JUL–DEC separately.
 */
export const hypoSolutionPreparation: FormSpec = {
  id: "hypo-solution-preparation",
  title: "1% HYPO SOLUTION PREPARATION FORM",
  recordingSchedule: "(Recording schedule – Daily)",
  clause: "6.3",
  pageOfClause: 8,
  sourcePage: 34,
  sourcePageSize: "Letter",
  orientation: "portrait",
  sheetPeriod: "halfYear",
  bands: [
    {
      key: "grid",
      heading: "Date",
      layout: "halfYearGrid",
      cadence: "daily",
      cell: "tick",
      rows: [],
    },
  ],
};

/** NDC/DI/6.3 page 10 — source page 36. Landscape. */
export const temperatureHumidityMonitoring: FormSpec = {
  id: "temperature-humidity-monitoring",
  title: "TEMPERATURE/ HUMIDITY MONITORING FORM",
  recordingSchedule: "(Recording schedule – Daily)",
  clause: "6.3",
  pageOfClause: 10,
  sourcePage: 36,
  sourcePageSize: "Letter",
  orientation: "landscape",
  sheetPeriod: "month",
  bands: [
    {
      key: "daily1",
      heading: "Location",
      layout: "dayGrid",
      cadence: "twiceDaily",
      dayFrom: 1,
      dayTo: 16,
      cell: "number",
      labelColumns: ["Location", "Date"],
      attestation: true,
      // Four monitored locations, each recorded morning and evening. The source
      // leaves the location names blank; they come from site configuration.
      rows: locationRows(),
    },
    {
      key: "daily2",
      heading: "Location",
      layout: "dayGrid",
      cadence: "twiceDaily",
      dayFrom: 17,
      dayTo: 31,
      cell: "number",
      labelColumns: ["Location", "Date"],
      attestation: true,
      rows: locationRows(),
    },
  ],
  footnotes: [
    "• Acceptance Criteria:  Fridge: 2 – 8ºC, Freezer: -10 to -20ºC, Room: 22ºC to 28ºC, Incubator: 37ºC +/- 2ºC, Humidity: 30% –70%, Ultra Deep Freezer: - 70ºC",
  ],
};

function locationRows(): ActivityRow[] {
  const rows: ActivityRow[] = [];
  for (let i = 1; i <= 4; i++) {
    rows.push({
      key: `loc${i}M`,
      label: "(M)",
      group: `loc${i}`,
      groupLabel: "",
      editableLabel: true,
    });
    rows.push({
      key: `loc${i}E`,
      label: "(E)",
      group: `loc${i}`,
      groupLabel: "",
      editableLabel: true,
    });
  }
  return rows;
}

/** NDC/DI/6.3 page 11 — source page 37. Landscape, two ledgers side by side. */
export const wasteDisposalRecord: FormSpec = {
  id: "waste-disposal-record",
  title: "WASTE DISPOSAL RECORD",
  recordingSchedule: "(Recording schedule – Daily)",
  clause: "6.3",
  pageOfClause: 11,
  sourcePage: 37,
  sourcePageSize: "Letter",
  orientation: "landscape",
  sheetPeriod: "month",
  showMonthCaption: true,
  bands: [
    {
      key: "ledger",
      heading: "Date",
      layout: "pairedLedger",
      cadence: "daily",
      rows: [],
      columns: [
        {
          key: "bagQty",
          label: "Yellow / Red Bag Waste Qty {in Kg)",
          cell: "number",
          width: 12,
          group: "Solid Waste Disposal",
        },
        {
          key: "punctureBox",
          label: "Blue & White Puncture Proof Box",
          cell: "number",
          width: 12,
          group: "Solid Waste Disposal",
        },
        {
          key: "handedOverBy",
          label: "Handed Over By",
          cell: "initial",
          width: 10,
          group: "Solid Waste Disposal",
        },
        {
          key: "hypoMixTime",
          label: "1% Hypo mixing time",
          cell: "time",
          width: 10,
          group: "Liquid Waste Disposal",
        },
        {
          key: "disposalTime",
          label: "Disposal Time",
          cell: "time",
          width: 10,
          group: "Liquid Waste Disposal",
        },
        { key: "doneBy", label: "Done By", cell: "initial", width: 9 },
      ],
    },
  ],
};

/** NDC/DI/6.3 page 12 — source page 38. Landscape, all 31 days in one band. */
export const housekeepingSchedule: FormSpec = {
  id: "housekeeping-schedule",
  title: "HOUSEKEEPING SCHEDULE",
  recordingSchedule:
    "(Recording schedule – Daily, Weekly, Fortnightly, Monthly",
  clause: "6.3",
  pageOfClause: 12,
  sourcePage: 38,
  sourcePageSize: "Letter",
  docNoOverride: "NDC / DI/ 6.3",
  orientation: "landscape",
  sheetPeriod: "month",
  showMonthCaption: true,
  bands: [
    {
      key: "activities",
      heading: "ACTIVITY",
      layout: "fullMonthGrid",
      cadence: "daily",
      cell: "tick",
      labelColumns: ["ACTIVITY", "FREQ"],
      attestation: true,
      rows: [
        { key: "flooring", label: "Flooring", freq: "2 X D" },
        { key: "dustbins", label: "Clear Dustbins", freq: "2 X D" },
        { key: "labFurniture", label: "Lab Furniture", freq: "D" },
        { key: "labWorkbench", label: "Lab Workbench", freq: "D" },
        { key: "workbenchHypo", label: "Workbench Hypo Cleaning", freq: "D" },
        { key: "windows", label: "Windows", freq: "W" },
        { key: "lightsFans", label: "Lights & Fans", freq: "F" },
        { key: "shelfCabinets", label: "Shelf &Cabinets", freq: "M" },
        { key: "others", label: "Others", freq: "AR" },
      ],
    },
  ],
  legend:
    "D – Daily          W – Weekly                 F – Fortnightly                   M – Monthly                   AR – As Required",
};

/** NDC/DI/6.3 page 13 — source page 39. Landscape. */
export const toiletCleaningSchedule: FormSpec = {
  id: "toilet-cleaning-schedule",
  title: "TOILET CLEANING SCHEDULE",
  recordingSchedule: "(Recording schedule – Daily)",
  clause: "6.3",
  pageOfClause: 13,
  sourcePage: 39,
  sourcePageSize: "Letter",
  orientation: "landscape",
  sheetPeriod: "month",
  showMonthCaption: true,
  bands: [
    {
      key: "slot1",
      heading: "TIME",
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 1,
      dayTo: 16,
      cell: "tick",
      rows: toiletRows(),
    },
    {
      key: "slot2",
      heading: "TIME",
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 17,
      dayTo: 31,
      cell: "tick",
      rows: toiletRows(),
    },
  ],
};

function toiletRows(): ActivityRow[] {
  return [
    { key: "t0800", label: "8:00 AM" },
    { key: "t1100", label: "11:00 NOON" },
    { key: "t1400", label: "2:00 PM" },
    { key: "t1700", label: "5:00 PM" },
    {
      key: "verifiedBy",
      label: "Verified",
      sublabel: "By",
      cell: "initial",
      attestation: true,
    },
  ];
}

/** NDC/DI/6.3 page 14 — source page 40. Landscape free ledger. */
export const autoclaveForm: FormSpec = {
  id: "autoclave-form",
  title: "AUTOCLAVE FORM",
  recordingSchedule: "(Recording schedule – Daily or when autoclave is run)",
  clause: "6.3",
  pageOfClause: 14,
  sourcePage: 40,
  sourcePageSize: "Letter",
  orientation: "landscape",
  sheetPeriod: "month",
  bands: [
    {
      key: "ledger",
      heading: "",
      layout: "ledger",
      cadence: "daily",
      rows: [],
      ledgerRows: 18,
      columns: [
        { key: "date", label: "Date", cell: "text", width: 8 },
        { key: "loadNo", label: "Load No.", cell: "text", width: 7 },
        { key: "items", label: "ITEMS", cell: "text", width: 22 },
        { key: "startTime", label: "Start Time", cell: "time", width: 9 },
        {
          key: "tempC",
          label: "Temp. in °C",
          cell: "number",
          width: 9,
          range: { min: 121, label: "121 °C minimum" },
        },
        {
          key: "pressurePsi",
          label: "Pressure in psi",
          cell: "number",
          width: 9,
          range: { min: 15, label: "15 psi minimum" },
        },
        { key: "endTime", label: "End Time", cell: "time", width: 9 },
        {
          key: "holdingTime",
          label: "Holding Time (In Min)",
          cell: "number",
          width: 9,
          range: { min: 15, label: "15 minutes minimum" },
        },
        { key: "doneBy", label: "Done By", cell: "initial", width: 8 },
        {
          key: "indicatorRecord",
          label: "Indicator Record",
          cell: "text",
          width: 10,
        },
      ],
    },
  ],
};

export const facilitiesForms: FormSpec[] = [
  facilityRoundChecklist,
  hypoSolutionPreparation,
  temperatureHumidityMonitoring,
  wasteDisposalRecord,
  housekeepingSchedule,
  toiletCleaningSchedule,
  autoclaveForm,
];

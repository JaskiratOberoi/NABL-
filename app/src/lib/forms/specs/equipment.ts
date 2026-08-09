import type { FormSpec, ActivityRow, Band } from "../types";

/**
 * Clause 6.4 maintenance schedules.
 *
 * These share a rigid shape: a split-month daily grid closed by Done By /
 * Verified By, then some combination of WEEKLY / MONTHLY / QUARTERLY /
 * 6 MONTHLY / YEARLY slot bands, and on three instruments an AS NEEDED and
 * REPLACEMENTS pair. The helpers below build that shape so each schedule
 * declares only what differs.
 */

/** Builds the paired 1–16 / 17–31 daily bands shared by every schedule. */
function dailyBands(rows: ActivityRow[], heading = "Daily"): Band[] {
  return [
    {
      key: "daily1",
      heading,
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 1,
      dayTo: 16,
      cell: "tick",
      attestation: true,
      rows,
    },
    {
      key: "daily2",
      heading,
      layout: "dayGrid",
      cadence: "daily",
      dayFrom: 17,
      dayTo: 31,
      cell: "tick",
      attestation: true,
      rows,
    },
  ];
}

/** A slot band — WEEKLY, MONTHLY, QUARTERLY and so on. */
function slotBand(
  key: string,
  heading: string,
  cadence: Band["cadence"],
  slotCount: number,
  rows: ActivityRow[],
  beside = false,
): Band {
  return {
    key,
    heading,
    layout: "slots",
    cadence,
    slotCount,
    cell: "dateInitial",
    rows,
    beside,
  };
}

/** Rows the source left blank for the laboratory to define. */
function blankRows(count: number, prefix: string): ActivityRow[] {
  return Array.from({ length: count }, (_, i) => ({
    key: `${prefix}${i + 1}`,
    label: "",
    editableLabel: true,
  }));
}

/** The AS NEEDED / REPLACEMENTS pair that closes three of the schedules. */
function asNeededBands(): Band[] {
  return [
    slotBand("asNeeded", "AS NEEDED:", "asRequired", 1, blankRows(3, "an")),
    slotBand(
      "replacements",
      "REPLACEMENTS:",
      "asRequired",
      1,
      blankRows(3, "rep"),
      true,
    ),
  ];
}

/** NDC/DI/6.4 page 32 — source page 73. Landscape. */
export const equipmentLogBook: FormSpec = {
  id: "equipment-log-book",
  title: "EQUIPMENT LOG BOOK FORMAT",
  recordingSchedule: "(Recording schedule – Daily or when equipment is run)",
  clause: "6.4",
  pageOfClause: 32,
  sourcePage: 73,
  sourcePageSize: "A4",
  orientation: "landscape",
  sheetPeriod: "month",
  headerFields: [{ key: "equipmentName", label: "Equipment Name:" }],
  bands: [
    {
      key: "ledger",
      heading: "Date",
      layout: "pairedLedger",
      cadence: "daily",
      rows: [],
      columns: [
        {
          key: "startUpTime",
          label: "Machine Start Up Time",
          cell: "time",
          width: 12,
        },
        {
          key: "operatorSign",
          label: "Operator’s Sign",
          cell: "initial",
          width: 12,
        },
        {
          key: "shutDownTime",
          label: "Machine Shut Down Time",
          cell: "time",
          width: 12,
        },
        { key: "techSign", label: "Tech Sign", cell: "initial", width: 8 },
        { key: "remarks", label: "Remarks if any", cell: "text", width: 18 },
      ],
    },
  ],
};

/** NDC/DI/6.4 page 34 — source page 75. */
export const maintenanceCentrifuge: FormSpec = {
  id: "maintenance-centrifuge",
  title: "MAINTENANCE SCHEDULE – CENTRIFUGE",
  recordingSchedule: "(Recording schedule – Daily, Weekly, Monthly Yearly)",
  clause: "6.4",
  pageOfClause: 34,
  sourcePage: 75,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "centrifuge",
  showMonthCaption: true,
  bands: [
    ...dailyBands([
      { key: "surfaceCleaning", label: "Surface Cleaning" },
      { key: "cableConnections", label: "Check Cable connections" },
      {
        key: "dryCondensate",
        label: "Dry condensed water in",
        sublabel: "rotor chamber after use",
      },
    ]),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      { key: "disinfectChamber", label: "Disinfect chamber" },
      {
        key: "disinfectBuckets",
        label: "Disinfect rotor buckets with 1%",
        sublabel: "Hypo",
      },
    ]),
    slotBand("monthly", "MONTHLY", "monthly", 1, [
      { key: "lubricateTrunions", label: "Lubricate rotor trunions" },
    ]),
    slotBand(
      "yearly",
      "YEARLY",
      "yearly",
      1,
      [{ key: "checkCalibration", label: "Check Calibration" }],
      true,
    ),
    ...asNeededBands(),
  ],
};

/** NDC/DI/6.4 page 35 — source page 76. */
export const maintenanceMicroscope: FormSpec = {
  id: "maintenance-microscope",
  title: "MAINTENANCE SCHEDULE– MICROSCOPE",
  recordingSchedule: "(Recording schedule – Daily, Quarterly)",
  clause: "6.4",
  pageOfClause: 35,
  sourcePage: 76,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "microscope",
  bands: [
    ...dailyBands([
      { key: "surfaceCleaning", label: "Surface Cleaning" },
      {
        key: "cleanLens",
        label: "Clean Lens with soft",
        sublabel: "moisten cloth",
      },
      {
        key: "cleanOilImmersion",
        label: "Clean Oil Immersion lens with 70% Iso",
        sublabel: "Propyl Alcohol",
      },
    ]),
    slotBand("quarterly", "QUARTERLY", "quarterly", 4, [
      { key: "lubricateMoving", label: "Lubricate Moving parts" },
    ]),
  ],
};

/**
 * NDC/DI/6.4 page 36 — source page 77.
 * The source prints this schedule with no maintenance activities named; every
 * activity row is blank. The rows are therefore lab-configurable.
 */
export const maintenanceBiolis30i: FormSpec = {
  id: "maintenance-biolis-30i",
  title: "MAINTENANCE SCHEDULE – BIOLIS 30i",
  recordingSchedule: "(Recording schedule – Daily, Weekly)",
  clause: "6.4",
  pageOfClause: 36,
  sourcePage: 77,
  sourcePageSize: "A4",
  footerTitle: "Policy and procedure – Handling equipment",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "biolis-30i",
  showMonthCaption: true,
  bands: [
    ...dailyBands(blankRows(7, "d")),
    slotBand("weekly", "WEEKLY", "weekly", 5, blankRows(4, "w")),
    slotBand("yearly", "YEARLY", "yearly", 1, blankRows(1, "y")),
  ],
};

/** NDC/DI/6.4 page 37 — source page 78. */
export const maintenanceMaglumiX3: FormSpec = {
  id: "maintenance-maglumi-x3",
  title: "MAINTENANCE SCHEDULE – MAGLUMI X3",
  recordingSchedule: "(Recording schedule – Daily, Weekly, Monthly)",
  clause: "6.4",
  pageOfClause: 37,
  sourcePage: 78,
  sourcePageSize: "A4",
  footerTitle: "Policy and procedure – Handling equipment",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "maglumi-x3",
  showMonthCaption: true,
  bands: [
    ...dailyBands([
      { key: "surfaceCleaning", label: "Surface Cleaning" },
      { key: "emptyCuvetteBag", label: "Empty Cuvette bag" },
      { key: "emptyWasteTank", label: "Empty liquid waste tank" },
      {
        key: "replenishCuvettes",
        label: "Check /Replenish",
        sublabel: "cuvettes",
      },
      { key: "starterVolume", label: "Check Starter Volume" },
      {
        key: "systemLiquidVolume",
        label: "Check system liquid",
        sublabel: "volume",
      },
      {
        key: "primeSampleArm",
        label: "Prime Sample Arm,",
        sublabel: "Washer & Chamber",
      },
    ]),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      { key: "cleanPipettorWall", label: "Clean outer wall of pipettor" },
      { key: "cleanWashingProbe", label: "Clean washing probe" },
      { key: "cleanWasteProbe", label: "Clean waste liquid probe" },
      {
        key: "prime10",
        label: "Prime Sample Arm, Washer &",
        sublabel: "Chamber 10 times",
      },
    ]),
    slotBand("monthly", "MONTHLY", "monthly", 1, [
      { key: "pipeWash", label: "Run pipe wash function" },
      {
        key: "emptySystemTank",
        label: "Empty system liquid tank & wash",
        sublabel: "with disinfectant",
      },
    ]),
  ],
};

/**
 * NDC/DI/6.4 page 38 — source page 79.
 * Activity rows are blank in the source. The two footnotes are reproduced
 * verbatim; note that the background-check limits quoted are haematology
 * parameters and do not belong to an electrolyte analyser — see
 * docs/reference/DI6-source-defects.md.
 */
export const maintenanceProlyte: FormSpec = {
  id: "maintenance-prolyte",
  title: "MAINTENANCE SCHEDULE – PROLYTE",
  recordingSchedule: "(Recording schedule – Daily, Monthly)",
  clause: "6.4",
  pageOfClause: 38,
  sourcePage: 79,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "prolyte",
  showMonthCaption: true,
  bands: [
    ...dailyBands(blankRows(5, "d")),
    slotBand("weekly", "WEEKLY", "weekly", 5, blankRows(3, "w")),
    slotBand("monthly", "MONTHLY", "monthly", 1, blankRows(2, "m")),
    slotBand("yearly", "Yearly", "yearly", 1, blankRows(2, "y"), true),
    ...asNeededBands(),
  ],
  footnotes: [
    "Background Check: WBC: < 0.03 X 10³ /µL, RBC: < 0.03 X 10⁶ /µL, Hb: < 0.3 g/dl, PLT: < 7 X 10³ /µL",
    "Clean surfaces with wet tissue",
  ],
};

/** NDC/DI/6.4 page 39 — source page 80. Activity rows blank in the source. */
export const maintenanceMindray5380: FormSpec = {
  id: "maintenance-mindray-5380",
  title: "MAINTENANCE SCHEDULE – MINDRAY 5380",
  recordingSchedule: "(Recording schedule – Daily, Weekly, AR)",
  clause: "6.4",
  pageOfClause: 39,
  sourcePage: 80,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "mindray-bc-5380",
  showMonthCaption: true,
  bands: [
    ...dailyBands(blankRows(5, "d"), "DAILY"),
    slotBand("weekly", "WEEKLY", "weekly", 5, blankRows(4, "w")),
    slotBand("monthly", "MONTHLY:", "monthly", 1, blankRows(6, "m")),
    slotBand("halfYearly", "6 MONTHLY", "halfYearly", 2, blankRows(6, "h"), true),
  ],
};

/** NDC/DI/6.4 page 40 — source page 81. */
export const maintenanceBioradCfx96: FormSpec = {
  id: "maintenance-biorad-cfx96",
  title: "MAINTENANCE SCHEDULE – BIORAD CFX 96",
  recordingSchedule: "(Recording schedule – Daily, Weekly)",
  clause: "6.4",
  pageOfClause: 40,
  sourcePage: 81,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "biorad-cfx-96",
  showMonthCaption: true,
  bands: [
    ...dailyBands(
      [
        {
          key: "surfaceCleaning",
          label: "Surface cleaning using lint free tissue dipped in",
          sublabel: "70% Ethanol",
        },
        { key: "cableConnection", label: "Check Cable Connection" },
        ...blankRows(2, "d"),
      ],
      "DAILY",
    ),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      {
        key: "cleanWellChamber",
        label: "Clean well chamber using lint free tissue dipped in",
        sublabel: "70% Ethanol",
      },
    ]),
    slotBand("monthly", "MONTHLY:", "monthly", 1, blankRows(2, "m")),
    slotBand("halfYearly", "6 MONTHLY", "halfYearly", 2, blankRows(2, "h"), true),
  ],
};

/** NDC/DI/6.4 page 41 — source page 82. */
export const maintenanceRotorGene3000: FormSpec = {
  id: "maintenance-rotor-gene-3000",
  title: "MAINTENANCE SCHEDULE – ROTOR GENE 3000",
  recordingSchedule: "(Recording schedule – Daily, Weekly, 6 Monthly)",
  clause: "6.4",
  pageOfClause: 41,
  sourcePage: 82,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "rotor-gene-3000",
  showMonthCaption: true,
  bands: [
    ...dailyBands([
      {
        key: "surfaceCleaning",
        label: "Surface cleaning using lint free tissue dipped in",
        sublabel: "70% Ethanol",
      },
      { key: "cableConnection", label: "Check Cable Connection" },
    ]),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      {
        key: "cleanWellChamber",
        label: "Clean well chamber using lint free tissue dipped in 70% Ethanol",
      },
    ]),
    slotBand("halfYearly", "6 MONTHLY", "halfYearly", 2, [
      { key: "routineMaintenance", label: "Routine Maintenance" },
    ]),
    slotBand("yearly", "YEARLY", "yearly", 1, blankRows(1, "y"), true),
    ...asNeededBands(),
  ],
};

/** NDC/DI/6.4 page 42 — source page 83. */
export const maintenanceBioSafetyCabinet: FormSpec = {
  id: "maintenance-bio-safety-cabinet",
  title: "MAINTENANCE SCHEDULE – BIO SAFETY CABINET",
  recordingSchedule: "(Recording schedule – Daily, Weekly, Monthly, Yearly)",
  clause: "6.4",
  pageOfClause: 42,
  sourcePage: 83,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  equipmentKey: "bio-safety-cabinet",
  showMonthCaption: true,
  bands: [
    ...dailyBands([
      { key: "surfaceCleaning", label: "Surface Cleaning" },
      {
        key: "disinfectInternal",
        label: "Disinfect internal working",
        sublabel: "area and instruments",
      },
      { key: "airFlow", label: "Check Air Flow condition" },
      {
        key: "workbenchAlcohol",
        label: "Clean workbench with",
        sublabel: "alcohol",
      },
      {
        key: "frontShutter",
        label: "Clean front shutter with mild",
        sublabel: "soap solution",
      },
      { key: "uvLight", label: "Check UV Light" },
    ]),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      { key: "cleanUvLamp", label: "Clean UV lamp" },
    ]),
    slotBand("monthly", "MONTHLY", "monthly", 1, [
      { key: "cleanHepa", label: "Clean HEPA Filters" },
      { key: "swipeTest", label: "Do swipe test" },
      {
        key: "externalHardware",
        label: "Check all external hardware & tighten if found loose",
      },
      { key: "airCulture", label: "Do Area / Air culture" },
    ]),
    slotBand(
      "yearly",
      "YEARLY",
      "yearly",
      1,
      [{ key: "checkCalibration", label: "Check Calibration" }],
      true,
    ),
  ],
};

/** NDC/DI/6.4 page 43 — source page 84. */
export const decontaminationSchedule: FormSpec = {
  id: "decontamination-schedule",
  title: "DECONTAMINATION SCHEDULE – EQUIPMENT",
  recordingSchedule: "(Recording schedule – Daily, Weekly, Monthly)",
  clause: "6.4",
  pageOfClause: 43,
  sourcePage: 84,
  sourcePageSize: "A4",
  orientation: "portrait",
  sheetPeriod: "month",
  showMonthCaption: true,
  bands: [
    ...dailyBands(
      [
        { key: "allPipettes", label: "All Pipettes" },
        { key: "allTimers", label: "All Timers" },
      ],
      "DAILY",
    ),
    slotBand("weekly", "WEEKLY", "weekly", 5, [
      { key: "allCentrifuges", label: "All Centrifuges" },
      { key: "allIncubators", label: "All Incubators" },
      { key: "allMicroscopes", label: "All Microscopes" },
      { key: "allThermometers", label: "All Thermometers" },
      { key: "allThermoHygrometers", label: "All Thermo Hygrometers" },
      { key: "rollerMixer", label: "Roller / Mixer" },
    ]),
    slotBand("monthly", "MONTHLY", "monthly", 1, [
      { key: "allRefrigerator", label: "All Refrigerator" },
    ]),
    slotBand("yearly", "YEARLY", "yearly", 1, blankRows(1, "y")),
  ],
};

export const equipmentForms: FormSpec[] = [
  equipmentLogBook,
  maintenanceCentrifuge,
  maintenanceMicroscope,
  maintenanceBiolis30i,
  maintenanceMaglumiX3,
  maintenanceProlyte,
  maintenanceMindray5380,
  maintenanceBioradCfx96,
  maintenanceRotorGene3000,
  maintenanceBioSafetyCabinet,
  decontaminationSchedule,
];

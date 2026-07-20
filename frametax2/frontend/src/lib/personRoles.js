// Canonical person-role schema — ONE inventory shared by Overview's
// Production Facts panel and Workspace's Inputs panel, mirroring the
// backend's _PEOPLE_ROLE_KEYS exactly. Discovery (script/budget/upload
// extraction) fills the first four; the lead-cast slots stay editable
// before anyone is discovered; dop/editor/composer are the recurring
// cultural-test creative roles extracted from the populated
// cultural_qualification_model rules DB (composer: au_producer_offset +
// uk_avec point rules; editor + dop: BFI AVEC weighted crew sections).
// Rendering from this list keeps the two surfaces automatically in sync.
export const PERSON_ROLES = [
  { key: "writer", label: "Writer", dataKey: "writers" },
  { key: "director", label: "Director", dataKey: "directors" },
  { key: "producer", label: "Producer(s)", dataKey: "producers" },
  { key: "lead_cast", label: "Lead Cast 1", dataKey: "cast" },
  { key: "lead_cast_2", label: "Lead Cast 2", dataKey: "lead_cast_2" },
  { key: "lead_cast_3", label: "Lead Cast 3", dataKey: "lead_cast_3" },
  { key: "dop", label: "Dir. of Photography", dataKey: "dop", cultural: true },
  { key: "editor", label: "Editor", dataKey: "editor", cultural: true },
  { key: "composer", label: "Composer", dataKey: "composer", cultural: true },
];

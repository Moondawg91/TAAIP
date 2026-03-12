export type Echelon = "CMD" | "BDE" | "BN" | "CO" | "STN";

export type UnitOption = {
  id?: number;
  unit_key: string;
  rsid?: string;
  display_name: string;
  echelon_type: Echelon;
  parent_key?: string;
  sort_order?: number;
};

export type OrgUnitSelection = {
  cmd: UnitOption;
  bde?: UnitOption | null;
  bn?: UnitOption | null;
  co?: UnitOption | null;
  stn?: UnitOption | null;
};

export type ActiveUnitContext = {
  selection: OrgUnitSelection;
  activeUnitKey: string;
  activeEchelon: Echelon;
  pathLabel: string;
};

/**
 * Snapshot JSON shape (build_snapshot.py 출력 일치)
 */
export type Stage = "취부" | "용접" | "마감" | "검사" | "전처리" | "도장" | "발송" | "시공";

export const STAGES: Stage[] = ["취부", "용접", "마감", "검사", "전처리", "도장", "발송", "시공"];

export interface Member {
  id: string;
  pkg: string | null;
  hoki: string;
  team: string | null;
  category: string | null;
  material: string | null;
  item: string | null;
  kind: string | null;
  section: string | null;
  spec: string | null;
  memberSize: string | null;
  lengthMm: number;
  qty: number;
  weightKg: number;
  paintM2: number;
  grid: string | null;
  취부_actual: string | null;
  용접_actual: string | null;
  마감_actual: string | null;
  검사_actual: string | null;
  전처리_actual: string | null;
  도장_actual: string | null;
  발송_actual: string | null;
  시공_actual: string | null;
}

export interface Meta {
  generatedAt: string;
  totalMembers: number;
  totalWeightT: number;
  totalPaintM2: number;
  sections: string[];
  hokis: string[];
  teams: string[];
  items: string[];
  stages: string[];
  lastInstallDate: string | null;
  dataSource: { chk: string; grid: string };
}

export interface Snapshot {
  meta: Meta;
  members: Member[];
}

export type Basis = "수량" | "중량";

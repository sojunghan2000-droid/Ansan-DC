/**
 * 브라우저 사이드 xlsx → Member[] 파서
 *
 * Python 측 lib/data_loader.py 와 동일한 컬럼 매핑/단계 추출 로직.
 * SheetJS(xlsx 패키지)를 동적으로 import해서 초기 번들 크기 영향 최소화.
 */
import type { Member } from "./types";

/** CHK LIST 시트 → 표준 컬럼 매핑 (0-indexed) */
const CHK_HEADER: Record<number, keyof Member | "ignored"> = {
  0: "pkg", // PKG NO.
  1: "team", // 팀
  2: "category", // 구분
  3: "material", // 재질
  4: "item", // ITEM
  5: "spec", // 내역
  7: "section", // 절주
  14: "kind", // 종류
  15: "id", // 부재명 (key)
  16: "memberSize",
  17: "lengthMm",
  18: "qty",
  19: "weightKg",
  22: "paintM2",
};

/** 단계별 실적일 컬럼 인덱스 (0-indexed) */
const STAGE_ACTUAL_COL: Record<string, number> = {
  취부: 24, // C25
  용접: 28, // C29
  마감: 32, // C33
  검사: 36, // C37
  전처리: 39, // C40
  도장: 43, // C44
  발송: 47, // C48
  시공: 89, // C90 (현장 실적일자)
};

/** 그리드 마스터 컬럼 (0-indexed) */
const GRID_HEADER = {
  member_no: 0, // DWGNO.
  description: 1, // DESCRIPTION
  grid: 7, // GIRD
};

interface RawCell {
  v?: unknown;
  w?: string;
  t?: string;
}

function hokiOf(pkg: unknown): string {
  if (pkg === null || pkg === undefined || pkg === "") return "(미분류)";
  const s = String(pkg).trim();
  if (s === "None" || s === "nan") return "(미분류)";
  return s;
}

function toNum(v: unknown): number {
  if (v === null || v === undefined || v === "") return 0;
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function toStr(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  return String(v).trim() || null;
}

function toIsoDate(v: unknown): string | null {
  if (v === null || v === undefined || v === "") return null;
  if (v instanceof Date) {
    if (Number.isNaN(v.getTime())) return null;
    if (v.getFullYear() < 2000) return null;
    return v.toISOString().split("T")[0];
  }
  if (typeof v === "number" && v > 0) {
    // Excel serial date (1900 origin, day count)
    // SheetJS with cellDates:true usually returns Date, but fall back here
    const ms = Math.round((v - 25569) * 86400 * 1000);
    const d = new Date(ms);
    if (d.getFullYear() < 2000) return null;
    return d.toISOString().split("T")[0];
  }
  if (typeof v === "string") {
    const d = new Date(v);
    if (Number.isNaN(d.getTime()) || d.getFullYear() < 2000) return null;
    return d.toISOString().split("T")[0];
  }
  return null;
}

export interface ParseResult {
  members: Member[];
  warnings: string[];
}

export async function parseExcels(
  chkFile: File,
  gridFile: File | null,
): Promise<ParseResult> {
  // 동적 import — 사용자가 업로드할 때만 SheetJS 로딩
  const XLSX = await import("xlsx");
  const warnings: string[] = [];

  // ── CHK LIST 파싱 ──────────────────────────────────────
  const chkBuf = await chkFile.arrayBuffer();
  const chkWb = XLSX.read(chkBuf, { type: "array", cellDates: true });
  const chkSheetName =
    chkWb.SheetNames.find((n) => n === "CHK LIST") ??
    chkWb.SheetNames.find((n) => n.toUpperCase().includes("CHK")) ??
    chkWb.SheetNames[0];
  if (!chkSheetName) {
    throw new Error("xlsx에서 'CHK LIST' 시트를 찾지 못했습니다.");
  }
  const chkSheet = chkWb.Sheets[chkSheetName];

  // R8(0-indexed 7)부터 데이터 시작, header:1로 배열 형태
  const chkRows = XLSX.utils.sheet_to_json<unknown[]>(chkSheet, {
    header: 1,
    defval: null,
    range: 7,
    raw: true,
  });

  const members: Member[] = [];
  for (const row of chkRows) {
    if (!Array.isArray(row)) continue;
    const id = row[15];
    if (!id) continue; // 부재명 없는 행 스킵

    const m: Member = {
      id: String(id).trim(),
      pkg: toStr(row[0]),
      hoki: hokiOf(row[0]),
      team: toStr(row[1]) ?? "(미배정)",
      category: toStr(row[2]),
      material: toStr(row[3]),
      item: toStr(row[4]) ?? "(미분류)",
      kind: toStr(row[14]),
      section: toStr(row[7]) ?? "(미배정)",
      spec: toStr(row[5]),
      memberSize: toStr(row[16]),
      lengthMm: Math.round(toNum(row[17])),
      qty: Math.round(toNum(row[18])),
      weightKg: toNum(row[19]),
      paintM2: toNum(row[22]),
      grid: null,
      취부_actual: toIsoDate(row[STAGE_ACTUAL_COL["취부"]]),
      용접_actual: toIsoDate(row[STAGE_ACTUAL_COL["용접"]]),
      마감_actual: toIsoDate(row[STAGE_ACTUAL_COL["마감"]]),
      검사_actual: toIsoDate(row[STAGE_ACTUAL_COL["검사"]]),
      전처리_actual: toIsoDate(row[STAGE_ACTUAL_COL["전처리"]]),
      도장_actual: toIsoDate(row[STAGE_ACTUAL_COL["도장"]]),
      발송_actual: toIsoDate(row[STAGE_ACTUAL_COL["발송"]]),
      시공_actual: toIsoDate(row[STAGE_ACTUAL_COL["시공"]]),
    };
    members.push(m);
  }

  if (members.length === 0) {
    warnings.push("CHK LIST에서 부재 데이터를 찾지 못했습니다. (R8부터 데이터가 있어야 합니다)");
  }

  // ── 그리드 마스터 (선택) ─────────────────────────────────
  if (gridFile) {
    const gBuf = await gridFile.arrayBuffer();
    const gWb = XLSX.read(gBuf, { type: "array", cellDates: false });
    const gSheetName =
      gWb.SheetNames.find((n) => n === "Sheet1") ?? gWb.SheetNames[0];
    if (gSheetName) {
      const gSheet = gWb.Sheets[gSheetName];
      const gRows = XLSX.utils.sheet_to_json<unknown[]>(gSheet, {
        header: 1,
        defval: null,
        range: 1, // R2부터 (헤더 R1 스킵)
      });
      const gridMap = new Map<string, string>();
      for (const row of gRows) {
        if (!Array.isArray(row)) continue;
        const dwg = row[GRID_HEADER.member_no];
        const grid = row[GRID_HEADER.grid];
        if (!dwg || !grid) continue;
        const key = String(dwg).trim();
        if (!gridMap.has(key)) gridMap.set(key, String(grid).trim());
      }
      // members에 grid 채우기
      let matched = 0;
      for (const m of members) {
        const g = gridMap.get(m.id);
        if (g) {
          m.grid = g;
          matched++;
        } else {
          m.grid = "(미지정)";
        }
      }
      warnings.push(
        `그리드 매핑: ${matched.toLocaleString()} / ${members.length.toLocaleString()} 부재 매칭됨`,
      );
    } else {
      warnings.push("그리드 파일에서 시트를 찾지 못했습니다.");
      members.forEach((m) => (m.grid = "(미지정)"));
    }
  } else {
    members.forEach((m) => (m.grid = "(미지정)"));
    warnings.push("그리드 파일이 업로드되지 않아 GRID 정보는 '(미지정)' 입니다.");
  }

  return { members, warnings };
}

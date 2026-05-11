import type { Member, Stage } from "./types";

export interface KPIs {
  total: number;
  totalWeightT: number;
  totalPaintM2: number;
  shipDone: number;
  installDone: number;
  shipPct: number;
  installPct: number;
}

export function computeKPIs(members: Member[]): KPIs {
  const total = members.length;
  const totalWeightT = members.reduce((s, m) => s + m.weightKg, 0) / 1000;
  const totalPaintM2 = members.reduce((s, m) => s + m.paintM2, 0);
  const shipDone = members.filter((m) => m.발송_actual !== null).length;
  const installDone = members.filter((m) => m.시공_actual !== null).length;
  return {
    total,
    totalWeightT: round1(totalWeightT),
    totalPaintM2: round1(totalPaintM2),
    shipDone,
    installDone,
    shipPct: total ? round1((100 * shipDone) / total) : 0,
    installPct: total ? round1((100 * installDone) / total) : 0,
  };
}

export interface HokiRow {
  hoki: string;
  total: number;
  ship: number;
  install: number;
  weightT: number;
}

export function byHoki(members: Member[]): HokiRow[] {
  const map = new Map<string, HokiRow>();
  for (const m of members) {
    const h = m.hoki || "(미분류)";
    if (!map.has(h)) map.set(h, { hoki: h, total: 0, ship: 0, install: 0, weightT: 0 });
    const row = map.get(h)!;
    row.total++;
    if (m.발송_actual) row.ship++;
    if (m.시공_actual) row.install++;
    row.weightT += m.weightKg / 1000;
  }
  return [...map.values()]
    .map((r) => ({ ...r, weightT: round1(r.weightT) }))
    .sort((a, b) => a.hoki.localeCompare(b.hoki, "ko"));
}

export interface CrossRow {
  hoki: string;
  zone: string;
  total: number;
  ship: number;
  install: number;
  weightT: number;
  shipPct: number;
  installPct: number;
}

export function byHokiZone(members: Member[]): CrossRow[] {
  const map = new Map<string, CrossRow>();
  for (const m of members) {
    const h = m.hoki || "(미분류)";
    const z = m.section || "(미분류)";
    const k = `${h}|${z}`;
    if (!map.has(k))
      map.set(k, {
        hoki: h,
        zone: z,
        total: 0,
        ship: 0,
        install: 0,
        weightT: 0,
        shipPct: 0,
        installPct: 0,
      });
    const r = map.get(k)!;
    r.total++;
    if (m.발송_actual) r.ship++;
    if (m.시공_actual) r.install++;
    r.weightT += m.weightKg / 1000;
  }
  return [...map.values()]
    .map((r) => ({
      ...r,
      weightT: round1(r.weightT),
      shipPct: r.total ? round1((100 * r.ship) / r.total) : 0,
      installPct: r.total ? round1((100 * r.install) / r.total) : 0,
    }))
    .sort((a, b) =>
      a.hoki === b.hoki ? a.zone.localeCompare(b.zone, "ko") : a.hoki.localeCompare(b.hoki, "ko"),
    );
}

export interface DailyPoint {
  date: string;
  count: number;
  cumCount: number;
  weightT: number;
  cumWeightT: number;
}

export function dailyCumulative(members: Member[], stage: Stage): DailyPoint[] {
  const key = `${stage}_actual` as keyof Member;
  const bucket = new Map<string, { count: number; weightT: number }>();
  for (const m of members) {
    const d = m[key] as string | null;
    if (!d) continue;
    if (!bucket.has(d)) bucket.set(d, { count: 0, weightT: 0 });
    const b = bucket.get(d)!;
    b.count++;
    b.weightT += m.weightKg / 1000;
  }
  const sorted = [...bucket.entries()].sort(([a], [b]) => a.localeCompare(b));
  let cumCount = 0;
  let cumWeightT = 0;
  return sorted.map(([date, { count, weightT }]) => {
    cumCount += count;
    cumWeightT += weightT;
    return {
      date,
      count,
      cumCount,
      weightT: round2(weightT),
      cumWeightT: round2(cumWeightT),
    };
  });
}

function round1(n: number) {
  return Math.round(n * 10) / 10;
}
function round2(n: number) {
  return Math.round(n * 100) / 100;
}

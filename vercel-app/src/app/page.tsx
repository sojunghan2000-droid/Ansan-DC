"use client";

import { useMemo, useState } from "react";
import { data } from "@/lib/data";
import { byHoki, byHokiZone, computeKPIs, dailyCumulative } from "@/lib/kpi";
import type { Basis } from "@/lib/types";
import { SegmentedControl } from "@/components/SegmentedControl";
import { Gauge } from "@/components/Gauge";
import { HokiBar } from "@/components/HokiBar";
import { ProgressTable } from "@/components/ProgressTable";
import { CumulativeLine } from "@/components/CumulativeLine";

const ALL = "전체" as const;
type Hoki = typeof ALL | string;
type Zone = typeof ALL | string;

export default function DashboardPage() {
  const { meta, members } = data;

  const hokiOptions: Hoki[] = useMemo(() => [ALL, ...meta.hokis], [meta.hokis]);
  const zoneOptions: Zone[] = useMemo(() => [ALL, ...meta.sections], [meta.sections]);

  const [hoki, setHoki] = useState<Hoki>(ALL);
  const [zone, setZone] = useState<Zone>(ALL);
  const [basis, setBasis] = useState<Basis>("수량");

  const filtered = useMemo(() => {
    return members.filter((m) => {
      if (hoki !== ALL && m.hoki !== hoki) return false;
      if (zone !== ALL && m.section !== zone) return false;
      return true;
    });
  }, [members, hoki, zone]);

  const kpi = useMemo(() => computeKPIs(filtered), [filtered]);
  const hokiRows = useMemo(() => byHoki(filtered), [filtered]);
  const crossRows = useMemo(() => byHokiZone(filtered), [filtered]);
  const shipDaily = useMemo(() => dailyCumulative(filtered, "발송"), [filtered]);
  const installDaily = useMemo(() => dailyCumulative(filtered, "시공"), [filtered]);

  return (
    <main className="dash-root">
      {/* 헤더 */}
      <div className="topbar">
        <h1>🏗️ 안산 글로벌 클라우드센터 — 시공 실적 대시보드</h1>
        <div className="meta">
          데이터 기준일 : <b>{meta.lastInstallDate ?? "-"}</b> · 입결 표준 기반 · 총{" "}
          {meta.totalMembers.toLocaleString()}부재
        </div>
      </div>

      {/* 필터 행 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          gap: "1.2rem",
          alignItems: "end",
        }}
      >
        <SegmentedControl<Hoki>
          label="PRD 호기"
          options={hokiOptions}
          value={hoki}
          onChange={setHoki}
        />
        <SegmentedControl<Zone>
          label="PRD Zone (절주)"
          options={zoneOptions}
          value={zone}
          onChange={setZone}
        />
        <SegmentedControl<Basis>
          label="기준 단위"
          options={["수량", "중량"] as const}
          value={basis}
          onChange={setBasis}
        />
      </div>

      {/* KPI 행: 게이지 2 + 호기별 막대 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 2.4fr",
          gap: "0.5rem",
        }}
      >
        <Gauge title="PRD 천공 (발송)" done={kpi.shipDone} total={kpi.total} color="#F5A623" />
        <Gauge title="PRD 철골 설치 (시공)" done={kpi.installDone} total={kpi.total} color="#4CAF50" />
        <HokiBar rows={hokiRows} />
      </div>

      {/* 데이터 행: 표 + 누적 라인 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.5fr 2.5fr",
          gap: "0.5rem",
          minHeight: 0,
        }}
      >
        <ProgressTable rows={crossRows} />
        <CumulativeLine shipDaily={shipDaily} installDaily={installDaily} basis={basis} />
      </div>
    </main>
  );
}

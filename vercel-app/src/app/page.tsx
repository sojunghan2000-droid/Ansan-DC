"use client";

import { useEffect, useMemo, useState } from "react";
import { data as baseData } from "@/lib/data";
import { byHoki, byHokiZone, computeKPIs, dailyCumulative } from "@/lib/kpi";
import type { Basis, Member } from "@/lib/types";
import { SegmentedControl } from "@/components/SegmentedControl";
import { Gauge } from "@/components/Gauge";
import { HokiBar } from "@/components/HokiBar";
import { ProgressTable } from "@/components/ProgressTable";
import { CumulativeLine } from "@/components/CumulativeLine";
import { UploadModal } from "@/components/UploadModal";

const ALL = "전체" as const;
type Hoki = typeof ALL | string;
type Zone = typeof ALL | string;

export default function DashboardPage() {
  // ── 데이터 소스: 기본 snapshot 또는 사용자 업로드 ───────
  const [uploadedMembers, setUploadedMembers] = useState<Member[] | null>(null);
  const [uploadToast, setUploadToast] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const members = uploadedMembers ?? baseData.members;

  // 메타는 동적으로 계산 (업로드 시 자동 갱신)
  const meta = useMemo(() => {
    const sections = [...new Set(members.map((m) => m.section).filter(Boolean))].sort() as string[];
    const hokis = [
      ...new Set(members.map((m) => m.hoki).filter((h) => h && h !== "(미분류)")),
    ].sort() as string[];
    const lastInstallDate = members
      .map((m) => m.시공_actual)
      .filter((d): d is string => !!d)
      .sort()
      .at(-1) ?? null;
    return { sections, hokis, lastInstallDate };
  }, [members]);

  const hokiOptions: Hoki[] = useMemo(() => [ALL, ...meta.hokis], [meta.hokis]);
  const zoneOptions: Zone[] = useMemo(() => [ALL, ...meta.sections], [meta.sections]);

  const [hoki, setHoki] = useState<Hoki>(ALL);
  const [zone, setZone] = useState<Zone>(ALL);
  const [basis, setBasis] = useState<Basis>("수량");

  // 업로드 데이터 변경 시, 선택된 옵션이 더 이상 유효하지 않으면 '전체'로 리셋
  useEffect(() => {
    if (hoki !== ALL && !meta.hokis.includes(hoki)) setHoki(ALL);
    if (zone !== ALL && !meta.sections.includes(zone)) setZone(ALL);
  }, [meta.hokis, meta.sections, hoki, zone]);

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

  function handleApplyUpload(newMembers: Member[], warnings: string[]) {
    setUploadedMembers(newMembers);
    const msg = [
      `✓ 사용자 업로드 데이터 적용 (${newMembers.length.toLocaleString()} 부재)`,
      ...warnings,
    ].join("\n");
    setUploadToast(msg);
    setTimeout(() => setUploadToast(null), 5000);
  }

  function handleResetData() {
    setUploadedMembers(null);
    setUploadToast(`↺ 기본 샘플 데이터로 복원 (${baseData.members.length.toLocaleString()} 부재)`);
    setTimeout(() => setUploadToast(null), 3500);
  }

  const isUploaded = uploadedMembers !== null;

  return (
    <main className="dash-root">
      {/* 헤더 */}
      <div className="topbar">
        <h1>
          🏗️ 안산 글로벌 클라우드센터 — 시공 실적 대시보드
          {isUploaded && <span className="badge-uploaded">사용자 업로드</span>}
        </h1>
        <div className="meta" style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <span>
            데이터 기준일 : <b>{meta.lastInstallDate ?? "-"}</b> · 총{" "}
            {members.length.toLocaleString()}부재
          </span>
          <button
            type="button"
            className="btn-upload"
            onClick={() => setShowUploadModal(true)}
            title="입결 표준 양식 엑셀 두 개를 업로드해서 데이터 갱신"
          >
            📁 엑셀 업로드
          </button>
          {isUploaded && (
            <button type="button" className="btn-reset" onClick={handleResetData}>
              ↺ 기본 데이터로
            </button>
          )}
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

      <UploadModal
        open={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onApply={handleApplyUpload}
      />

      {uploadToast && <div className="toast">{uploadToast}</div>}
    </main>
  );
}

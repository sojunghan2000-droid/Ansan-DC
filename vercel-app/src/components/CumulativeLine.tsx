"use client";

import { Plot } from "./PlotlyClient";
import type { DailyPoint } from "@/lib/kpi";
import type { Basis } from "@/lib/types";

const FONT = "Pretendard, 'Noto Sans KR', sans-serif";

interface Props {
  shipDaily: DailyPoint[];
  installDaily: DailyPoint[];
  basis: Basis;
}

export function CumulativeLine({ shipDaily, installDaily, basis }: Props) {
  const isCount = basis === "수량";
  const unit = isCount ? "건" : "ton";
  const yKey: keyof DailyPoint = isCount ? "cumCount" : "cumWeightT";

  return (
    <div className="card" style={{ height: "100%" }}>
      <Plot
        data={[
          {
            type: "scatter",
            mode: "lines+markers",
            name: "발송 누적",
            x: shipDaily.map((d) => d.date),
            y: shipDaily.map((d) => d[yKey] as number),
            line: { color: "#F5A623", width: 2.5 },
            marker: { size: 5 },
            fill: "tozeroy",
            fillcolor: "rgba(245, 166, 35, 0.08)",
          },
          {
            type: "scatter",
            mode: "lines+markers",
            name: "시공 누적",
            x: installDaily.map((d) => d.date),
            y: installDaily.map((d) => d[yKey] as number),
            line: { color: "#4CAF50", width: 3 },
            marker: {
              size: 10,
              symbol: "diamond",
              line: { width: 1.5, color: "white" },
            },
          },
        ]}
        layout={{
          title: {
            text: `PRD 진행현황 — 일자별 누적 (${unit} 기준)`,
            x: 0.02,
            y: 0.97,
            font: { size: 12, color: "#1F3A68" },
          },
          margin: { l: 36, r: 16, t: 32, b: 32 },
          paper_bgcolor: "white",
          plot_bgcolor: "white",
          font: { family: FONT, size: 10 },
          legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.02,
            x: 0.6,
            xanchor: "center",
            font: { size: 9 },
          },
          xaxis: { showgrid: true, gridcolor: "#EEF2F7", tickfont: { size: 9 } },
          yaxis: {
            showgrid: true,
            gridcolor: "#EEF2F7",
            tickfont: { size: 9 },
            title: { text: unit, font: { size: 10 } },
          },
          hovermode: "x unified",
          autosize: true,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}

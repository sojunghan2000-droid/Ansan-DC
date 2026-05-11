"use client";

import { Plot } from "./PlotlyClient";
import type { HokiRow } from "@/lib/kpi";

const FONT = "Pretendard, 'Noto Sans KR', sans-serif";

export function HokiBar({ rows }: { rows: HokiRow[] }) {
  return (
    <div className="card">
      <Plot
        data={[
          {
            type: "bar",
            name: "계획",
            x: rows.map((r) => r.hoki),
            y: rows.map((r) => r.total),
            text: rows.map((r) => r.total.toString()),
            textposition: "outside",
            marker: { color: "#CBD5E1" },
            textfont: { size: 10 },
          },
          {
            type: "bar",
            name: "발송 실적",
            x: rows.map((r) => r.hoki),
            y: rows.map((r) => r.ship),
            text: rows.map((r) => r.ship.toString()),
            textposition: "outside",
            marker: { color: "#F5A623" },
            textfont: { size: 10 },
          },
          {
            type: "bar",
            name: "시공 실적",
            x: rows.map((r) => r.hoki),
            y: rows.map((r) => r.install),
            text: rows.map((r) => r.install.toString()),
            textposition: "outside",
            marker: { color: "#4CAF50" },
            textfont: { size: 10 },
          },
        ]}
        layout={{
          title: { text: "호기별 계획 / 실적", x: 0.02, y: 0.97, font: { size: 12, color: "#1F3A68" } },
          barmode: "group",
          height: 170,
          margin: { l: 36, r: 10, t: 26, b: 28 },
          paper_bgcolor: "white",
          plot_bgcolor: "white",
          font: { family: FONT, size: 10 },
          legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.02,
            x: 0.5,
            xanchor: "center",
            font: { size: 9 },
          },
          xaxis: { tickfont: { size: 10 } },
          yaxis: { showgrid: true, gridcolor: "#EEF2F7", tickfont: { size: 9 } },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "170px" }}
        useResizeHandler
      />
    </div>
  );
}

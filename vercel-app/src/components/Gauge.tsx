"use client";

import { Plot } from "./PlotlyClient";

interface Props {
  title: string;
  done: number;
  total: number;
  color: string;
}

const FONT = "Pretendard, 'Noto Sans KR', sans-serif";

export function Gauge({ title, done, total, color }: Props) {
  const pct = total ? (100 * done) / total : 0;

  return (
    <div className="card">
      <Plot
        data={[
          {
            type: "indicator",
            mode: "gauge+number",
            value: pct,
            number: { suffix: "%", font: { size: 26, color: "#1F3A68" } },
            gauge: {
              axis: { range: [0, 100], tickwidth: 1, tickcolor: "#9CA3AF", tickfont: { size: 8 } },
              bar: { color, thickness: 0.85 },
              bgcolor: "#F3F4F6",
              borderwidth: 0,
              steps: [
                { range: [0, 30], color: "#FEF3C7" },
                { range: [30, 70], color: "#FDE68A" },
                { range: [70, 100], color: "#FCD34D" },
              ],
            },
            domain: { x: [0, 1], y: [0, 0.85] },
          },
        ]}
        layout={{
          height: 170,
          margin: { l: 6, r: 6, t: 22, b: 22 },
          paper_bgcolor: "white",
          font: { family: FONT },
          annotations: [
            {
              text: `<b>${title}</b>`,
              x: 0.5,
              y: 1.06,
              xref: "paper",
              yref: "paper",
              showarrow: false,
              font: { size: 12, color: "#1F3A68" },
            },
            {
              text: `${done.toLocaleString()} / ${total.toLocaleString()}건`,
              x: 0.5,
              y: -0.06,
              xref: "paper",
              yref: "paper",
              showarrow: false,
              font: { size: 10, color: "#6B7280" },
            },
          ],
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height: "170px" }}
        useResizeHandler
      />
    </div>
  );
}

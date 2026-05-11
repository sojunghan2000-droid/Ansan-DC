"use client";

import dynamic from "next/dynamic";

/**
 * Plotly의 react-plotly.js/factory가 내부적으로 CommonJS(require)를 쓰므로
 * Next.js 서버 번들에서 제외해야 함.
 * → 실제 import는 PlotlyImpl.tsx에서만 하고, 여기서는 dynamic({ ssr:false })로 감쌈.
 */
export const Plot = dynamic(
  () => import("./PlotlyImpl").then((m) => m.PlotImpl),
  { ssr: false, loading: () => <div style={{ fontSize: "0.78rem", color: "#9ca3af" }}>차트 로딩…</div> },
);

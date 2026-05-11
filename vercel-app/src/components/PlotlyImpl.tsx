"use client";

// 실제 Plotly + factory는 이 파일에만 import.
// PlotlyClient.tsx에서 dynamic({ ssr:false })으로만 로드 → 서버 번들에서 완전히 제외.
import Plotly from "plotly.js-dist-min";
import createPlotComponent from "react-plotly.js/factory";

export const PlotImpl = createPlotComponent(Plotly);

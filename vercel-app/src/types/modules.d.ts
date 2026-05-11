// Plotly 외부 모듈 타입 보강

declare module "plotly.js-dist-min" {
  const Plotly: unknown;
  export default Plotly;
}

declare module "react-plotly.js/factory" {
  import type { ComponentType } from "react";
  import type { PlotParams } from "react-plotly.js";
  const createPlotComponent: (Plotly: unknown) => ComponentType<PlotParams>;
  export default createPlotComponent;
}

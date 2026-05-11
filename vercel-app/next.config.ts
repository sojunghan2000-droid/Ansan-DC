import path from "node:path";
import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  // 부모 디렉토리(C:\Users\user)의 package.json("type":"module")과 충돌 방지
  // → 이 프로젝트 루트를 명시
  outputFileTracingRoot: path.join(__dirname),
  // Plotly의 react-plotly.js/factory가 CJS(require) 사용 → 서버 번들에서 제외
  serverExternalPackages: ["plotly.js-dist-min", "react-plotly.js"],
};

export default config;

# Ansan DC Dashboard — Vercel (Next.js)

Power BI 스타일 1-screen 시공 실적 대시보드 — Next.js 15 + Plotly.js + Vercel.
Streamlit 버전(`/streamlit_app.py`)과 동일한 데이터/필터/시각화를 React로 재구성.

## 구조

```
vercel-app/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx          # 메인 1-screen 대시보드
│   │   └── globals.css
│   ├── components/           # 차트/필터 클라이언트 컴포넌트
│   │   ├── SegmentedControl.tsx
│   │   ├── Gauge.tsx          # Plotly Indicator (게이지)
│   │   ├── HokiBar.tsx        # 호기별 계획/실적 클러스터 막대
│   │   ├── ProgressTable.tsx  # 호기 × Zone 진척표
│   │   ├── CumulativeLine.tsx # 발송/시공 누적 라인
│   │   ├── PlotlyClient.tsx   # dynamic({ ssr:false }) 래퍼
│   │   └── PlotlyImpl.tsx     # 실제 plotly-min + factory
│   ├── lib/
│   │   ├── data.ts            # snapshot.json import
│   │   ├── kpi.ts             # 클라이언트 집계 함수
│   │   └── types.ts           # Snapshot/Member 타입
│   └── types/modules.d.ts     # plotly 외부 모듈 선언
├── public/data/snapshot.json  # 빌드 타임 데이터 (407KB, 929부재)
├── scripts/build_snapshot.py  # xlsx → JSON 변환기 (루트 lib/ 재사용)
└── package.json
```

## 빠른 시작 (로컬)

```bash
npm install
npm run dev    # → http://localhost:3000
```

## 데이터 갱신

루트의 `data/samples/*.xlsx`를 새 파일로 교체 후:

```bash
python scripts/build_snapshot.py
# → public/data/snapshot.json 갱신
git add public/data/snapshot.json && git commit && git push
# Vercel 자동 재배포
```

## Vercel 배포 설정

- **Root Directory**: `vercel-app`
- **Framework**: Next.js (자동 감지)
- **Build Command**: `next build` (기본)
- **Install Command**: `npm install` (기본)

## 기술 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| 데이터 fetch | 빌드 타임 JSON import | Vercel 정적 호스팅 최적화, 런타임 fetch 불필요 |
| 차트 | Plotly.js (dist-min) | Streamlit 버전과 시각적 일관성, 게이지 지원 |
| Plotly SSR | `dynamic({ ssr:false })` | factory 패키지가 CJS `require` 사용 → 서버 번들에서 제외 |
| 스타일 | Tailwind 4 + custom CSS | 1-screen 레이아웃을 위한 정밀 제어 |

## 알려진 제약

- **path with spaces/한글**: 로컬 dev는 `C:\dev\` 같은 ASCII-only 경로에서 실행 권장. Vercel은 Linux 컨테이너이므로 무관.
- **사용자 업로드 미지원**: 현재는 빌드 타임 스냅샷만. Streamlit 버전은 런타임 업로드 지원하므로 용도별로 분리 사용.

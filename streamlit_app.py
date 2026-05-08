"""안산 데이터센터 시공 실적 — 통합 대시보드 (1-Screen)

Power BI 패턴: 상단 필터 버튼(호기/Zone/단계) + 게이지 + 호기별 막대 + 진척표 + 누적 라인
세로 스크롤 없이 한 화면에 모든 핵심 KPI/차트 배치.
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import DEFAULT_CHK, DEFAULT_GRID, load_dataset
from lib.kpi import compute_kpis, daily_cumulative
from lib.std import COLOR_PALETTE

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="안산 DC 시공 실적 대시보드",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 1-Screen용 컴팩트 CSS ────────────────────────────────────
st.markdown(
    """
    <style>
      html, body, [class*="css"] {
        font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
      }
      /* 메인 컨테이너 패딩 최소화 */
      .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
        max-width: 100% !important;
      }
      /* 헤더 바 */
      .topbar {
        background: linear-gradient(135deg, #1F3A68 0%, #2A5298 100%);
        color: white;
        padding: 0.55rem 1rem;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.55rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      }
      .topbar h1 { font-size: 1.05rem; margin: 0; font-weight: 700; }
      .topbar .meta { font-size: 0.78rem; opacity: 0.92; }
      /* segmented_control 컴팩트 */
      [data-testid="stSegmentedControl"] button {
        font-size: 0.82rem !important;
        padding: 0.3rem 0.7rem !important;
      }
      /* metric 카드 컴팩트 */
      [data-testid="stMetric"] {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 0.5rem 0.7rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
      }
      [data-testid="stMetricLabel"] p { font-size: 0.75rem; color: #6B7280; }
      [data-testid="stMetricValue"] { color: #1F3A68; font-size: 1.4rem !important; font-weight: 700; }
      [data-testid="stMetricDelta"] { font-size: 0.72rem; }
      /* 섹션 라벨 */
      .sect-label {
        font-size: 0.78rem; color: #6B7280; font-weight: 600;
        margin: 0.15rem 0 0.05rem 0; letter-spacing: 0.02em;
      }
      /* dataframe 컴팩트 */
      [data-testid="stDataFrame"] { font-size: 0.78rem; }
      /* hide streamlit deploy/menu by default for cleaner view */
      [data-testid="stToolbar"] { display: none; }
      footer { display: none; }
      header[data-testid="stHeader"] { background: transparent; height: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── 데이터 로드 ───────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _data():
    return load_dataset(DEFAULT_CHK, DEFAULT_GRID)


def _hoki_of(pkg) -> str:
    """pkg → 호기 라벨 (원본 값 사용, 미분류만 정리)"""
    if pkg is None or pkg == "" or str(pkg) in ("None", "nan"):
        return "(미분류)"
    return str(pkg).strip()


df_all = _data()
df_all = df_all.copy()
df_all["호기"] = df_all["pkg"].apply(_hoki_of)

ALL_HOKI = ["전체"] + sorted([h for h in df_all["호기"].unique() if h != "(미분류)"])
ALL_ZONE = ["전체"] + sorted(df_all["section"].unique().tolist())
STAGE_PAIR = [
    ("발송", "PRD 천공 (≈ 출하)"),
    ("시공", "PRD 철골 설치"),
]

# ── 헤더 ──────────────────────────────────────────────────────
recent = df_all["시공_actual"].dropna()
last_date = pd.to_datetime(recent).max().date().isoformat() if len(recent) else "-"
st.markdown(
    f"""
    <div class="topbar">
      <h1>🏗️ 안산 글로벌 클라우드센터 — 시공 실적 대시보드</h1>
      <div class="meta">데이터 기준일: <b>{last_date}</b> · 입결 표준 기반 · 총 {len(df_all):,}부재</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 필터 행 (호기 / Zone / 보조) ─────────────────────────────
fc1, fc2, fc3 = st.columns([1.4, 2.5, 1.0])
with fc1:
    st.markdown('<div class="sect-label">PRD 호기</div>', unsafe_allow_html=True)
    sel_hoki = st.segmented_control("호기", ALL_HOKI, default="전체",
                                    key="f_hoki", label_visibility="collapsed")
with fc2:
    st.markdown('<div class="sect-label">PRD Zone (절주)</div>', unsafe_allow_html=True)
    sel_zone = st.segmented_control("Zone", ALL_ZONE, default="전체",
                                    key="f_zone", label_visibility="collapsed")
with fc3:
    st.markdown('<div class="sect-label">기준 단위</div>', unsafe_allow_html=True)
    sel_basis = st.segmented_control("기준", ["수량(건)", "중량(ton)"], default="수량(건)",
                                     key="f_basis", label_visibility="collapsed")

# 필터 적용
df = df_all
if sel_hoki and sel_hoki != "전체":
    df = df[df["호기"] == sel_hoki]
if sel_zone and sel_zone != "전체":
    df = df[df["section"] == sel_zone]

if df.empty:
    st.warning("선택한 필터 조건에 해당하는 부재가 없습니다.")
    st.stop()

is_count = (sel_basis or "수량(건)").startswith("수량")

# ── KPI 게이지 + 호기별 막대 (Row 2) ─────────────────────────
g1, g2, g3 = st.columns([1.0, 1.0, 2.4])


def _gauge(title: str, done: int, total: int, color: str) -> go.Figure:
    pct = (100 * done / total) if total else 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 30, "color": "#1F3A68"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#9CA3AF",
                     "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.85},
            "bgcolor": "#F3F4F6",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "#FEF3C7"},
                {"range": [30, 70], "color": "#FDE68A"},
                {"range": [70, 100], "color": "#FCD34D"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 0.85]},
    ))
    fig.add_annotation(
        text=f"<b>{title}</b>", x=0.5, y=1.05, xref="paper", yref="paper",
        showarrow=False, font=dict(size=13, color="#1F3A68"),
    )
    fig.add_annotation(
        text=f"{done:,} / {total:,}건", x=0.5, y=-0.08, xref="paper", yref="paper",
        showarrow=False, font=dict(size=11, color="#6B7280"),
    )
    fig.update_layout(
        height=190, margin=dict(l=8, r=8, t=22, b=22),
        paper_bgcolor="white", font=dict(family="Pretendard, 'Noto Sans KR', sans-serif"),
    )
    return fig


total = len(df)
ship_done = df["발송_actual"].notna().sum()
inst_done = df["시공_actual"].notna().sum()

with g1:
    st.plotly_chart(_gauge("PRD 천공 (발송)", int(ship_done), total, COLOR_PALETTE["accent"]),
                    use_container_width=True, key="gauge1")
with g2:
    st.plotly_chart(_gauge("PRD 철골 설치 (시공)", int(inst_done), total, COLOR_PALETTE["success"]),
                    use_container_width=True, key="gauge2")
with g3:
    # 호기별 계획(=총량) vs 실적(시공+발송)
    h_grp = df.groupby("호기", dropna=False).agg(
        총량=("member_no", "count"),
        발송=("발송_actual", lambda s: s.notna().sum()),
        시공=("시공_actual", lambda s: s.notna().sum()),
    ).reset_index().sort_values("호기")

    fig_h = go.Figure()
    fig_h.add_trace(go.Bar(
        x=h_grp["호기"], y=h_grp["총량"], name="계획",
        marker_color="#CBD5E1",
        text=h_grp["총량"], textposition="outside", textfont=dict(size=10),
    ))
    fig_h.add_trace(go.Bar(
        x=h_grp["호기"], y=h_grp["발송"], name="발송 실적",
        marker_color=COLOR_PALETTE["accent"],
        text=h_grp["발송"], textposition="outside", textfont=dict(size=10),
    ))
    fig_h.add_trace(go.Bar(
        x=h_grp["호기"], y=h_grp["시공"], name="시공 실적",
        marker_color=COLOR_PALETTE["success"],
        text=h_grp["시공"], textposition="outside", textfont=dict(size=10),
    ))
    fig_h.update_layout(
        title=dict(text="호기별 계획 / 실적", x=0.02, y=0.97,
                   font=dict(size=13, color="#1F3A68")),
        barmode="group", height=190,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.45,
                    font=dict(size=10)),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_h, use_container_width=True, key="hoki_bar")

# ── 진척표 + 누적 라인 (Row 3) ───────────────────────────────
t_col, l_col = st.columns([1.5, 2.5])

with t_col:
    st.markdown('<div class="sect-label">호기 × Zone 진척 현황</div>', unsafe_allow_html=True)
    grp = df.groupby(["호기", "section"], dropna=False).agg(
        계획=("member_no", "count"),
        발송=("발송_actual", lambda s: s.notna().sum()),
        시공=("시공_actual", lambda s: s.notna().sum()),
        중량_t=("weight_kg", lambda s: round(s.sum() / 1000, 1)),
    ).reset_index()
    grp["발송율"] = (100 * grp["발송"] / grp["계획"]).round(1).astype(str) + "%"
    grp["시공율"] = (100 * grp["시공"] / grp["계획"]).round(1).astype(str) + "%"
    grp = grp.rename(columns={"section": "Zone"})

    # Total 행
    total_row = pd.DataFrame([{
        "호기": "Total", "Zone": "-",
        "계획": int(grp["계획"].sum()),
        "발송": int(grp["발송"].sum()),
        "시공": int(grp["시공"].sum()),
        "중량_t": round(df["weight_kg"].sum() / 1000, 1),
        "발송율": f"{round(100 * grp['발송'].sum() / grp['계획'].sum(), 1)}%" if grp['계획'].sum() else "0.0%",
        "시공율": f"{round(100 * grp['시공'].sum() / grp['계획'].sum(), 1)}%" if grp['계획'].sum() else "0.0%",
    }])
    grp_disp = pd.concat([total_row, grp], ignore_index=True)[
        ["호기", "Zone", "계획", "발송", "발송율", "시공", "시공율", "중량_t"]
    ]
    st.dataframe(
        grp_disp, use_container_width=True, hide_index=True, height=300,
        column_config={
            "계획": st.column_config.NumberColumn("계획", format="%d"),
            "발송": st.column_config.NumberColumn("발송", format="%d"),
            "시공": st.column_config.NumberColumn("시공", format="%d"),
            "중량_t": st.column_config.NumberColumn("중량(t)", format="%.1f"),
        },
    )

with l_col:
    # 누적 라인 2개 (발송 / 시공) 같은 차트에 stack
    daily_ship = daily_cumulative(df, stage="발송")
    daily_inst = daily_cumulative(df, stage="시공")

    val_col = "cum_count" if is_count else "cum_weight_t"
    unit = "건" if is_count else "ton"

    fig_l = go.Figure()
    if not daily_ship.empty:
        fig_l.add_trace(go.Scatter(
            x=daily_ship["date"], y=daily_ship[val_col],
            name="발송 누적", mode="lines+markers",
            line=dict(color=COLOR_PALETTE["accent"], width=2.5),
            marker=dict(size=5),
            fill="tozeroy", fillcolor="rgba(245, 166, 35, 0.08)",
        ))
    if not daily_inst.empty:
        fig_l.add_trace(go.Scatter(
            x=daily_inst["date"], y=daily_inst[val_col],
            name="시공 누적", mode="lines+markers",
            line=dict(color=COLOR_PALETTE["success"], width=3),
            marker=dict(size=10, symbol="diamond",
                        line=dict(width=1.5, color="white")),
        ))

    if not fig_l.data:
        fig_l.add_annotation(text="실적 데이터 없음", xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False,
                             font=dict(size=13, color=COLOR_PALETTE["muted"]))

    fig_l.update_layout(
        title=dict(text=f"PRD 진행현황 — 일자별 누적 ({unit} 기준)",
                   x=0.02, y=0.97, font=dict(size=13, color="#1F3A68")),
        height=300, margin=dict(l=10, r=10, t=30, b=30),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.6, font=dict(size=10)),
        xaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=10), title=""),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=10),
                   title=dict(text=unit, font=dict(size=10))),
        hovermode="x unified",
    )
    st.plotly_chart(fig_l, use_container_width=True, key="line")

# 작은 푸터 (사이드바 안내)
st.caption(
    "💡 좌측 사이드바에서 상세 분석 페이지(공정별 진척 · 그리드별 실적 · 일자별 추이 · 팀·절주별 분석 · 데이터 표준)로 이동할 수 있습니다."
)

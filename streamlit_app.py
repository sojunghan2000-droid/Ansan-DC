"""안산 글로벌 클라우드센터 — 통합 시공 대시보드

좌측 단일 네비게이션으로 6개 시트 전환. 기본 화면 = 6.4 철골 SUMMARY.
- 6.1 PRD 종합 (실제 데이터, 기존 1-screen)
- 6.2 파일 공사진행 현황
- 6.3 파일 SUMMARY
- 6.4 철골 SUMMARY (메인)
- 6.5 철골 설치 생산성
- 6.6 철근배근 생산성
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import DEFAULT_CHK, DEFAULT_GRID, load_dataset
from lib.kpi import compute_kpis, daily_cumulative
from lib.std import COLOR_PALETTE
from lib.mock_data import (
    PILE_PROGRESS, PILE_SUMMARY, STEEL_SUMMARY,
    STEEL_PRODUCTIVITY, REBAR_PRODUCTIVITY,
)

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="안산 DC 통합 대시보드",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 공통 CSS ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
      html, body, [class*="css"] {
        font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
      }
      .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 1.0rem !important;
        padding-right: 1.0rem !important;
        max-width: 100% !important;
      }
      /* 헤더 SAMSUNG 스타일 (사진 2~5 공통) */
      .samsung-header {
        background: linear-gradient(135deg, #1F3A68 0%, #2A5298 100%);
        color: white; padding: 0.5rem 1rem; border-radius: 8px;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 0.6rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      }
      .samsung-header .left { display: flex; align-items: center; gap: 0.8rem; }
      .samsung-header .brand { font-size: 0.78rem; font-weight: 600; opacity: 0.85; }
      .samsung-header h1 { font-size: 1.0rem; margin: 0; font-weight: 700; }
      .samsung-header .page-tag {
        background: rgba(255,255,255,0.15); padding: 0.2rem 0.65rem;
        border-radius: 999px; font-size: 0.74rem; font-weight: 600;
      }
      /* KPI 카드 */
      [data-testid="stMetric"] {
        background: white; border: 1px solid #E5E7EB; border-radius: 8px;
        padding: 0.5rem 0.7rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
      }
      [data-testid="stMetricLabel"] p { font-size: 0.78rem; color: #6B7280; }
      [data-testid="stMetricValue"] { color: #1F3A68; font-size: 1.5rem !important; font-weight: 700; }
      /* 섹션 라벨 */
      .sect-label {
        font-size: 0.78rem; color: #6B7280; font-weight: 600;
        margin: 0.15rem 0 0.05rem 0; letter-spacing: 0.02em;
      }
      /* 사이드바 메뉴 */
      [data-testid="stSidebar"] {
        background: #F8FAFC;
      }
      [data-testid="stSidebar"] .stRadio > label > div p { font-size: 0.88rem; font-weight: 500; }
      .sidebar-title {
        background: linear-gradient(135deg, #1F3A68 0%, #2A5298 100%);
        color: white; padding: 0.7rem 0.9rem; border-radius: 8px;
        margin-bottom: 0.8rem; font-size: 0.92rem; font-weight: 700;
      }
      .sidebar-section { font-size: 0.78rem; color: #6B7280; margin: 0.5rem 0 0.3rem 0.2rem; font-weight: 600; }
      /* 표 컴팩트 */
      [data-testid="stDataFrame"] { font-size: 0.78rem; }
      /* 도면 placeholder */
      .floorplan {
        background: repeating-linear-gradient(
          45deg, #F1F5F9, #F1F5F9 8px, #E2E8F0 8px, #E2E8F0 9px
        );
        border: 1px solid #94A3B8; border-radius: 6px;
        position: relative; min-height: 360px;
      }
      .zone-box {
        position: absolute; border: 2px solid #475569; background: rgba(255,255,255,0.85);
        border-radius: 4px; display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.78rem; color: #1F3A68;
      }
      .floorplan-legend {
        font-size: 0.72rem; color: #475569; margin-top: 0.3rem; text-align: center;
      }
      /* Hide deploy/menu */
      [data-testid="stToolbar"] { display: none; }
      footer { display: none; }
      header[data-testid="stHeader"] { background: transparent; height: 0; }
      /* 사진 4·5 표 — 컬러 강조 */
      .perf-card {
        background: #1F3A68; color: white; border-radius: 8px;
        padding: 0.6rem 0.9rem; display: flex; align-items: center; gap: 1rem;
        margin-bottom: 0.5rem;
      }
      .perf-card .label { font-size: 0.74rem; opacity: 0.8; }
      .perf-card .value { font-size: 1.5rem; font-weight: 800; }
      .perf-card .unit { font-size: 0.72rem; opacity: 0.7; }
      .delta-up { color: #4ADE80; }
      .delta-down { color: #F87171; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── 사이드바 네비 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-title">🏗️ 안산 글로벌 클라우드센터<br/>'
        '<span style="font-size:0.74rem;font-weight:500;opacity:0.85;">'
        '시공 통합 대시보드</span></div>',
        unsafe_allow_html=True,
    )
    page = st.radio(
        "📊 시트 선택",
        options=[
            "6.4 철골 SUMMARY",
            "6.1 PRD 종합",
            "6.2 파일 공사진행 현황",
            "6.3 파일 SUMMARY",
            "6.5 철골 설치 생산성",
            "6.6 철근배근 생산성",
        ],
        index=0,
    )

    st.markdown('<div class="sidebar-section">ℹ️ 정보</div>', unsafe_allow_html=True)
    st.caption(
        "데이터는 첨부 사진 5장 기준 박제값입니다. "
        "UI 확인 용도로 인원 정보는 마스킹 처리했습니다."
    )


# ── 공통 헤더 렌더 ────────────────────────────────────────────
def samsung_header(page_tag: str, title: str = "안산 글로벌 클라우드센터", subtitle: str = "Work Front Dashboard"):
    st.markdown(
        f"""
        <div class="samsung-header">
          <div class="left">
            <span class="brand">SAMSUNG · C&T Corporation</span>
            <h1>{title}</h1>
            <span style="opacity:0.75;font-size:0.78rem;">| {subtitle}</span>
          </div>
          <span class="page-tag">{page_tag}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# 6.4 철골 SUMMARY (메인/기본)
# ══════════════════════════════════════════════════════════════
def render_steel_summary():
    samsung_header("6.4 철골 SUMMARY", subtitle="철골 공사 종합")

    d = STEEL_SUMMARY

    # ── 상단 표 ────────────────────────────────────────────
    st.markdown('<div class="sect-label">철골공사 · 종합 진척</div>', unsafe_allow_html=True)
    df = pd.DataFrame(d["rows"])
    st.dataframe(df, use_container_width=True, hide_index=True, height=120)

    # ── 게이지 2 + 호기별 막대 ─────────────────────────────
    g1, g2, g3 = st.columns([1.0, 1.0, 2.4])
    with g1:
        _gauge_card(d["gauges"][0], COLOR_PALETTE["accent"])
    with g2:
        _gauge_card(d["gauges"][1], COLOR_PALETTE["success"])
    with g3:
        _hoki_bar(d["hoki_bars"])

    # ── Zone 단위 표 + 누적 라인 ───────────────────────────
    z_col, l_col = st.columns([1.4, 2.4])
    with z_col:
        st.markdown('<div class="sect-label">Zone별 천공·철골 진척</div>',
                    unsafe_allow_html=True)
        zdf = pd.DataFrame(d["zone_table"])
        st.dataframe(zdf, use_container_width=True, hide_index=True, height=265)
    with l_col:
        c1, c2 = st.columns(2)
        with c1:
            _progress_line("PRD 천공 진행현황", d["drill_line"],
                           COLOR_PALETTE["accent"])
        with c2:
            _progress_line("PRD 철골 진행현황", d["steel_line"],
                           COLOR_PALETTE["success"])


def _gauge_card(gdata, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gdata["pct"],
        number={"suffix": "%", "font": {"size": 26, "color": "#1F3A68"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"size": 9}},
            "bar": {"color": color, "thickness": 0.85},
            "bgcolor": "#F3F4F6", "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "#FEF3C7"},
                {"range": [30, 70], "color": "#FDE68A"},
                {"range": [70, 100], "color": "#FCD34D"},
            ],
        },
        domain={"x": [0, 1], "y": [0, 0.85]},
    ))
    fig.add_annotation(text=f'<b>{gdata["title"]}</b>', x=0.5, y=1.07,
                       xref="paper", yref="paper", showarrow=False,
                       font=dict(size=12, color="#1F3A68"))
    fig.add_annotation(text=f'(단위 : {gdata["unit"]})', x=0.5, y=0.92,
                       xref="paper", yref="paper", showarrow=False,
                       font=dict(size=10, color="#6B7280"))
    fig.add_annotation(text=f'{gdata["done"]:,} / {gdata["total"]:,}', x=0.5, y=-0.08,
                       xref="paper", yref="paper", showarrow=False,
                       font=dict(size=11, color="#1F3A68"))
    fig.update_layout(height=180, margin=dict(l=8, r=8, t=24, b=20),
                      paper_bgcolor="white",
                      font=dict(family="Pretendard, 'Noto Sans KR', sans-serif"))
    st.plotly_chart(fig, use_container_width=True)


def _hoki_bar(bars):
    fig = go.Figure()
    colors = {"PRD 전체": "#CBD5E1", "PRD 천공 실적": "#5DADE2", "PRD 철골 실적": "#1F3A68"}
    for label in ["PRD 전체", "PRD 천공 실적", "PRD 철골 실적"]:
        fig.add_trace(go.Bar(
            x=bars["labels"], y=bars[label], name=label,
            marker_color=colors[label],
            text=bars[label], textposition="outside",
            textfont=dict(size=10),
        ))
    fig.update_layout(
        title=dict(text="호기별 계획/실적", x=0.02, y=0.97,
                   font=dict(size=12, color="#1F3A68")),
        barmode="group", height=180,
        margin=dict(l=30, r=10, t=24, b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.5,
                    xanchor="center", font=dict(size=9)),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=9)),
    )
    st.plotly_chart(fig, use_container_width=True)


def _progress_line(title, data, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data["months"][:len(data["계획(B/L)"])], y=data["계획(B/L)"],
        name="계획(B/L)", mode="lines+markers+text",
        text=[str(v) if v else "" for v in data["계획(B/L)"]],
        textposition="top center", textfont=dict(size=8, color="#94A3B8"),
        line=dict(color="#CBD5E1", width=2, dash="dot"),
        marker=dict(size=5),
    ))
    actual = [v for v in data["실적"] if v is not None]
    fig.add_trace(go.Scatter(
        x=data["months"][:len(actual)], y=actual,
        name="실적", mode="lines+markers+text",
        text=[str(v) for v in actual],
        textposition="bottom center", textfont=dict(size=8, color=color),
        line=dict(color=color, width=2.5),
        marker=dict(size=6),
    ))
    fig.update_layout(
        title=dict(text=title, x=0.02, y=0.97,
                   font=dict(size=12, color="#1F3A68")),
        height=265, margin=dict(l=30, r=10, t=28, b=24),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.6,
                    font=dict(size=9)),
        xaxis=dict(tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=9)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 6.2 파일 공사진행 현황
# ══════════════════════════════════════════════════════════════
def render_pile_progress():
    samsung_header("6.2 파일 공사진행 현황", subtitle="현장타설말뚝")

    d = PILE_PROGRESS

    # 좌(평면도 placeholder) + 우(KPI)
    L, R = st.columns([1.5, 1.0])
    with L:
        st.markdown('<div class="sect-label">평면 배치 (Zone 추상)</div>',
                    unsafe_allow_html=True)
        # 추상 Zone 박스 다이어그램 (원본 도면 미사용)
        zones = d["zones"]
        floorplan_html = '<div class="floorplan">'
        positions = [
            ("A ZONE", 8, 25, 18, 50),
            ("B ZONE", 28, 25, 18, 50),
            ("C ZONE", 48, 25, 18, 50),
            ("D ZONE", 68, 25, 18, 50),
            ("E ZONE", 8, 12, 78, 10),
            ("F ZONE", 8, 78, 78, 10),
            ("G ZONE", 86, 25, 8, 50),
        ]
        for name, left, top, width, height in positions:
            floorplan_html += (
                f'<div class="zone-box" style="left:{left}%;top:{top}%;'
                f'width:{width}%;height:{height}%;">{name}</div>'
            )
        # 가상 시공 점 마커
        for i in range(60):
            x = 10 + (i % 12) * 6
            y = 30 + (i // 12) * 9
            floorplan_html += (
                f'<div style="position:absolute;left:{x}%;top:{y}%;'
                f'width:8px;height:8px;background:#3B82F6;border-radius:50%;'
                f'border:1px solid #1E40AF;"></div>'
            )
        floorplan_html += '</div>'
        floorplan_html += '<div class="floorplan-legend">파란 점 = 시공 완료 마커 (개념도)</div>'
        st.markdown(floorplan_html, unsafe_allow_html=True)

    with R:
        st.markdown('<div class="sect-label">공사진행 현황 (KPI)</div>',
                    unsafe_allow_html=True)
        k = d["kpi"]
        c1, c2 = st.columns(2)
        c1.metric("총 수량", f"{k['total_qty']:,}")
        c2.metric("설치(공, 누계)", f"{k['install_qty']:,}")
        c3, c4 = st.columns(2)
        c3.metric("설치(M, 누계)", f"{k['install_m']:,.2f}")
        c4.metric("진행률", f"{k['progress_pct']:.2f}")

        st.markdown(
            f"""
            <div style="background:#2A5298;color:white;padding:0.6rem 0.9rem;
                        border-radius:8px;margin-top:0.5rem;display:flex;
                        justify-content:space-around;gap:0.5rem;">
              <div style="text-align:center;">
                <div style="font-size:0.72rem;opacity:0.8;">기준일설치(공)</div>
                <div style="font-size:1.4rem;font-weight:800;">{k['today_qty']}</div>
              </div>
              <div style="text-align:center;">
                <div style="font-size:0.72rem;opacity:0.8;">기준일설치(M)</div>
                <div style="font-size:1.4rem;font-weight:800;">{k['today_m']}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sect-label" style="margin-top:0.6rem;">호기별 누적</div>',
                    unsafe_allow_html=True)
        df = pd.DataFrame(d["table"])
        st.dataframe(df, use_container_width=True, hide_index=True, height=145)


# ══════════════════════════════════════════════════════════════
# 6.3 파일 SUMMARY
# ══════════════════════════════════════════════════════════════
def render_pile_summary():
    samsung_header("6.3 파일 SUMMARY", subtitle="현장타설말뚝 종합")

    d = PILE_SUMMARY

    st.markdown('<div class="sect-label">파일공사 종합 표</div>', unsafe_allow_html=True)
    df = pd.DataFrame(d["rows"])
    st.dataframe(df, use_container_width=True, hide_index=True, height=110)

    # 라인 차트 + 우측 8개 KPI
    L, R = st.columns([2.4, 1.0])
    with L:
        wk = d["weekly_line"]
        fig = go.Figure()
        for k, color, dash in [
            ("주간계획", "#94A3B8", "solid"),
            ("주간실적", "#1F3A68", "solid"),
            ("계획(누계)", "#F87171", "dot"),
            ("실적(누계)", "#7C3AED", "dot"),
        ]:
            y = wk[k]
            fig.add_trace(go.Scatter(
                x=wk["dates"][:len(y)], y=y, name=k, mode="lines+markers+text",
                text=[str(int(v)) if v else "" for v in y],
                textposition="top center", textfont=dict(size=8),
                line=dict(color=color, width=2, dash=dash),
                marker=dict(size=5),
            ))
        fig.update_layout(
            title=dict(text="주간 계획·실적 / 누계", x=0.02, y=0.97,
                       font=dict(size=12, color="#1F3A68")),
            height=360, margin=dict(l=36, r=12, t=30, b=46),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
            legend=dict(orientation="h", yanchor="top", y=-0.12, x=0.5,
                        xanchor="center", font=dict(size=10)),
            xaxis=dict(tickangle=-40, tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=9)),
        )
        st.plotly_chart(fig, use_container_width=True)

    with R:
        st.markdown('<div class="sect-label">주차별 진척 (8주)</div>',
                    unsafe_allow_html=True)
        rows = [d["kpi_cards"][i:i + 4] for i in range(0, 8, 4)]
        for row in rows:
            cols = st.columns(4)
            for col, card in zip(cols, row):
                col.metric(card["label"], card["value"])


# ══════════════════════════════════════════════════════════════
# 6.5 철골 설치 생산성
# ══════════════════════════════════════════════════════════════
def render_steel_productivity():
    samsung_header("6.5 철골 설치 생산성", subtitle="Zone·일자별")

    d = STEEL_PRODUCTIVITY
    L, R = st.columns(2)

    with L:
        st.markdown('<div class="sect-label">Zone별 철골 설치 생산성</div>',
                    unsafe_allow_html=True)
        _perf_summary_card(d["target_ton_per_person_day"],
                           d["actual_ton_per_person_day"],
                           d["zone_perf"], unit="ton/인일")
        _perf_table(d["zone_table"])

    with R:
        st.markdown('<div class="sect-label">일자별 철골 설치 생산성</div>',
                    unsafe_allow_html=True)
        _perf_summary_card(d["target_ton_per_person_day"], None, [], unit="ton/인일")
        _perf_table(d["daily_table"])

    # 인원 출입 로그
    st.markdown('<div class="sect-label">📋 인원 출입 기록 (PII 마스킹)</div>',
                unsafe_allow_html=True)
    wdf = pd.DataFrame(d["workers"])
    st.dataframe(wdf, use_container_width=True, hide_index=True, height=85)


def _perf_summary_card(target, actual, zone_perf, unit):
    a_html = (
        f'<div style="display:flex;align-items:baseline;gap:0.3rem;">'
        f'<span class="label">실적</span>'
        f'<span class="value">{actual}</span>'
        f'<span class="unit">({unit})</span></div>'
    ) if actual is not None else ""
    zones_html = ""
    for z in zone_perf:
        arrow = "▲" if z.get("up") else "▼"
        cls = "delta-up" if z.get("up") else "delta-down"
        zones_html += (
            f'<div style="text-align:center;flex:1;">'
            f'<div style="font-size:0.72rem;opacity:0.8;">{z["name"]}</div>'
            f'<div style="font-size:1.0rem;font-weight:700;">{z["value"]} '
            f'<span class="{cls}" style="font-size:0.78rem;">'
            f'/ {z["delta"]:+.1f}{arrow}</span></div></div>'
        )
    st.markdown(
        f"""
        <div class="perf-card">
          <div>
            <div class="label">목표</div>
            <div class="value">{target}</div>
            <div class="unit">({unit})</div>
          </div>
          {a_html}
          <div style="flex:2;display:flex;gap:0.3rem;">{zones_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _perf_table(table):
    cols = table["columns"]
    rows = table["rows"]
    df = pd.DataFrame(rows, columns=cols)
    # None -> "-"
    df = df.fillna("-")
    st.dataframe(df, use_container_width=True, hide_index=True, height=345)


# ══════════════════════════════════════════════════════════════
# 6.6 철근배근 생산성
# ══════════════════════════════════════════════════════════════
def render_rebar():
    samsung_header("6.6 철근배근 생산성", subtitle="Actual Productivity per Task ID")

    d = REBAR_PRODUCTIVITY
    L, R = st.columns([2.3, 1.4])

    with L:
        _perf_summary_card(d["target"], d["actual"], d["zone_perf"], unit="-")
        _perf_table(d["task_table"])

    with R:
        st.markdown('<div class="sect-label">📋 인원 출입 기록 (마스킹)</div>',
                    unsafe_allow_html=True)
        wdf = pd.DataFrame(d["workers"])
        st.dataframe(wdf, use_container_width=True, hide_index=True, height=420)


# ══════════════════════════════════════════════════════════════
# 6.1 PRD 종합 (기존 1-screen Power BI 패턴 — 실 샘플 데이터 사용)
# ══════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="엑셀 데이터 읽는 중…")
def _real_data(chk_path: str, grid_path: str):
    return load_dataset(chk_path, grid_path)


def render_prd_overview():
    samsung_header("6.1 PRD 종합", subtitle="실데이터 기반 1-screen")

    df_all = _real_data(DEFAULT_CHK, DEFAULT_GRID).copy()
    df_all["호기"] = df_all["pkg"].apply(
        lambda p: "(미분류)" if not p or str(p) in ("None", "nan") else str(p).strip()
    )

    ALL_HOKI = ["전체"] + sorted([h for h in df_all["호기"].unique() if h != "(미분류)"])
    ALL_ZONE = ["전체"] + sorted(df_all["section"].unique().tolist())

    fc1, fc2, fc3 = st.columns([1.4, 2.5, 1.0])
    with fc1:
        st.markdown('<div class="sect-label">PRD 호기</div>', unsafe_allow_html=True)
        sel_h = st.segmented_control("h", ALL_HOKI, default="전체",
                                     key="p1_h", label_visibility="collapsed")
    with fc2:
        st.markdown('<div class="sect-label">PRD Zone (절주)</div>', unsafe_allow_html=True)
        sel_z = st.segmented_control("z", ALL_ZONE, default="전체",
                                     key="p1_z", label_visibility="collapsed")
    with fc3:
        st.markdown('<div class="sect-label">기준 단위</div>', unsafe_allow_html=True)
        sel_b = st.segmented_control("b", ["수량(건)", "중량(ton)"], default="수량(건)",
                                     key="p1_b", label_visibility="collapsed")

    df = df_all
    if sel_h and sel_h != "전체":
        df = df[df["호기"] == sel_h]
    if sel_z and sel_z != "전체":
        df = df[df["section"] == sel_z]

    if df.empty:
        st.warning("선택 조건에 부재가 없습니다.")
        return

    total = len(df)
    ship_done = int(df["발송_actual"].notna().sum())
    inst_done = int(df["시공_actual"].notna().sum())

    g1, g2, g3 = st.columns([1.0, 1.0, 2.4])
    with g1:
        _gauge_card({"title": "PRD 천공 (발송)", "unit": "건",
                     "done": ship_done, "total": total,
                     "pct": round(100 * ship_done / total, 1) if total else 0},
                    COLOR_PALETTE["accent"])
    with g2:
        _gauge_card({"title": "PRD 철골 설치 (시공)", "unit": "건",
                     "done": inst_done, "total": total,
                     "pct": round(100 * inst_done / total, 1) if total else 0},
                    COLOR_PALETTE["success"])
    with g3:
        h_grp = df.groupby("호기", dropna=False).agg(
            계획=("member_no", "count"),
            발송=("발송_actual", lambda s: s.notna().sum()),
            시공=("시공_actual", lambda s: s.notna().sum()),
        ).reset_index().sort_values("호기")
        bars = {
            "labels": h_grp["호기"].tolist(),
            "PRD 전체": h_grp["계획"].tolist(),
            "PRD 천공 실적": h_grp["발송"].tolist(),
            "PRD 철골 실적": h_grp["시공"].tolist(),
        }
        _hoki_bar(bars)

    t_col, l_col = st.columns([1.5, 2.5])
    with t_col:
        st.markdown('<div class="sect-label">호기 × Zone 진척</div>', unsafe_allow_html=True)
        grp = df.groupby(["호기", "section"], dropna=False).agg(
            계획=("member_no", "count"),
            발송=("발송_actual", lambda s: s.notna().sum()),
            시공=("시공_actual", lambda s: s.notna().sum()),
            중량_t=("weight_kg", lambda s: round(s.sum() / 1000, 1)),
        ).reset_index()
        grp["발송율"] = (100 * grp["발송"] / grp["계획"]).round(1).astype(str) + "%"
        grp["시공율"] = (100 * grp["시공"] / grp["계획"]).round(1).astype(str) + "%"
        grp = grp.rename(columns={"section": "Zone"})
        st.dataframe(
            grp[["호기", "Zone", "계획", "발송", "발송율", "시공", "시공율", "중량_t"]],
            use_container_width=True, hide_index=True, height=300,
        )

    with l_col:
        is_count = (sel_b or "수량(건)").startswith("수량")
        daily_ship = daily_cumulative(df, stage="발송")
        daily_inst = daily_cumulative(df, stage="시공")
        val_col = "cum_count" if is_count else "cum_weight_t"
        unit = "건" if is_count else "ton"
        fig = go.Figure()
        if not daily_ship.empty:
            fig.add_trace(go.Scatter(
                x=daily_ship["date"], y=daily_ship[val_col],
                name="발송 누적", mode="lines+markers",
                line=dict(color=COLOR_PALETTE["accent"], width=2.5),
                marker=dict(size=5),
                fill="tozeroy", fillcolor="rgba(245, 166, 35, 0.08)",
            ))
        if not daily_inst.empty:
            fig.add_trace(go.Scatter(
                x=daily_inst["date"], y=daily_inst[val_col],
                name="시공 누적", mode="lines+markers",
                line=dict(color=COLOR_PALETTE["success"], width=3),
                marker=dict(size=10, symbol="diamond",
                            line=dict(width=1.5, color="white")),
            ))
        fig.update_layout(
            title=dict(text=f"PRD 진행현황 — 일자별 누적 ({unit} 기준)",
                       x=0.02, y=0.97, font=dict(size=12, color="#1F3A68")),
            height=300, margin=dict(l=30, r=16, t=28, b=30),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Pretendard, 'Noto Sans KR', sans-serif", size=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0.6, font=dict(size=10)),
            xaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="#EEF2F7", tickfont=dict(size=9)),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 라우팅
# ══════════════════════════════════════════════════════════════
RENDER = {
    "6.4 철골 SUMMARY": render_steel_summary,
    "6.1 PRD 종합": render_prd_overview,
    "6.2 파일 공사진행 현황": render_pile_progress,
    "6.3 파일 SUMMARY": render_pile_summary,
    "6.5 철골 설치 생산성": render_steel_productivity,
    "6.6 철근배근 생산성": render_rebar,
}

RENDER.get(page, render_steel_summary)()

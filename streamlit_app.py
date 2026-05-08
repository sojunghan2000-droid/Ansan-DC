"""안산 데이터센터 시공 실적 대시보드 — 메인 (종합 현황)"""
from __future__ import annotations
from pathlib import Path

import streamlit as st

from lib import DEFAULT_CHK, DEFAULT_GRID, load_dataset
from lib.kpi import compute_kpis, stage_progress, by_group_progress
from lib.charts import funnel_chart, stage_progress_bar, group_progress_bar

# ── 페이지 설정 ─────────────────────────────────────────────────
st.set_page_config(
    page_title="안산 데이터센터 시공 실적 대시보드",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 공통 스타일 ─────────────────────────────────────────────────
st.markdown(
    """
    <style>
      html, body, [class*="css"] { font-family: 'Pretendard', 'Noto Sans KR', 'Malgun Gothic', sans-serif; }
      .main-header {
        background: linear-gradient(135deg, #1F3A68 0%, #2A5298 100%);
        color: white; padding: 1.4rem 1.6rem; border-radius: 10px;
        margin-bottom: 1.4rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      }
      .main-header h1 { margin: 0; font-size: 1.7rem; }
      .main-header p  { margin: 0.3rem 0 0; opacity: 0.9; font-size: 0.9rem; }
      [data-testid="stMetric"] {
        background: white; border: 1px solid #E5E7EB; border-radius: 10px;
        padding: 1rem 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      }
      [data-testid="stMetricLabel"] p { font-size: 0.85rem; color: #6B7280; }
      [data-testid="stMetricValue"]   { color: #1F3A68; font-weight: 700; }
      .info-card {
        background: #F8FAFC; border-left: 4px solid #2A5298;
        padding: 0.8rem 1rem; border-radius: 6px; margin: 0.4rem 0;
        font-size: 0.92rem; color: #374151;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 업로드 → 임시 파일 변환 ────────────────────────────────────
def _file_to_path(uploaded_file, default: str) -> str:
    """업로더에 파일이 들어오면 임시저장하여 경로 반환, 없으면 기본 샘플 경로."""
    if uploaded_file is None:
        return default
    tmp = Path(__file__).parent / ".cache" / "uploads"
    tmp.mkdir(parents=True, exist_ok=True)
    out = tmp / uploaded_file.name
    out.write_bytes(uploaded_file.getbuffer())
    return str(out)


# ── 사이드바: 데이터 입력 ──────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 데이터 입력")
    st.caption("표준 양식의 엑셀 2개를 업로드하면 즉시 반영됩니다.\n비워 두면 샘플 데이터가 사용됩니다.")
    up_chk = st.file_uploader("① CHK LIST (안산 설치물량.xlsx)", type=["xlsx"], key="up_chk")
    up_grid = st.file_uploader("② 그리드 마스터 (그리드정리.xlsx)", type=["xlsx"], key="up_grid")

    chk_path = _file_to_path(up_chk, DEFAULT_CHK)
    grid_path = _file_to_path(up_grid, DEFAULT_GRID)

    st.markdown("---")
    st.markdown("### ℹ️ 입결 데이터 표준")
    st.caption(
        "• 부재명(member_no)이 두 파일을 잇는 키입니다.\n"
        "• CHK LIST: 7단계 공정 + 시공 실적 일자\n"
        "• 그리드 마스터: 부재명-GRID 매핑\n"
        "• 표준 양식 다운로드는 *데이터 표준* 페이지 참고"
    )

# ── 데이터 로드 ────────────────────────────────────────────────
try:
    df = load_dataset(chk_path, grid_path)
except Exception as e:
    st.error(f"데이터 로드 실패: {e}")
    st.stop()

if df.empty:
    st.warning("부재 데이터가 비어 있습니다. 파일을 확인하세요.")
    st.stop()

# 세션에 공유 (다른 페이지에서 재사용)
st.session_state["df"] = df
st.session_state["chk_path"] = chk_path
st.session_state["grid_path"] = grid_path

# ── 헤더 ───────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">
      <h1>🏗️ 안산 글로벌 클라우드센터 — 시공 실적 대시보드</h1>
      <p>입결(입출력 결과) 데이터 표준 기반 · CHK LIST + 그리드 마스터 통합 시각화</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 종합 KPI ───────────────────────────────────────────────────
kpi = compute_kpis(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 부재 (행)", f"{kpi['total_members']:,}", help="CHK LIST의 부재 행 수")
c2.metric("총 중량", f"{kpi['total_weight_t']:,.1f} t")
c3.metric("총 도장면적", f"{kpi['total_paint_m2']:,.0f} ㎡")
c4.metric("절주 / 팀 수", f"{kpi['sections']} / {kpi['teams']}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("제작(용접) 진척률", f"{kpi['fab_pct']}%")
c6.metric("발송(출하) 진척률", f"{kpi['ship_pct']}%")
c7.metric("시공(설치) 진척률", f"{kpi['install_pct']}%",
          delta=f"{kpi['install_pct'] - kpi['ship_pct']:+.1f}%p vs 발송")
grid_filled = (df["grid"] != "(미지정)").sum()
c8.metric("그리드 매칭률", f"{100 * grid_filled / len(df):.1f}%",
          help=f"{grid_filled:,} / {len(df):,} 부재가 그리드 마스터와 매칭됨")

st.markdown("---")

# ── 메인 차트: 깔대기 + 진척률 ─────────────────────────────────
col_a, col_b = st.columns(2)
sp = stage_progress(df)

with col_a:
    by = st.radio("기준 단위", ["수량(건)", "중량(ton)"], horizontal=True, key="funnel_basis")
    fig = funnel_chart(sp, by="count" if by.startswith("수량") else "weight")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = stage_progress_bar(sp)
    st.plotly_chart(fig, use_container_width=True)

# ── 절주별 시공 진척 ───────────────────────────────────────────
st.markdown("### 🧱 절주(層) 단위 시공 진척")
section_df = by_group_progress(df, "section", stage="시공")
fig = group_progress_bar(section_df, "section", title="절주별 시공 진척 (완료 vs 잔여)")
st.plotly_chart(fig, use_container_width=True)

# 표 (pct 강조)
st.dataframe(
    section_df.assign(
        pct=lambda d: d["pct"].astype(str) + "%",
        weight_pct=lambda d: d["weight_pct"].astype(str) + "%",
    ).rename(columns={
        "section": "절주", "total": "총 부재(건)", "done": "시공 완료(건)",
        "pct": "수량 진척률", "weight_total_t": "총 중량(ton)",
        "weight_done_t": "시공 완료(ton)", "weight_pct": "중량 진척률",
    }),
    use_container_width=True, hide_index=True,
)

# ── 푸터 안내 ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div class="info-card">
      좌측 사이드바에서 다른 분석 페이지로 이동할 수 있습니다 ·
      <b>공정별 진척</b> / <b>그리드별 실적</b> / <b>일자별 추이</b> / <b>팀·절주 분석</b> / <b>데이터 표준</b>
    </div>
    """,
    unsafe_allow_html=True,
)

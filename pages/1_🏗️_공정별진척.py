"""공정별 진척 상세 페이지"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib import get_dataset
from lib.kpi import stage_progress
from lib.charts import funnel_chart, _layout, COLOR_PALETTE
from lib.std import STAGES

st.set_page_config(page_title="공정별 진척", page_icon="🏗️", layout="wide")
st.markdown("# 🏗️ 공정별 진척 상세")

df = get_dataset()
sp = stage_progress(df)

# 단계별 도넛 8개 (4 x 2)
st.markdown("### 단계별 진척률 게이지")
total_n = len(df)
cols = st.columns(4)
for i, stage in enumerate(STAGES):
    col = cols[i % 4]
    row = sp[sp["stage"] == stage].iloc[0]
    pct = float(row["pct_count"])
    fig = go.Figure(go.Pie(
        labels=["완료", "잔여"], values=[pct, max(0, 100 - pct)], hole=0.65,
        marker_colors=[COLOR_PALETTE["stage"][i % len(COLOR_PALETTE["stage"])], "#EEF2F7"],
        textinfo="none",
    ))
    fig.add_annotation(text=f"<b>{pct:.1f}%</b>", x=0.5, y=0.55, showarrow=False, font=dict(size=20))
    fig.add_annotation(text=f"{int(row['done_count'])} / {total_n}건",
                       x=0.5, y=0.40, showarrow=False, font=dict(size=11, color="#6B7280"))
    fig.update_layout(showlegend=False, height=220, margin=dict(l=10, r=10, t=40, b=10),
                      title=dict(text=stage, x=0.5, xanchor="center", font=dict(size=14)))
    col.plotly_chart(fig, use_container_width=True)
    if i % 4 == 3 and i < len(STAGES) - 1:
        cols = st.columns(4)

st.markdown("---")

# ── 깔대기 차트 (수량/중량 토글) ──────────────────────────────
left, right = st.columns([3, 1])
with right:
    basis = st.radio("기준", ["수량(건)", "중량(ton)"], key="basis_funnel")
with left:
    fig = funnel_chart(sp, by="count" if basis.startswith("수량") else "weight")
    st.plotly_chart(fig, use_container_width=True)

# ── 단계별 표 ─────────────────────────────────────────────────
st.markdown("### 📋 단계별 진척 요약 (표)")
sp_disp = sp.rename(columns={
    "stage": "공정 단계", "done_count": "완료(건)",
    "done_weight_t": "완료(ton)", "pct_count": "수량 진척률(%)",
    "pct_weight": "중량 진척률(%)",
})
st.dataframe(sp_disp, use_container_width=True, hide_index=True)

# ── 단계 선택 후 미진행 부재 목록 ──────────────────────────────
st.markdown("### 🔍 미진행 부재 조회")
sel = st.selectbox("단계 선택", STAGES, index=STAGES.index("시공"))
actual_col = f"{sel}_actual"
pending = df[df[actual_col].isna()].copy()
st.caption(f"**{sel}** 단계가 아직 완료되지 않은 부재: **{len(pending):,}건**")

if not pending.empty:
    show_cols = ["pkg", "team", "section", "item", "kind", "member_no",
                 "member_size", "length_mm", "qty", "weight_kg", "grid"]
    show_cols = [c for c in show_cols if c in pending.columns]
    st.dataframe(
        pending[show_cols].head(200).rename(columns={
            "pkg": "PKG", "team": "팀", "section": "절주",
            "item": "ITEM", "kind": "종류", "member_no": "부재명",
            "member_size": "MEMBERSIZE", "length_mm": "길이(mm)",
            "qty": "수량", "weight_kg": "중량(kg)", "grid": "GRID",
        }),
        use_container_width=True, hide_index=True,
    )
    if len(pending) > 200:
        st.caption(f"… 상위 200건만 표시 (전체 {len(pending):,}건)")

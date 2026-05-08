"""팀·절주·ITEM 다차원 분석 페이지"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from lib import get_dataset
from lib.kpi import by_group_progress
from lib.charts import group_progress_bar, _layout, COLOR_PALETTE

st.set_page_config(page_title="팀·절주별 분석", page_icon="👥", layout="wide")
st.markdown("# 👥 팀 · 절주 · ITEM 다차원 분석")

df = get_dataset()

# ── 컨트롤 ─────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    group_label = st.selectbox(
        "분석 기준",
        ["절주 (section)", "팀 (team)", "ITEM (item)", "재질 (material)", "PKG (pkg)"],
        index=0,
    )
with c2:
    stage = st.selectbox("기준 공정 단계", ["시공", "발송", "도장", "용접", "취부"], index=0)

label_to_col = {
    "절주 (section)": "section", "팀 (team)": "team", "ITEM (item)": "item",
    "재질 (material)": "material", "PKG (pkg)": "pkg",
}
group_col = label_to_col[group_label]

# ── 그룹별 진척 ────────────────────────────────────────────────
gp = by_group_progress(df, group_col, stage=stage)

st.markdown(f"### {group_label} 단위 **{stage}** 진척")
fig = group_progress_bar(gp, group_col, title=f"{group_label} × {stage} 진척 (완료 vs 잔여)")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    gp.assign(
        pct=lambda d: d["pct"].astype(str) + "%",
        weight_pct=lambda d: d["weight_pct"].astype(str) + "%",
    ).rename(columns={
        group_col: group_label, "total": "총 부재(건)", "done": f"{stage} 완료(건)",
        "pct": "수량 진척률", "weight_total_t": "총 중량(ton)",
        "weight_done_t": f"{stage} 완료(ton)", "weight_pct": "중량 진척률",
    }),
    use_container_width=True, hide_index=True,
)

# ── 교차 분석: 절주 × 팀 (스택 막대) ──────────────────────────
st.markdown("---")
st.markdown("### 🔀 교차 분석 — 절주 × 팀 부재 분포")

cross = df.groupby(["section", "team"], dropna=False).agg(
    부재수=("member_no", "count"),
    중량_t=("weight_kg", lambda s: s.sum() / 1000),
).reset_index()

basis_cross = st.radio("기준", ["부재수(건)", "중량(ton)"], horizontal=True, key="cross_basis")
val_col = "부재수" if basis_cross.startswith("부재수") else "중량_t"

fig = px.bar(
    cross, x="section", y=val_col, color="team",
    color_discrete_sequence=COLOR_PALETTE["stage"],
    text_auto=True,
    category_orders={"section": ["KICK-WALL", "A-1절", "A-2절", "B-1절", "B-2절", "C-1절", "C-2절"]},
)
fig.update_layout(
    height=420, barmode="stack",
    xaxis_title="절주", yaxis_title=val_col.replace("_", " "),
    legend_title="팀",
)
_layout(fig, title=f"절주 × 팀 — {val_col.replace('_', ' ')}")
st.plotly_chart(fig, use_container_width=True)

# ── 교차 분석: 절주 × ITEM (히트맵) ───────────────────────────
st.markdown("### 🌡️ 절주 × ITEM — 부재 수 히트맵")

item_pivot = df.pivot_table(
    index="section", columns="item", values="member_no", aggfunc="count", fill_value=0,
)
item_pivot = item_pivot.reindex(
    ["KICK-WALL", "A-1절", "A-2절", "B-1절", "B-2절", "C-1절", "C-2절"]
).dropna(how="all")

import plotly.graph_objects as go
fig = go.Figure(go.Heatmap(
    z=item_pivot.values, x=item_pivot.columns, y=item_pivot.index,
    text=item_pivot.values.astype(int), texttemplate="%{text}",
    colorscale=[[0, "#F8FAFC"], [0.5, "#93C5FD"], [1, "#1E40AF"]],
    hovertemplate="절주: %{y}<br>ITEM: %{x}<br>부재 수: %{z}<extra></extra>",
))
fig.update_layout(
    height=380, margin=dict(l=60, r=20, t=40, b=40),
    plot_bgcolor="white",
    font=dict(family="Pretendard, 'Noto Sans KR', sans-serif"),
)
st.plotly_chart(fig, use_container_width=True)

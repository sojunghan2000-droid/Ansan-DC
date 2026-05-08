"""일자별 실적 추이 페이지"""
from __future__ import annotations
import streamlit as st
import pandas as pd

from lib import get_dataset
from lib.kpi import daily_cumulative
from lib.charts import cumulative_line

st.set_page_config(page_title="일자별 실적 추이", page_icon="📅", layout="wide")
st.markdown("# 📅 일자별 실적 추이")

df = get_dataset()

c1, c2 = st.columns([2, 1])
with c1:
    stage = st.selectbox(
        "기준 단계", ["시공", "발송", "도장", "전처리", "검사", "마감", "용접", "취부"], index=0,
    )
with c2:
    basis = st.radio("기준 단위", ["수량(건)", "중량(ton)"], horizontal=True)

daily = daily_cumulative(df, stage=stage)

# ── KPI ────────────────────────────────────────────────────────
if not daily.empty:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("실적 발생 일수", f"{len(daily):,}일")
    k2.metric(f"{stage} 누계 (건)", f"{int(daily['cum_count'].iloc[-1]):,}")
    k3.metric(f"{stage} 누계 (ton)", f"{daily['cum_weight_t'].iloc[-1]:,.2f}")
    k4.metric("최근 일자", daily["date"].iloc[-1].isoformat())
else:
    st.info(f"'{stage}' 단계 실적이 아직 입력되지 않았습니다.")

# ── 차트 ───────────────────────────────────────────────────────
fig = cumulative_line(daily, by="count" if basis.startswith("수량") else "weight", stage=stage)
st.plotly_chart(fig, use_container_width=True)

# ── 표 ─────────────────────────────────────────────────────────
if not daily.empty:
    st.markdown("### 📋 일자별 상세")
    daily_disp = daily.rename(columns={
        "date": "일자", "daily_count": "일일 건수", "daily_weight_t": "일일 중량(ton)",
        "cum_count": "누계 건수", "cum_weight_t": "누계 중량(ton)",
    })
    st.dataframe(daily_disp, use_container_width=True, hide_index=True)

    # 다운로드
    csv = daily_disp.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 일자별 실적 CSV 다운로드", data=csv,
        file_name=f"{stage}_일자별실적.csv", mime="text/csv",
    )

# ── 다단계 비교 ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 단계별 누계 비교 (현재까지)")

import plotly.graph_objects as go
from lib.charts import _layout, COLOR_PALETTE

stages_to_compare = st.multiselect(
    "비교할 단계 선택",
    ["취부", "용접", "마감", "검사", "전처리", "도장", "발송", "시공"],
    default=["용접", "도장", "발송", "시공"],
)

fig = go.Figure()
unit = "건" if basis.startswith("수량") else "ton"
val_col = "cum_count" if basis.startswith("수량") else "cum_weight_t"
for i, s in enumerate(stages_to_compare):
    d = daily_cumulative(df, stage=s)
    if d.empty:
        continue
    fig.add_trace(go.Scatter(
        x=d["date"], y=d[val_col], name=s, mode="lines+markers",
        line=dict(width=2.5, color=COLOR_PALETTE["stage"][i % len(COLOR_PALETTE["stage"])]),
    ))
if not fig.data:
    st.info("선택한 단계에 실적 데이터가 없습니다.")
else:
    fig.update_layout(
        xaxis_title="일자", yaxis_title=f"누계 ({unit})",
        height=420,
    )
    _layout(fig, title=f"단계별 누계 비교 ({unit} 기준)")
    st.plotly_chart(fig, use_container_width=True)

"""그리드(GRID 위치)별 시공 실적 페이지"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib import get_dataset
from lib.charts import grid_heatmap_data, _layout, COLOR_PALETTE
from lib.kpi import grid_summary
from lib.data_loader import parse_grid_axes

st.set_page_config(page_title="그리드별 시공 실적", page_icon="🗺️", layout="wide")
st.markdown("# 🗺️ 그리드(GRID 위치)별 시공 실적")

df = get_dataset()

# ── 단계 선택 ──────────────────────────────────────────────────
stage = st.selectbox(
    "기준 단계 (이 단계가 완료된 부재를 '완료'로 집계)",
    ["시공", "발송", "도장", "검사", "마감", "용접", "취부"],
    index=0,
)

# ── 상위 GRID 막대 차트 ────────────────────────────────────────
fig = grid_heatmap_data(df, stage=stage)
st.plotly_chart(fig, use_container_width=True)

# ── 축 분해 (X축 = 1-2,3-4 등 / Y축 = G-H,E-F 등) ─────────────
st.markdown("### 🧭 그리드 축 분해 — X열 × Y열 매트릭스")

gs = grid_summary(df, stage=stage)
gs = gs[gs["grid"] != "(미지정)"].copy()
if gs.empty:
    st.info("그리드 정보가 매핑된 부재가 없습니다.")
else:
    parsed = gs["grid"].apply(parse_grid_axes)
    gs["axis_x"] = parsed.apply(lambda t: t[0])
    gs["axis_y"] = parsed.apply(lambda t: t[1])
    valid = gs.dropna(subset=["axis_x", "axis_y"])

    if valid.empty:
        st.info("축 분해가 가능한 그리드가 없습니다.")
    else:
        # 진척률 매트릭스 (heatmap)
        pivot_pct = valid.pivot_table(
            index="axis_y", columns="axis_x", values="pct", aggfunc="mean"
        ).fillna(-1)
        pivot_total = valid.pivot_table(
            index="axis_y", columns="axis_x", values="total", aggfunc="sum"
        ).fillna(0)

        # X축 정렬 (숫자 기반)
        def _x_key(s: str):
            try:
                return int(str(s).split("-")[0])
            except Exception:
                return 999

        x_order = sorted(pivot_pct.columns.tolist(), key=_x_key)
        y_order = sorted(pivot_pct.index.tolist())
        pivot_pct = pivot_pct.reindex(index=y_order, columns=x_order)
        pivot_total = pivot_total.reindex(index=y_order, columns=x_order)

        text_matrix = [
            [
                f"{int(pivot_total.iloc[i, j])}건<br>{pivot_pct.iloc[i, j]:.0f}%"
                if pivot_pct.iloc[i, j] >= 0 else ""
                for j in range(pivot_pct.shape[1])
            ]
            for i in range(pivot_pct.shape[0])
        ]

        fig = go.Figure(go.Heatmap(
            z=pivot_pct.values,
            x=pivot_pct.columns,
            y=pivot_pct.index,
            text=text_matrix,
            texttemplate="%{text}",
            textfont=dict(size=10),
            colorscale=[
                [0.0, "#F1F5F9"], [0.01, "#FEF3C7"],
                [0.5, "#FCD34D"], [1.0, "#10B981"],
            ],
            zmin=-1, zmax=100,
            hovertemplate="X열: %{x}<br>Y열: %{y}<br>" + stage + " 진척률: %{z:.1f}%<extra></extra>",
            colorbar=dict(title=f"{stage}<br>진척률(%)"),
        ))
        fig.update_layout(
            height=max(360, len(y_order) * 38 + 120),
            xaxis_title="X열 (기둥선 번호)",
            yaxis_title="Y열 (기둥선 알파벳)",
            margin=dict(l=60, r=20, t=40, b=60),
            plot_bgcolor="white",
            font=dict(family="Pretendard, 'Noto Sans KR', sans-serif"),
        )
        fig.update_xaxes(side="top")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "💡 셀 = X열·Y열 그리드 묶음. 각 셀에 표시되는 값은 부재 수와 평균 진척률입니다. "
            "진하게 초록일수록 완료율이 높음."
        )

# ── 미시공 그리드 우선순위 ─────────────────────────────────────
st.markdown("### ⚠️ 미시공 GRID 우선순위 (부재 수 많은 순)")
remaining = gs[(gs["pct"] < 100) & (gs["grid"] != "(미지정)")].copy()
remaining["잔여(건)"] = remaining["total"] - remaining["done"]
remaining = remaining.sort_values(["잔여(건)", "weight_total_t"], ascending=[False, False]).head(30)

st.dataframe(
    remaining.rename(columns={
        "grid": "GRID", "total": "총 부재(건)", "done": f"{stage} 완료(건)",
        "pct": f"{stage} 진척률(%)", "weight_total_t": "총 중량(ton)",
    }),
    use_container_width=True, hide_index=True,
)

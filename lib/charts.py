"""Plotly 차트 빌더 — 모두 한국어 라벨"""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from lib.std import COLOR_PALETTE, STAGES

KO_FONT = "Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif"


def _layout(fig: go.Figure, height: int = 420, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        font=dict(family=KO_FONT, size=12, color="#1F2937"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=50 if title else 30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F7", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EEF2F7", zeroline=False)
    return fig


def funnel_chart(stage_df: pd.DataFrame, by: str = "count") -> go.Figure:
    """공정 단계 깔대기 차트.

    by: 'count' (수량 기준) 또는 'weight' (중량 기준)
    """
    if stage_df.empty:
        return _layout(go.Figure(), title="공정 단계별 진척 (데이터 없음)")

    val_col = "done_count" if by == "count" else "done_weight_t"
    pct_col = "pct_count" if by == "count" else "pct_weight"
    unit = "건" if by == "count" else "ton"

    fig = go.Figure(go.Funnel(
        y=stage_df["stage"],
        x=stage_df[val_col],
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(color=COLOR_PALETTE["stage"][:len(stage_df)]),
        hovertemplate="<b>%{y}</b><br>완료: %{x:,} " + unit + "<br>진척률: %{customdata}%<extra></extra>",
        customdata=stage_df[pct_col],
    ))
    return _layout(fig, height=480, title=f"공정 단계별 누적 진척 ({unit} 기준)")


def stage_progress_bar(stage_df: pd.DataFrame) -> go.Figure:
    """단계별 진척률(수량/중량) 가로 막대."""
    if stage_df.empty:
        return _layout(go.Figure())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=stage_df["stage"], x=stage_df["pct_count"],
        name="수량 기준", orientation="h",
        marker_color=COLOR_PALETTE["secondary"],
        text=[f"{v}%" for v in stage_df["pct_count"]],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        y=stage_df["stage"], x=stage_df["pct_weight"],
        name="중량 기준", orientation="h",
        marker_color=COLOR_PALETTE["accent"],
        text=[f"{v}%" for v in stage_df["pct_weight"]],
        textposition="outside",
    ))
    fig.update_layout(barmode="group", xaxis_title="진척률 (%)", yaxis=dict(autorange="reversed"))
    fig.update_xaxes(range=[0, 110])
    return _layout(fig, height=420, title="단계별 진척률 (수량 vs 중량)")


def group_progress_bar(group_df: pd.DataFrame, group_col: str, title: str = "") -> go.Figure:
    """그룹(절주/팀/ITEM)별 시공 진척률 막대."""
    if group_df.empty:
        return _layout(go.Figure())

    df = group_df.sort_values("pct", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df[group_col].astype(str), x=df["done"],
        name="완료", orientation="h",
        marker_color=COLOR_PALETTE["success"],
        text=[f"{int(d)}" for d in df["done"]],
        textposition="inside",
        hovertemplate="<b>%{y}</b><br>완료: %{x}건<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df[group_col].astype(str), x=df["total"] - df["done"],
        name="잔여", orientation="h",
        marker_color="#E0E0E0",
        text=[f"{int(t-d)}" for t, d in zip(df["total"], df["done"])],
        textposition="inside",
        hovertemplate="<b>%{y}</b><br>잔여: %{x}건<extra></extra>",
    ))
    fig.update_layout(barmode="stack", xaxis_title="부재 수 (건)")
    return _layout(fig, height=max(300, len(df) * 35 + 100), title=title)


def cumulative_line(daily_df: pd.DataFrame, by: str = "count", stage: str = "시공") -> go.Figure:
    """일자별 일일 실적(막대) + 누계(선) 콤보."""
    if daily_df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"{stage} 실적 데이터가 아직 없습니다.",
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color=COLOR_PALETTE["muted"]))
        return _layout(fig, title=f"일자별 {stage} 실적 추이")

    daily_col = "daily_count" if by == "count" else "daily_weight_t"
    cum_col = "cum_count" if by == "count" else "cum_weight_t"
    unit = "건" if by == "count" else "ton"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily_df["date"], y=daily_df[daily_col],
        name=f"일일 {stage} ({unit})",
        marker_color=COLOR_PALETTE["secondary"],
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df[cum_col],
        name=f"누계 ({unit})",
        mode="lines+markers",
        line=dict(color=COLOR_PALETTE["accent"], width=3),
        yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title=f"일일 ({unit})", side="left"),
        yaxis2=dict(title=f"누계 ({unit})", side="right", overlaying="y", showgrid=False),
        xaxis_title="일자",
    )
    return _layout(fig, height=420, title=f"일자별 {stage} 실적 추이 ({unit} 기준)")


def grid_heatmap_data(df: pd.DataFrame, stage: str = "시공") -> go.Figure:
    """그리드(GIRD)별 부재 수 + 시공 진척 — 상위 30개."""
    if df.empty or "grid" not in df.columns:
        return _layout(go.Figure(), title="그리드별 시공 진척 (데이터 없음)")

    actual_col = f"{stage}_actual"
    g = df.groupby("grid", dropna=False)
    summary = pd.DataFrame({
        "total": g.size(),
        "done": g[actual_col].apply(lambda s: s.notna().sum()),
        "weight_t": (g["weight_kg"].sum() / 1000).round(2),
    }).reset_index()
    summary = summary[summary["grid"] != "(미지정)"]
    summary["pct"] = (100 * summary["done"] / summary["total"]).round(1).fillna(0)
    summary = summary.sort_values("total", ascending=False).head(30)

    if summary.empty:
        return _layout(go.Figure(), title="그리드별 시공 진척 (데이터 없음)")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=summary["grid"], y=summary["total"],
        name="총 부재",
        marker_color=COLOR_PALETTE["muted"],
        hovertemplate="<b>%{x}</b><br>총 부재: %{y}건<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=summary["grid"], y=summary["done"],
        name="시공 완료",
        marker_color=COLOR_PALETTE["success"],
        hovertemplate="<b>%{x}</b><br>완료: %{y}건<extra></extra>",
    ))
    fig.update_layout(barmode="overlay", xaxis_title="GRID 위치", yaxis_title="부재 수 (건)")
    fig.update_xaxes(tickangle=-40)
    return _layout(fig, height=460, title="그리드별 부재 분포 (상위 30) — 회색=총량, 초록=시공완료")


def stage_donut(stage_df: pd.DataFrame, stage_name: str) -> go.Figure:
    """단일 단계 도넛 차트 (완료/잔여)."""
    row = stage_df[stage_df["stage"] == stage_name]
    if row.empty:
        return _layout(go.Figure())
    done = int(row["done_count"].iloc[0])
    total = int(stage_df["done_count"].max() if stage_name == "취부" else 0)
    # 단순화: 전체는 stage_df의 max값으로 근사하지 않고, 별도 인자 받지 않으므로 100%-pct로
    pct = float(row["pct_count"].iloc[0])
    rest = round(100 - pct, 1)

    fig = go.Figure(go.Pie(
        labels=["완료", "잔여"],
        values=[pct, rest],
        hole=0.65,
        marker_colors=[COLOR_PALETTE["success"], "#E5E7EB"],
        textinfo="label+percent",
    ))
    fig.add_annotation(text=f"<b>{pct}%</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=22))
    return _layout(fig, height=280, title=stage_name)

"""KPI / 진척 계산"""
from __future__ import annotations
import pandas as pd
from lib.std import STAGES


def compute_kpis(df: pd.DataFrame) -> dict:
    """전체 요약 KPI."""
    if df.empty:
        return {
            "total_members": 0, "total_pcs": 0, "total_weight_t": 0,
            "total_paint_m2": 0, "sections": 0, "teams": 0,
            "fab_pct": 0, "ship_pct": 0, "install_pct": 0,
        }

    total_pcs = int(df["qty"].fillna(0).sum())
    total_weight_t = float(df["weight_kg"].fillna(0).sum()) / 1000.0
    total_paint = float(df["paint_m2"].fillna(0).sum())

    fab_done = df["용접_actual"].notna().sum()
    ship_done = df["발송_actual"].notna().sum()
    install_done = df["시공_actual"].notna().sum()
    n = len(df)

    return {
        "total_members": int(n),
        "total_pcs": total_pcs,
        "total_weight_t": round(total_weight_t, 1),
        "total_paint_m2": round(total_paint, 1),
        "sections": int(df["section"].nunique()),
        "teams": int(df["team"].nunique()),
        "fab_pct": round(100 * fab_done / n, 1) if n else 0,
        "ship_pct": round(100 * ship_done / n, 1) if n else 0,
        "install_pct": round(100 * install_done / n, 1) if n else 0,
    }


def stage_progress(df: pd.DataFrame) -> pd.DataFrame:
    """단계별 누적 완료 (수량/중량/비율)."""
    if df.empty:
        return pd.DataFrame(columns=["stage", "done_count", "done_weight_t", "pct_count", "pct_weight"])

    n = len(df)
    total_w = df["weight_kg"].fillna(0).sum()

    rows = []
    for stage in STAGES:
        done_mask = df[f"{stage}_actual"].notna()
        done_count = int(done_mask.sum())
        done_weight = float(df.loc[done_mask, "weight_kg"].fillna(0).sum())
        rows.append({
            "stage": stage,
            "done_count": done_count,
            "done_weight_t": round(done_weight / 1000, 2),
            "pct_count": round(100 * done_count / n, 1) if n else 0,
            "pct_weight": round(100 * done_weight / total_w, 1) if total_w else 0,
        })
    return pd.DataFrame(rows)


def by_group_progress(df: pd.DataFrame, group_col: str, stage: str = "시공") -> pd.DataFrame:
    """그룹(절주/팀/ITEM) 단위 진척 — done/total + pct (수량 기준)."""
    if df.empty or group_col not in df.columns:
        return pd.DataFrame(columns=[group_col, "total", "done", "pct", "weight_total_t", "weight_done_t"])

    actual_col = f"{stage}_actual"
    g = df.groupby(group_col, dropna=False)
    weight_done_t = g.apply(
        lambda s: s.loc[s[actual_col].notna(), "weight_kg"].sum() / 1000,
        include_groups=False,
    )
    out = pd.DataFrame({
        "total": g.size(),
        "done": g[actual_col].apply(lambda s: s.notna().sum()),
        "weight_total_t": g["weight_kg"].sum() / 1000,
        "weight_done_t": weight_done_t,
    }).reset_index()
    out["pct"] = (100 * out["done"] / out["total"]).round(1).fillna(0)
    out["weight_pct"] = (100 * out["weight_done_t"] / out["weight_total_t"]).round(1).fillna(0)
    return out.sort_values("total", ascending=False)


def daily_cumulative(df: pd.DataFrame, stage: str = "시공") -> pd.DataFrame:
    """일자별 일일 실적 + 누계."""
    actual_col = f"{stage}_actual"
    if df.empty or actual_col not in df.columns:
        return pd.DataFrame(columns=["date", "daily_count", "daily_weight_t", "cum_count", "cum_weight_t"])

    sub = df[df[actual_col].notna()].copy()
    if sub.empty:
        return pd.DataFrame(columns=["date", "daily_count", "daily_weight_t", "cum_count", "cum_weight_t"])

    sub["date"] = pd.to_datetime(sub[actual_col]).dt.date
    daily = sub.groupby("date").agg(
        daily_count=("member_no", "count"),
        daily_weight_t=("weight_kg", lambda s: s.sum() / 1000),
    ).reset_index()
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["cum_count"] = daily["daily_count"].cumsum()
    daily["cum_weight_t"] = daily["daily_weight_t"].cumsum().round(2)
    daily["daily_weight_t"] = daily["daily_weight_t"].round(2)
    return daily


def grid_summary(df: pd.DataFrame, stage: str = "시공") -> pd.DataFrame:
    """그리드별 시공 요약."""
    if df.empty or "grid" not in df.columns:
        return pd.DataFrame()

    actual_col = f"{stage}_actual"
    g = df.groupby("grid", dropna=False)
    out = pd.DataFrame({
        "total": g.size(),
        "done": g[actual_col].apply(lambda s: s.notna().sum()),
        "weight_total_t": (g["weight_kg"].sum() / 1000).round(2),
    }).reset_index()
    out["pct"] = (100 * out["done"] / out["total"]).round(1).fillna(0)
    return out.sort_values("total", ascending=False)

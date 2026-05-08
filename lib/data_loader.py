"""엑셀 입결 데이터 → 표준 DataFrame 변환

두 파일을 받아 정규화된 컬럼으로 통일하고 부재명 키로 조인한다.
- 안산 설치물량.xlsx → CHK LIST 시트 (R8부터 데이터)
- 그리드정리.xlsx   → Sheet1 (R2부터 데이터)
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Union

import openpyxl
import pandas as pd

from lib.std import CHK_HEADER, GRID_HEADER, STAGE_COLS

# 고속 엔진 우선 사용 (없으면 openpyxl로 폴백)
try:
    import python_calamine  # noqa: F401
    _EXCEL_ENGINE = "calamine"
except ImportError:
    _EXCEL_ENGINE = "openpyxl"

PathLike = Union[str, Path, bytes]


def _safe_date(v):
    """엑셀 셀 값을 datetime/None으로 변환. 1900년 더미값 제거."""
    if v is None or v == "" or v == "#N/A":
        return None
    if isinstance(v, datetime):
        return v if v.year > 2000 else None
    return None


def _safe_num(v):
    if v is None or v == "" or v == "#N/A":
        return 0
    try:
        f = float(v)
        return f if f == f else 0  # NaN guard
    except (TypeError, ValueError):
        return 0


def load_chk_list(file: PathLike, sheet_name: str = "CHK LIST", data_start_row: int = 8) -> pd.DataFrame:
    """CHK LIST 시트를 표준 DataFrame으로 로드.

    pandas read_excel(엔진 기반) → 정규화된 표준 컬럼으로 변환.
    """
    # 필요한 최대 컬럼 (0-idx)
    needed = set(CHK_HEADER.keys())
    for cols in STAGE_COLS.values():
        for v in cols.values():
            if v is not None:
                needed.add(v)
    max_col = max(needed) + 1

    raw = pd.read_excel(
        file,
        sheet_name=sheet_name,
        header=None,
        skiprows=data_start_row - 1,
        usecols=list(range(max_col)),
        engine=_EXCEL_ENGINE,
    )
    if raw.empty:
        return pd.DataFrame()

    # 부재명(15번 컬럼)이 없는 행 제외
    raw = raw[raw[15].notna()].reset_index(drop=True)
    if raw.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    for col_idx, key in CHK_HEADER.items():
        s = raw[col_idx] if col_idx in raw.columns else pd.Series([None] * len(raw))
        if key in ("length_mm", "qty"):
            out[key] = pd.to_numeric(s, errors="coerce").fillna(0).astype(int)
        elif key in ("weight_kg", "paint_m2"):
            out[key] = pd.to_numeric(s, errors="coerce").fillna(0.0)
        else:
            out[key] = s.where(pd.notna(s), None)

    for stage, cols in STAGE_COLS.items():
        for kind, idx in cols.items():
            key = f"{stage}_{kind}"
            if idx is None or idx not in raw.columns:
                out[key] = None if kind in ("plan", "actual") else 0.0
                continue
            s = raw[idx]
            if kind in ("plan", "actual"):
                d = pd.to_datetime(s, errors="coerce")
                out[key] = d.where(d.dt.year > 2000, pd.NaT)
            else:
                out[key] = pd.to_numeric(s, errors="coerce").fillna(0.0)

    out["member_no"] = out["member_no"].astype(str).str.strip()
    out["section"] = out["section"].fillna("(미배정)").astype(str)
    out["team"] = out["team"].fillna("(미배정)").astype(str)
    out["item"] = out["item"].fillna("(미분류)").astype(str)
    return out


def load_grid_master(file: PathLike, sheet_name: str = "Sheet1", data_start_row: int = 2) -> pd.DataFrame:
    """그리드정리 파일을 표준 DataFrame으로 로드 (pandas read_excel)."""
    max_col = max(GRID_HEADER.keys()) + 1
    raw = pd.read_excel(
        file, sheet_name=sheet_name, header=None,
        skiprows=data_start_row - 1, usecols=list(range(max_col)),
        engine=_EXCEL_ENGINE,
    )
    if raw.empty:
        return pd.DataFrame()
    raw = raw[raw[0].notna()].reset_index(drop=True)
    if raw.empty:
        return pd.DataFrame()

    out = pd.DataFrame()
    for col_idx, key in GRID_HEADER.items():
        s = raw[col_idx] if col_idx in raw.columns else pd.Series([None] * len(raw))
        if key in ("length_mm", "qty"):
            out[key] = pd.to_numeric(s, errors="coerce").fillna(0).astype(int)
        elif key in ("paint_unit", "weight_unit"):
            out[key] = pd.to_numeric(s, errors="coerce").fillna(0.0)
        else:
            out[key] = s.where(pd.notna(s), None)

    out["member_no"] = out["member_no"].astype(str).str.strip()
    out["grid"] = out["grid"].fillna("(미지정)").astype(str).str.strip()
    return out


def merge_with_grid(chk: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    """CHK LIST(부재 진척) + 그리드 마스터(설치 위치)를 left join."""
    if chk.empty:
        return chk
    if grid.empty or "member_no" not in grid.columns:
        chk = chk.copy()
        chk["grid"] = "(미지정)"
        return chk

    grid_unique = grid.drop_duplicates(subset=["member_no"], keep="first")[
        ["member_no", "grid", "description"]
    ]
    merged = chk.merge(grid_unique, on="member_no", how="left", suffixes=("", "_g"))
    merged["grid"] = merged["grid"].fillna("(미지정)")
    return merged


def parse_grid_axes(grid_str: str) -> tuple[str | None, str | None]:
    """'3-5/G-H' → ('3-5', 'G-H'). 파싱 불가 시 (None, None)."""
    if not grid_str or grid_str == "(미지정)":
        return None, None
    parts = str(grid_str).split("/")
    if len(parts) != 2:
        return None, None
    return parts[0].strip(), parts[1].strip()

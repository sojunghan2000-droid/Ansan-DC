"""Ansan Data Center Construction Performance Dashboard - 라이브러리"""
from pathlib import Path

import streamlit as st

from lib.std import STAGE_COLS, STAGES, GRID_HEADER, CHK_HEADER, COLOR_PALETTE
from lib.data_loader import load_chk_list, load_grid_master, merge_with_grid
from lib.kpi import compute_kpis, stage_progress, by_group_progress
from lib.charts import (
    funnel_chart, stage_progress_bar, group_progress_bar,
    cumulative_line, grid_heatmap_data,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
DEFAULT_CHK = str(DATA_DIR / "안산_설치물량_샘플.xlsx")
DEFAULT_GRID = str(DATA_DIR / "그리드정리_샘플.xlsx")


@st.cache_data(show_spinner="엑셀 데이터를 읽는 중…")
def load_dataset(chk_path: str, grid_path: str):
    """캐시된 통합 데이터셋 로더 (모든 페이지에서 공유)."""
    chk = load_chk_list(chk_path)
    grid = load_grid_master(grid_path)
    return merge_with_grid(chk, grid)


def get_dataset():
    """현재 세션의 (chk_path, grid_path)로 데이터 로드.

    페이지 진입 직후 호출하면 메인 페이지를 거치지 않아도 샘플 데이터로 동작.
    """
    chk_path = st.session_state.get("chk_path", DEFAULT_CHK)
    grid_path = st.session_state.get("grid_path", DEFAULT_GRID)
    df = load_dataset(chk_path, grid_path)
    st.session_state["df"] = df
    st.session_state["chk_path"] = chk_path
    st.session_state["grid_path"] = grid_path
    return df


__all__ = [
    "STAGE_COLS", "STAGES", "GRID_HEADER", "CHK_HEADER", "COLOR_PALETTE",
    "load_chk_list", "load_grid_master", "merge_with_grid",
    "compute_kpis", "stage_progress", "by_group_progress",
    "funnel_chart", "stage_progress_bar", "group_progress_bar",
    "cumulative_line", "grid_heatmap_data",
    "load_dataset", "get_dataset", "DEFAULT_CHK", "DEFAULT_GRID",
]

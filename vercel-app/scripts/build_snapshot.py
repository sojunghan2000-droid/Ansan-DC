"""안산 DC 입결 데이터 → Next.js public/data/snapshot.json 빌드

빌드 타임에 한 번 실행: `python scripts/build_snapshot.py`
- 두 엑셀 파일(CHK LIST + 그리드 마스터)을 읽어 정규화 JSON으로 굳힘
- Next.js는 이 JSON을 import 또는 fetch해서 클라이언트에서 필터/집계
- 데이터 갱신 시: 새 xlsx 넣고 스크립트 재실행 → git commit/push → Vercel 자동 재빌드
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, date
from pathlib import Path

# Windows console UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 프로젝트 루트(vercel-app의 부모)의 lib 사용 (Streamlit 버전과 동일 로더)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.data_loader import load_chk_list, load_grid_master, merge_with_grid  # noqa: E402
from lib.std import STAGES  # noqa: E402

CHK = ROOT / "data" / "samples" / "안산_설치물량_샘플.xlsx"
GRID = ROOT / "data" / "samples" / "그리드정리_샘플.xlsx"
OUT = Path(__file__).resolve().parent.parent / "public" / "data" / "snapshot.json"


import pandas as pd  # noqa: E402


def _iso(v):
    if v is None or pd.isna(v):
        return None
    if hasattr(v, "isoformat"):
        try:
            return v.date().isoformat() if hasattr(v, "date") else v.isoformat()
        except Exception:
            return None
    return None


def _safe(v):
    """pandas NaN/NaT → None, 나머지는 원본."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _hoki_of(pkg) -> str:
    if pkg is None or pkg == "" or str(pkg) in ("None", "nan"):
        return "(미분류)"
    return str(pkg).strip()


def main():
    print(f"[snapshot] Loading {CHK.name}…")
    chk = load_chk_list(str(CHK))
    print(f"[snapshot] Loading {GRID.name}…")
    grid = load_grid_master(str(GRID))
    print(f"[snapshot] Merging ({len(chk)} chk × {len(grid)} grid)…")
    df = merge_with_grid(chk, grid)

    members = []
    for _, r in df.iterrows():
        member = {
            "id": str(r["member_no"]),
            "pkg": _safe(r.get("pkg")),
            "hoki": _hoki_of(r.get("pkg")),
            "team": _safe(r.get("team")),
            "category": _safe(r.get("category")),
            "material": _safe(r.get("material")),
            "item": _safe(r.get("item")),
            "kind": _safe(r.get("kind")),
            "section": _safe(r.get("section")),
            "spec": _safe(r.get("spec")),
            "memberSize": _safe(r.get("member_size")),
            "lengthMm": int(r.get("length_mm") or 0),
            "qty": int(r.get("qty") or 0),
            "weightKg": float(r.get("weight_kg") or 0.0),
            "paintM2": float(r.get("paint_m2") or 0.0),
            "grid": _safe(r.get("grid")),
        }
        for s in STAGES:
            member[f"{s}_actual"] = _iso(r.get(f"{s}_actual"))
        members.append(member)

    # Meta 정보
    install_dates = df["시공_actual"].dropna()
    last_install = None
    if len(install_dates):
        last_install = _iso(install_dates.max())

    meta = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "totalMembers": int(len(df)),
        "totalWeightT": round(float(df["weight_kg"].sum()) / 1000, 2),
        "totalPaintM2": round(float(df["paint_m2"].sum()), 1),
        "sections": sorted(df["section"].dropna().unique().tolist()),
        "hokis": sorted(
            list({_hoki_of(p) for p in df["pkg"].dropna().unique() if _hoki_of(p) != "(미분류)"})
        ),
        "teams": sorted(df["team"].dropna().unique().tolist()),
        "items": sorted(df["item"].dropna().unique().tolist()),
        "stages": list(STAGES),
        "lastInstallDate": last_install,
        "dataSource": {
            "chk": CHK.name,
            "grid": GRID.name,
        },
    }

    payload = {"meta": meta, "members": members}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"[snapshot] ✓ Wrote {OUT.relative_to(ROOT)} ({size_kb:.1f} KB, {len(members)} members)")
    print(f"[snapshot]   meta: hokis={meta['hokis']}, sections={len(meta['sections'])}, lastInstall={last_install}")


if __name__ == "__main__":
    main()

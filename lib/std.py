"""입결(입출력 결과) 데이터 표준 정의

두 원본 엑셀 파일의 컬럼 구조를 그대로 표준으로 받아들이고,
대시보드 내부에서 사용하는 정규화된 키 이름과의 매핑을 한곳에 모은다.
"""
from __future__ import annotations

# ─── 공정 단계 정의 ───────────────────────────────────────────
# CHK LIST 시트의 0-indexed 컬럼 인덱스 (R7 헤더 기준)
# 각 단계는 계획일/실적일/수량/중량 4개 컬럼 묶음 (전처리만 3개)
STAGE_COLS = {
    "취부":   {"plan": 23, "actual": 24, "qty": 25, "wgt": 26},   # C24~27
    "용접":   {"plan": 27, "actual": 28, "qty": 29, "wgt": 30},   # C28~31
    "마감":   {"plan": 31, "actual": 32, "qty": 33, "wgt": 34},   # C32~35
    "검사":   {"plan": 35, "actual": 36, "qty": 37, "wgt": 38},   # C36~39
    "전처리": {"plan": None, "actual": 39, "qty": 40, "wgt": 41}, # C40~42
    "도장":   {"plan": 42, "actual": 43, "qty": 44, "wgt": 45},   # C43~46 (wgt 자리는 면적)
    "발송":   {"plan": 46, "actual": 47, "qty": 48, "wgt": 49},   # C47~50
    "시공":   {"plan": None, "actual": 89, "qty": 90, "wgt": 91}, # C90~92 (현장설치 실적)
}

STAGES = list(STAGE_COLS.keys())

# CHK LIST 표준 컬럼 (정규화 후)
CHK_HEADER = {
    0:  "pkg",         # PKG NO. (KICK/A1/A2…)
    1:  "team",        # 팀
    2:  "category",    # 구분 (NRC/일반철골)
    3:  "material",    # 재질 (SS275/SHN355…)
    4:  "item",        # ITEM (COLUMN/BEAM/GIRDER…)
    5:  "spec",        # 내역
    7:  "section",     # 절주 (KICK-WALL/A-1절…)
    8:  "grid_x",      # X
    9:  "grid_y",      # Y
    14: "kind",        # 종류 (기둥/보…)
    15: "member_no",   # 부재명 (A0C-001…) ← 키
    16: "member_size", # MEMBERSIZE
    17: "length_mm",   # 길이
    18: "qty",         # 수량
    19: "weight_kg",   # 중량
    22: "paint_m2",    # 도장 면적
}

# 그리드정리 파일 표준 컬럼 (1-indexed → 0-indexed로 매핑)
GRID_HEADER = {
    0: "member_no",     # DWGNO. (A1B-001…)  ← 키
    1: "description",   # DESCRIPTION
    2: "member_size",   # MEMBERSIZE
    3: "qty",           # Qty.
    4: "length_mm",     # Length
    5: "paint_unit",    # TotalPaint
    6: "weight_unit",   # Total
    7: "grid",          # GIRD ← 핵심 (예: "3-5/G-H")
    8: "remark",        # REMARK
}

# 색상 팔레트 (네이비 톤 + 포인트)
COLOR_PALETTE = {
    "primary":   "#1F3A68",
    "secondary": "#2A5298",
    "accent":    "#F5A623",
    "success":   "#4CAF50",
    "warning":   "#FF9800",
    "danger":    "#E53935",
    "muted":     "#90A4AE",
    "stage": [
        "#90CAF9", "#64B5F6", "#42A5F5", "#1E88E5",
        "#1565C0", "#0D47A1", "#FFA726", "#EF5350",
    ],
}

# 입결 데이터 표준 명세 (UI 표시용)
INPUT_STANDARD_SPEC = [
    # (필드, 한글명, 타입, 필수, 설명)
    ("member_no",   "부재명",       "str",   True,  "고유 식별자 (예: A0C-001) — 그리드 마스터와 조인 키"),
    ("section",     "절주",         "str",   True,  "공정 단위 절주 (KICK-WALL, A-1절 …)"),
    ("team",        "팀",           "str",   True,  "제작 담당 팀 (창ENG2, 창ENG, 장안 …)"),
    ("category",    "구분",         "str",   True,  "NRC / 일반철골"),
    ("item",        "ITEM",         "str",   True,  "COLUMN / BEAM / GIRDER / COVER_PLATE …"),
    ("kind",        "종류",         "str",   False, "기둥 / 보 등 세부 분류"),
    ("material",    "재질",         "str",   True,  "SS275, SHN355 등 강재 재질"),
    ("member_size", "MEMBERSIZE",   "str",   True,  "단면 규격 (예: L100*100*13)"),
    ("length_mm",   "길이(mm)",     "int",   True,  "부재 길이"),
    ("qty",         "수량",         "int",   True,  "동일 부재 개수"),
    ("weight_kg",   "중량(kg)",     "float", True,  "부재 단위 중량"),
    ("paint_m2",    "도장면적(㎡)", "float", False, "도장 표면적"),
    ("grid",        "GRID",         "str",   True,  "설치 위치 (그리드정리 파일 기준, 예: 3-5/G-H)"),
    ("취부_actual", "취부 실적일",  "date",  False, "공정 1단계 완료일"),
    ("용접_actual", "용접 실적일",  "date",  False, "공정 2단계 완료일"),
    ("마감_actual", "마감 실적일",  "date",  False, "공정 3단계 완료일"),
    ("검사_actual", "검사 실적일",  "date",  False, "공정 4단계 완료일"),
    ("전처리_actual", "전처리 실적일", "date", False, "공정 5단계 완료일"),
    ("도장_actual", "도장 실적일",  "date",  False, "공정 6단계 완료일"),
    ("발송_actual", "발송 실적일",  "date",  False, "출하 일자"),
    ("시공_actual", "시공 실적일",  "date",  False, "현장 설치 완료일"),
]

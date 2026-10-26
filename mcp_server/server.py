#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acupoint Anatomy & Substrate Identification — 로컬 stdio MCP 서버

도구 로직은 acupoint_core.py에 있고, 이 파일은 로컬 디스크에서 데이터를 읽는 백엔드만 정의한다.

데이터 위치 (저장소 루트 기준, 없으면 Drive 프로젝트 구조의 상위 폴더 사본으로 대체)
  framework/·data/                       : 정본 사본, 마스터 CSV·생의학 DB·Layer B·FMA 대응표·참조 JSON
  data/classics/<원전>/*.md              : 4대 원전 정제 마크다운
  보조 문헌(선택)                        : 환경변수 ACUPOINT_EXTRA_CLASSICS="東醫寶鑑=G:/…/동의보감;…"
                                           지정이 없으면 상위 폴더 01_도서_번역_및_원전/동의보감을 자동 사용
  FMA 로컬 색인(선택)                    : scripts/fma + FMA_DATA_DIR(기본 %LOCALAPPDATA%/acupoint_fma)

사용:
  python server.py
  등록: python scripts/register_mcp.py   (Claude Code 사용자 범위)
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from acupoint_core import norm_text, run_stdio  # noqa: E402

LOCAL_PATHS = {
    "framework": PROJECT_ROOT / "framework" / "acupoint_anatomical_logic_framework.md",
    "layer_b_md": PROJECT_ROOT / "framework" / "layer_b_reference_registry.md",
    "layer_b_json": PROJECT_ROOT / "data" / "layer_b_reference_registry.json",
    "master_csv": PROJECT_ROOT / "data" / "361_Acupoints_Refined_Master_DB_v2.csv",
    "biomed_json": PROJECT_ROOT / "data" / "경혈_생의학_신경반사_마스터DB.json",
    "fma_json": PROJECT_ROOT / "data" / "acupoint_fma_mapping.json",
    "reference_json": PROJECT_ROOT / "data" / "mcp_reference_data.json",
}
# Drive 프로젝트(도서 번역/acupoint_anatomy)에서 실행될 때 상위 폴더의 정본 데이터로 대체
PARENT = PROJECT_ROOT.parent
PARENT_FALLBACKS = {
    "framework": PARENT / "01_Framework" / "acupoint_anatomical_logic_framework.md",
    "layer_b_md": PARENT / "01_Framework" / "layer_b_reference_registry.md",
    "layer_b_json": PARENT / "02_Master_Datasets" / "layer_b_reference_registry.json",
    "master_csv": PARENT / "02_Master_Datasets" / "361_Acupoints_Refined_Master_DB_v2.csv",
    "biomed_json": PARENT / "02_Master_Datasets" / "경혈_생의학_신경반사_마스터DB.json",
    "fma_json": PARENT / "02_Master_Datasets" / "FMA" / "acupoint_fma_mapping.json",
}
CLASSICS_DIR = PROJECT_ROOT / "data" / "classics"
CORE_BOOKS = [  # (필터 키, 디렉토리, 표기)
    ("穴位通鉴", "中国针灸穴位通鉴", "《中国针灸穴位通鉴》"),
    ("腧穴通考", "针灸腧穴通考", "《针灸腧穴通考》"),
    ("证治通鉴", "中国针灸证治通鉴", "《中国针灸证治通鉴》"),
    ("经络通鉴", "中国针灸经络通鉴", "《中国针灸经络通鉴》"),
]
DEFAULT_EXTRA = [("東醫寶鑑", PARENT / "01_도서_번역_및_원전" / "동의보감")]


class LocalBackend:
    def __init__(self):
        self.label = f"로컬 {PROJECT_ROOT.as_posix()}"
        self._books = [(k, str(CLASSICS_DIR / d), label, "core") for k, d, label in CORE_BOOKS if (CLASSICS_DIR / d).is_dir()]
        for name, path in self._extra_config():
            if path.is_dir():
                self._books.append((norm_text(name), str(path), f"《{name}》(보조)", "extra"))
        self._fma = None

    @staticmethod
    def _extra_config():
        env = os.environ.get("ACUPOINT_EXTRA_CLASSICS", "").strip()
        if not env:
            return DEFAULT_EXTRA
        out = []
        for part in env.split(";"):
            if "=" in part:
                name, path = part.split("=", 1)
                out.append((name.strip(), Path(path.strip())))
        return out

    def read_text(self, key):
        for path in (LOCAL_PATHS.get(key), PARENT_FALLBACKS.get(key)):
            if path and path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
        return ""

    def classics_books(self):
        return self._books

    def classics_list(self, dir_id):
        d = Path(dir_id)
        return sorted(f.name for f in d.glob("*.md")) if d.is_dir() else []

    def classics_read(self, dir_id, name):
        try:
            return (Path(dir_id) / name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def classics_prefetch(self, dir_id, names):
        return None

    def fma_instance(self):
        """로컬 FMA 색인이 있으면 (FMA 객체, fma_query 모듈). 경혈 대응표는 저장소 data/ 사본을 쓰도록 맞춘다"""
        if self._fma is None:
            self._fma = (None, None)
            fma_dir = PROJECT_ROOT / "scripts" / "fma"
            try:
                if fma_dir.is_dir() and str(fma_dir) not in sys.path:
                    sys.path.insert(0, str(fma_dir))
                import fma_common
                import fma_query
                if not fma_query.MAPPING_JSON.exists() and LOCAL_PATHS["fma_json"].exists():
                    fma_query.MAPPING_JSON = LOCAL_PATHS["fma_json"]
                    fma_common.MAPPING_JSON = LOCAL_PATHS["fma_json"]
                if fma_common.INDEX_PATH.exists():
                    self._fma = (fma_query.FMA(), fma_query)
            except BaseException as e:  # 패키지 없음·sys.exit 등 — 대응표 JSON으로 대체
                sys.stderr.write(f"[server] FMA 색인 미사용: {e}\n")
        return self._fma


if __name__ == "__main__":
    run_stdio(LocalBackend())

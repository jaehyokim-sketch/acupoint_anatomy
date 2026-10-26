# -*- coding: utf-8 -*-
"""
Acupoint Anatomy & Substrate Identification — 원격 stdio MCP 서버 (GitHub 스트리밍)

로컬 저장소 없이 이 파일 하나로 GitHub 저장소의 데이터를 받아 쓴다. 도구는 로컬 server.py와 같다.

  python remote_server.py [--repo <owner>/<repo>] [--branch main] [--token <PAT>] [--cache-dir <경로>] [--ttl 3600]
  환경변수: GITHUB_REPO · GITHUB_BRANCH · GITHUB_TOKEN · ACUPOINT_CACHE_DIR

데이터 갱신 방식
  - 원전 목록·변경은 data/classics/index.json(파일별 SHA-1)으로 확인한다 → GitHub API 호출 횟수 제한(시간당 60회)과 무관
    (index.json이 없을 때만 GitHub Contents API로 목록을 받는다)
  - 원전 파일은 SHA-1을 이름으로 디스크 캐시(~/.acupoint_anatomy/cache/classics)에 저장해 재시작 후에도 다시 받지 않는다
  - index.json과 그 밖의 데이터는 --ttl(기본 3600초)마다 다시 확인하므로, 저장소가 갱신되면 재시작 없이 반영된다
  - 보조 문헌(동의보감 등)과 FMA 로컬 색인은 원격 모드에서 쓰지 않는다(FMA는 대응표 JSON으로 응답)
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# <core-import> 개발 중 같은 폴더에서 실행할 때만 쓰인다. 생성된 remote_server.py에서는 이 블록이 지워지고 코어가 앞에 붙는다
sys.path.insert(0, str(Path(__file__).resolve().parent))
from acupoint_core import run_stdio  # noqa: E402
# </core-import>

REMOTE_DATA_PATHS = {
    "framework": "framework/acupoint_anatomical_logic_framework.md",
    "layer_b_md": "framework/layer_b_reference_registry.md",
    "layer_b_json": "data/layer_b_reference_registry.json",
    "master_csv": "data/361_Acupoints_Refined_Master_DB_v2.csv",
    "biomed_json": "data/경혈_생의학_신경반사_마스터DB.json",
    "fma_json": "data/acupoint_fma_mapping.json",
    "reference_json": "data/mcp_reference_data.json",
}
REMOTE_BOOKS = [
    ("穴位通鉴", "中国针灸穴位通鉴", "《中国针灸穴位通鉴》"),
    ("腧穴通考", "针灸腧穴通考", "《针灸腧穴通考》"),
    ("证治通鉴", "中国针灸证治通鉴", "《中国针灸证治通鉴》"),
    ("经络通鉴", "中国针灸经络通鉴", "《中国针灸经络通鉴》"),
]


class RemoteBackend:
    def __init__(self, repo, branch, token="", cache_dir=None, ttl=3600):
        self.repo, self.branch, self.token, self.ttl = repo, branch, token, max(60, int(ttl))
        self.label = f"GitHub {repo}@{branch}"
        self.cache_dir = Path(cache_dir or os.environ.get("ACUPOINT_CACHE_DIR") or (Path.home() / ".acupoint_anatomy" / "cache"))
        (self.cache_dir / "classics").mkdir(parents=True, exist_ok=True)
        self._mem = {}        # 경로 → (받은 시각, 내용)
        self._index = None    # (받은 시각, {원전 디렉토리: {파일명: sha1}})

    # --- HTTP -----------------------------------------------------------
    def _get(self, url, accept=None):
        headers = {"User-Agent": "AcupointAnatomy-Remote-MCP/3.0"}
        if accept:
            headers["Accept"] = accept
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
            return resp.read()

    def _raw(self, path):
        url = f"https://raw.githubusercontent.com/{self.repo}/{urllib.parse.quote(self.branch)}/{urllib.parse.quote(path)}"
        return self._get(url).decode("utf-8", errors="replace")

    def fetch(self, path, ttl=None):
        ttl = self.ttl if ttl is None else ttl
        hit = self._mem.get(path)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        try:
            text = self._raw(path)
        except Exception as e:
            sys.stderr.write(f"[remote] {path} 받기 실패: {e}\n")
            return hit[1] if hit else ""  # 실패 시 이전 내용 유지
        self._mem[path] = (time.time(), text)
        return text

    # --- 백엔드 인터페이스 ------------------------------------------------
    def cache_token(self):
        """이 값이 바뀌면 코어가 파싱해 둔 데이터를 버리고 다시 읽는다"""
        return int(time.time() // self.ttl)

    def read_text(self, key):
        path = REMOTE_DATA_PATHS.get(key)
        return self.fetch(path) if path else ""

    def _books_index(self):
        if self._index and time.time() - self._index[0] < self.ttl:
            return self._index[1]
        books = {}
        text = self.fetch("data/classics/index.json")
        if text:
            try:
                for d, files in json.loads(text).get("books", {}).items():
                    books[d] = {f["name"]: f.get("sha1") for f in files}
            except Exception as e:
                sys.stderr.write(f"[remote] index.json 파싱 실패: {e}\n")
        if not books:  # 색인이 없으면 GitHub API로 목록만(SHA 없음)
            for _, d, _ in REMOTE_BOOKS:
                try:
                    url = f"https://api.github.com/repos/{self.repo}/contents/{urllib.parse.quote('data/classics/' + d)}?ref={urllib.parse.quote(self.branch)}"
                    items = json.loads(self._get(url, "application/vnd.github+json").decode("utf-8"))
                    books[d] = {i["name"]: None for i in items if i.get("type") == "file" and i.get("name", "").endswith(".md")}
                except Exception as e:
                    sys.stderr.write(f"[remote] {d} 목록 실패: {e}\n")
        if books:
            self._index = (time.time(), books)
        return books

    def classics_books(self):
        idx = self._books_index()
        return [(k, d, label, "core") for k, d, label in REMOTE_BOOKS if not idx or d in idx]

    def classics_list(self, dir_id):
        return sorted(self._books_index().get(dir_id, {}))

    def classics_version(self, dir_id, name):
        return self._books_index().get(dir_id, {}).get(name)

    def classics_read(self, dir_id, name):
        sha = self.classics_version(dir_id, name)
        disk = self.cache_dir / "classics" / f"{sha}.md" if sha else None
        if disk and disk.exists():
            return disk.read_text(encoding="utf-8")
        try:
            text = self._raw(f"data/classics/{dir_id}/{name}")
        except Exception as e:
            sys.stderr.write(f"[remote] {dir_id}/{name} 받기 실패: {e}\n")
            return ""
        if disk:
            got = hashlib.sha1(text.encode("utf-8").replace(b"\r\n", b"\n")).hexdigest()
            if got == sha:  # 색인과 내용이 맞을 때만 디스크에 남긴다
                disk.write_text(text, encoding="utf-8", newline="\n")
        return text

    def classics_prefetch(self, dir_id, names):
        todo = [n for n in names if not (self.classics_version(dir_id, n) and
                                         (self.cache_dir / "classics" / f"{self.classics_version(dir_id, n)}.md").exists())]
        if len(todo) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(lambda n: self.classics_read(dir_id, n), todo))

    def fma_instance(self):
        return None, None


def main():
    ap = argparse.ArgumentParser(description="Acupoint Anatomy Remote MCP Server (GitHub streaming)")
    ap.add_argument("--repo", default=os.getenv("GITHUB_REPO", "jaehyokim-sketch/acupoint_anatomy"))
    ap.add_argument("--branch", default=os.getenv("GITHUB_BRANCH", "main"))
    ap.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""), help="GitHub PAT (공개 저장소는 불필요)")
    ap.add_argument("--cache-dir", default=None, help="디스크 캐시 위치 (기본 ~/.acupoint_anatomy/cache)")
    ap.add_argument("--ttl", type=int, default=3600, help="데이터 재확인 주기(초, 기본 3600)")
    args, _ = ap.parse_known_args()
    run_stdio(RemoteBackend(args.repo, args.branch, args.token, args.cache_dir, args.ttl))


if __name__ == "__main__":
    main()

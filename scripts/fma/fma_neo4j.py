# -*- coding: utf-8 -*-
"""
fma_neo4j.py — FMA 그래프를 Neo4j에 적재하고 Cypher로 순회 분석 (Claude Code 전용)

연결 설정 (사용자 환경변수, PC마다):
  NEO4J_URI=bolt://localhost:7687   NEO4J_USER=neo4j   NEO4J_PASSWORD=<비밀번호>   (NEO4J_DATABASE=neo4j)

사용 (프로젝트 루트에서, fma_build.py all 이후):
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py server start|stop|status   # 로컬 설치 서버 (관리자 권한 불필요)
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py ping
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py load [--driver neo4j|py2neo] [--wipe]
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py templates
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py query acupoint_structures --param code=ST36
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py query shared_nerve_territory --param nerve="Deep fibular nerve"
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_neo4j.py cypher "MATCH (a:Acupoint) RETURN count(a)"

로컬 서버 위치: NEO4J_HOME → %LOCALAPPDATA%/neo4j/neo4j-community-* (JAVA_HOME → %LOCALAPPDATA%/neo4j/jdk-21*)
  서버는 콘솔 모드로 분리 실행되며 로그는 <NEO4J_HOME>/logs/console.log, PID는 <NEO4J_HOME>/run/console.pid.
  Windows 서비스 등록(자동 시작)은 관리자 권한이 필요하므로 쓰지 않는다. 분석 전에 server start를 실행한다.

드라이버: 공식 `neo4j` 드라이버가 기본이다. `py2neo`는 2023년 개발 종료(아카이브)되어 Neo4j 5.x 이상과 호환이
보장되지 않으므로 --driver py2neo는 기존 환경 호환용으로만 쓴다.
"""
import argparse
import csv
import io
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

from fma_common import NEO4J_DIR

BATCH = 5000

TEMPLATES = {
    "acupoint_structures": (
        "경혈의 교재 해부 구조와 FMA 상위 줄기",
        """MATCH (a:Acupoint {code:$code})-[h:HAS_STRUCTURE]->(s:Anatomy)
           WITH s, h.category AS 구분, collect(h.source) AS 교재, collect(DISTINCT h.match) AS 대응
           OPTIONAL MATCH p=(s)-[:BRANCH_OF|BRANCH_OF_INFERRED|TRIBUTARY_OF*1..8]->(t:Anatomy)
           WITH s, 구분, 교재, 대응, p ORDER BY length(p) DESC
           WITH s, 구분, 교재, 대응, collect(p)[0] AS longest
           RETURN 구분, s.fmaId AS fma, s.label AS 구조, 교재, 대응,
                  [n IN nodes(longest)[1..] | n.label] AS 상위줄기
           ORDER BY 구분, 구조"""),
    "acupoint_innervation": (
        "경혈 근육의 지배신경과 척수 분절",
        """MATCH (a:Acupoint {code:$code})-[:HAS_STRUCTURE]->(m:Anatomy)
           OPTIONAL MATCH (m)-[:NERVE_SUPPLY]->(n:Anatomy)
           OPTIONAL MATCH (m)-[r:SEGMENTAL_SUPPLY|PRIMARY_SEGMENTAL_SUPPLY|SECONDARY_SEGMENTAL_SUPPLY]->(seg:Anatomy)
           WITH m, collect(DISTINCT n.label) AS 신경, collect(DISTINCT type(r) + ':' + seg.label) AS 분절
           WHERE size(신경) > 0 OR size(분절) > 0
           RETURN m.fmaId AS fma, m.label AS 구조, 신경, 분절"""),
    "shared_nerve_territory": (
        "한 신경(과 그 모든 가지)이 분포하는 구조를 공유하는 경혈들",
        """MATCH (root:Anatomy) WHERE toLower(root.label) = toLower($nerve)
           MATCH (b:Anatomy)-[:BRANCH_OF|BRANCH_OF_INFERRED*0..8]->(root)
           OPTIONAL MATCH (m:Anatomy)-[:NERVE_SUPPLY]->(b)
           WITH collect(DISTINCT b) + collect(DISTINCT m) AS territory
           UNWIND territory AS s
           MATCH (a:Acupoint)-[:HAS_STRUCTURE]->(s)
           RETURN a.code AS 경혈, a.nameKr AS 혈명, collect(DISTINCT s.label) AS 공유구조
           ORDER BY 경혈"""),
    "shared_structure": (
        "두 경혈이 공유하는 FMA 실체 (직접 + 같은 상위 줄기)",
        """MATCH (a:Acupoint {code:$a})-[:HAS_STRUCTURE]->(s:Anatomy)<-[:HAS_STRUCTURE]-(b:Acupoint {code:$b})
           RETURN '직접' AS 유형, s.label AS 구조
           UNION
           MATCH (a:Acupoint {code:$a})-[:HAS_STRUCTURE]->(sa:Anatomy)-[:BRANCH_OF|BRANCH_OF_INFERRED*1..4]->(t:Anatomy)
                 <-[:BRANCH_OF|BRANCH_OF_INFERRED*1..4]-(sb:Anatomy)<-[:HAS_STRUCTURE]-(b:Acupoint {code:$b})
           WHERE sa <> sb
           RETURN '공통 줄기' AS 유형, t.label AS 구조"""),
    "acupoints_by_segment": (
        "특정 척수 분절(예: L5)에서 지배받는 근육을 가진 경혈 (4개 분절 이하에 걸친 근육만 — 다분절 척추근 제외)",
        """MATCH (seg:Anatomy {label:$segment})<-[:SEGMENTAL_SUPPLY|PRIMARY_SEGMENTAL_SUPPLY]-(m:Anatomy)
                 <-[:HAS_STRUCTURE]-(a:Acupoint)
           MATCH (m)-[:SEGMENTAL_SUPPLY]->(any:Anatomy)
           WITH a, m, count(DISTINCT any) AS span WHERE span <= 4
           RETURN a.code AS 경혈, a.nameKr AS 혈명, collect(DISTINCT m.label + ' (' + span + '분절)') AS 근육 ORDER BY 경혈"""),
    "anatomy_path": (
        "말초 구조 → 줄기 방향 경로 (가지·지류·부분 관계, 방향 고정). 없으면 무방향 최단 경로",
        """MATCH (x:Anatomy), (y:Anatomy) WHERE toLower(x.label)=toLower($from) AND toLower(y.label)=toLower($to)
           OPTIONAL MATCH up = shortestPath((x)-[:BRANCH_OF|BRANCH_OF_INFERRED|TRIBUTARY_OF|REGIONAL_PART_OF|CONSTITUTIONAL_PART_OF*..12]->(y))
           OPTIONAL MATCH any = shortestPath((x)-[:BRANCH_OF|BRANCH_OF_INFERRED|REGIONAL_PART_OF|CONSTITUTIONAL_PART_OF|CONTINUOUS_WITH|TRIBUTARY_OF*..12]-(y))
           WITH coalesce(up, any) AS p, up IS NOT NULL AS directed
           RETURN directed AS 방향경로, [n IN nodes(p) | n.label] AS 경로, [r IN relationships(p) | type(r)] AS 관계"""),
}


def conn_params():
    pw = os.environ.get("NEO4J_PASSWORD")
    if not pw and sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as reg:
                pw, _ = winreg.QueryValueEx(reg, "NEO4J_PASSWORD")
        except Exception:
            pass
    return (os.environ.get("NEO4J_URI", "bolt://localhost:7687"), os.environ.get("NEO4J_USER", "neo4j"),
            pw, os.environ.get("NEO4J_DATABASE", "neo4j"))


class Runner:
    """neo4j 공식 드라이버와 py2neo를 같은 인터페이스로 감싼다."""

    def __init__(self, driver="neo4j"):
        uri, user, pw, self.db = conn_params()
        if not pw:
            sys.exit("[neo4j] NEO4J_PASSWORD 환경변수가 없습니다. 예) setx NEO4J_PASSWORD <비밀번호> 후 새 터미널")
        self.kind = driver
        if driver == "py2neo":
            from py2neo import Graph
            self.g = Graph(uri, auth=(user, pw), name=self.db)
        else:
            from neo4j import GraphDatabase
            self.g = GraphDatabase.driver(uri, auth=(user, pw))
            self.g.verify_connectivity()

    def run(self, cypher, **params):
        if self.kind == "py2neo":
            return [dict(r) for r in self.g.run(cypher, **params).data()]
        recs, _, _ = self.g.execute_query(cypher, params, database_=self.db)
        return [r.data() for r in recs]

    def close(self):
        if self.kind != "py2neo":
            self.g.close()


def _local_dir(env, pattern):
    if os.environ.get(env):
        return Path(os.environ[env])
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "neo4j"
    hits = sorted(base.glob(pattern)) if base.exists() else []
    return hits[-1] if hits else None


def _port_open(port=7687):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def cmd_server(a):
    home, jdk = _local_dir("NEO4J_HOME", "neo4j-community-*"), _local_dir("JAVA_HOME", "jdk-21*")
    if not home or not (home / "bin").exists():
        sys.exit("[server] Neo4j 설치를 찾지 못했습니다. NEO4J_HOME을 설정하거나 %LOCALAPPDATA%/neo4j에 압축을 푸세요.")
    pidf = home / "run" / "console.pid"
    if a.action == "status":
        print(f"[server] NEO4J_HOME={home}")
        print(f"         JAVA_HOME={jdk}")
        print(f"         bolt 7687: {'열림(실행 중)' if _port_open() else '닫힘'}")
        return
    if a.action == "start":
        if _port_open():
            print("[server] 이미 실행 중 (bolt 7687)")
            return
        (home / "logs").mkdir(exist_ok=True)
        (home / "run").mkdir(exist_ok=True)
        bat = str(home / "bin" / "neo4j.bat")
        if sys.platform == "win32":
            jdk_str = str(jdk) if jdk else ""
            ps_cmd = f'$env:JAVA_HOME = "{jdk_str}"; Start-Process -FilePath "{bat}" -ArgumentList "console" -WindowStyle Hidden'
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd])
        else:
            env = dict(os.environ)
            if jdk:
                env["JAVA_HOME"] = str(jdk)
            log = open(home / "logs" / "console.log", "ab")
            flags = 0x00000008 | 0x00000200
            p = subprocess.Popen(["cmd", "/c", bat, "console"], cwd=str(home), env=env,
                                 stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags)
            pidf.write_text(str(p.pid))

        for _ in range(90):
            if _port_open():
                print(f"[server] 시작됨 (bolt://localhost:7687, http://localhost:7474)")
                return
            time.sleep(1)
        sys.exit(f"[server] 90초 안에 bolt 포트가 열리지 않았습니다. 로그 확인: {home / 'logs' / 'console.log'}")
    if a.action == "stop":
        pid = "—"
        if pidf.exists():
            pid = pidf.read_text().strip()
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
            pidf.unlink()
            time.sleep(2)
        if not _port_open() and pid == "—":
            print("[server] 실행 중인 서버가 없습니다 (bolt 7687 닫힘)")
            return
        if _port_open():
            # 콘솔 래퍼만 끝나고 java 본체가 남는 경우: 7687을 듣는 java 중 이 NEO4J_HOME의 것만 종료
            ps = ("$c=Get-NetTCPConnection -LocalPort 7687 -State Listen -ErrorAction SilentlyContinue|Select-Object -First 1;"
                  "if($c){$p=Get-CimInstance Win32_Process -Filter \"ProcessId=$($c.OwningProcess)\";"
                  f"if($p.CommandLine -like '*{home.name}*'){{Stop-Process -Id $p.ProcessId -Force;'killed '+$p.ProcessId}}}}")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
            print(f"[server] java 본체 정리: {r.stdout.strip() or '해당 없음'}")
            time.sleep(2)
        print(f"[server] 종료 (pid {pid})" + (" — 포트가 아직 열려 있음" if _port_open() else " — bolt 7687 닫힘"))


def _csv_rows(name):
    path = NEO4J_DIR / name
    if not path.exists():
        sys.exit(f"[neo4j] {path}가 없습니다. 먼저: python .claude/skills/acupoint-anatomy/scripts/fma/fma_build.py neo4j-csv")
    with io.open(path, encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        next(r)
        yield from r


def _batches(it, n=BATCH):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def cmd_load(a):
    r = Runner(a.driver)
    if a.wipe:
        print("[neo4j] 기존 :Anatomy/:Acupoint 노드 삭제")
        r.run("MATCH (n) WHERE n:Anatomy OR n:Acupoint CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS")
    r.run("CREATE CONSTRAINT anatomy_fma IF NOT EXISTS FOR (n:Anatomy) REQUIRE n.fmaId IS UNIQUE")
    r.run("CREATE CONSTRAINT acupoint_code IF NOT EXISTS FOR (n:Acupoint) REQUIRE n.code IS UNIQUE")
    r.run("CREATE INDEX anatomy_label IF NOT EXISTS FOR (n:Anatomy) ON (n.label)")
    n = 0
    for b in _batches(_csv_rows("fma_nodes.csv")):
        r.run("UNWIND $rows AS row MERGE (n:Anatomy {fmaId: toInteger(row[0])}) SET n.label = row[1], n.taId = row[2]", rows=b)
        n += len(b)
    print(f"[neo4j] Anatomy 노드 {n:,}")
    by_type = {}
    for s, d, t in _csv_rows("fma_rels.csv"):
        # Neo4j 관계 유형에 쓸 수 없는 문자(예: INHERENT_3-D_SHAPE의 '-')는 '_'로 바꾼다
        by_type.setdefault(re.sub(r"[^A-Z0-9_]", "_", t), []).append((s, d))
    total = 0
    for t, pairs in sorted(by_type.items()):
        for b in _batches(pairs):
            r.run(f"UNWIND $rows AS row MATCH (s:Anatomy {{fmaId: toInteger(row[0])}}), (d:Anatomy {{fmaId: toInteger(row[1])}}) "
                  f"MERGE (s)-[:{t}]->(d)", rows=b)
        total += len(pairs)
    print(f"[neo4j] FMA 관계 {total:,} ({len(by_type)}종)")
    if (NEO4J_DIR / "acupoint_nodes.csv").exists():
        pts = list(_csv_rows("acupoint_nodes.csv"))
        r.run("UNWIND $rows AS row MERGE (a:Acupoint {code: row[0]}) SET a.nameKr = row[1]", rows=pts)
        rels = list(_csv_rows("acupoint_rels.csv"))
        for b in _batches(rels):
            r.run("UNWIND $rows AS row MATCH (a:Acupoint {code: row[0]}), (s:Anatomy {fmaId: toInteger(row[1])}) "
                  "MERGE (a)-[h:HAS_STRUCTURE {source: row[2]}]->(s) SET h.category = row[3], h.match = row[4]", rows=b)
        print(f"[neo4j] Acupoint 노드 {len(pts)} / HAS_STRUCTURE {len(rels):,}")
    r.close()


def _params(items):
    out = {}
    for kv in items or []:
        k, _, v = kv.partition("=")
        if k == "code" or k in ("a", "b"):
            m = re.fullmatch(r"([A-Za-z]+)-?(\d+)", v.strip())
            v = f"{m.group(1).upper()}{int(m.group(2)):02d}" if m else v
        out[k] = v
    return out


def _print(rows):
    if not rows:
        print("(결과 없음)")
    for row in rows:
        print(" | ".join(f"{k}={v}" for k, v in row.items()))


def main():
    ap = argparse.ArgumentParser(description="FMA ↔ Neo4j 적재·Cypher 분석")
    ap.add_argument("--driver", choices=["neo4j", "py2neo"], default="neo4j")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("server"); s.add_argument("action", choices=["start", "stop", "status"])
    sub.add_parser("ping")
    s = sub.add_parser("load"); s.add_argument("--wipe", action="store_true", help="기존 Anatomy/Acupoint 노드 삭제 후 적재")
    sub.add_parser("templates")
    s = sub.add_parser("query"); s.add_argument("name", choices=sorted(TEMPLATES)); s.add_argument("--param", action="append")
    s = sub.add_parser("cypher"); s.add_argument("text"); s.add_argument("--param", action="append")
    a = ap.parse_args()
    if a.cmd == "templates":
        for k, (desc, q) in TEMPLATES.items():
            print(f"## {k} — {desc}\n{re.sub(r'(?m)^ {11}', '', q)}\n")
        return
    if a.cmd == "server":
        return cmd_server(a)
    if a.cmd == "load":
        return cmd_load(a)
    r = Runner(a.driver)
    if a.cmd == "ping":
        _print(r.run("CALL dbms.components() YIELD name, versions RETURN name, versions"))
        _print(r.run("MATCH (n:Anatomy) RETURN count(n) AS Anatomy"))
    elif a.cmd == "query":
        _print(r.run(TEMPLATES[a.name][1], **_params(a.param)))
    else:
        _print(r.run(a.text, **_params(a.param)))
    r.close()


if __name__ == "__main__":
    main()

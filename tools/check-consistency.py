# -*- coding: utf-8 -*-
"""책 전체의 불변식을 검사한다.

왜 있나
  2026-07-30 뜻 검수에서 장 사이 자기모순 3건이 나왔다.
    · 14장 「자동화는 _reports/ 에만 쓴다」 vs 15장 대시보드는 _moc/ 에 쓴다
    · 14장 프롬프트는 deadline 필드, 15장 표는 due (15장이 due/deadline 혼용을 나쁜 예로 든다)
    · 15장 status 다섯 개 vs 3장 설계서의 제품 status 네 개
  셋 다 사람이 읽어서 우연히 찾았다. ch14 와 ch15 가 같은 검수자에게 배정된 덕이고,
  다른 에이전트로 갈렸으면 못 잡았다. 그 우연을 없애기 위한 스크립트다.

쓰는 법
  python tools/check-consistency.py                 전체
  python tools/check-consistency.py --book <folder> 한 권만
  python tools/check-consistency.py --json          기계 판독용

종료 코드
  0 = 통과, 1 = ERROR 있음
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = json.loads((ROOT / "tools" / "invariants.json").read_text(encoding="utf-8"))
EM = "—"

findings: list[tuple[str, str, str]] = []  # (level, where, message)


def add(level: str, where: str, msg: str) -> None:
    findings.append((level, where, msg))


def rel(p: Path) -> str:
    """저장소 상대경로. 네 책이 모두 ch01.html 을 가지므로 파일명만으로는 구분이 안 된다."""
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.name


def prose_of(html: str) -> str:
    """산문만. svg·pre·code·nav 를 뺀다."""
    try:
        body = html[html.index("<article>"):html.index("</article>")]
    except ValueError:
        body = html
    body = re.sub(r"<svg.*?</svg>|<pre>.*?</pre>", "", body, flags=re.S)
    return body


def visible(html: str) -> str:
    """태그를 벗긴 눈에 보이는 텍스트."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


# ---------------------------------------------------------------- 검사 항목

def check_prose_metrics(f: Path, html: str) -> None:
    """STYLE.md 지표. em dash 와 여러분은 0 이어야 한다."""
    if ".en." in f.name:
        return
    p = prose_of(html)
    chars = len(re.sub(r"<[^>]+>|\s", "", p)) or 1
    z = INV["prose_rules"]["zero_tolerance"]
    for tok, limit in (("em_dash", z["em_dash"]), ("여러분", z["여러분"])):
        needle = EM if tok == "em_dash" else tok
        n = p.count(needle)
        if n > limit:
            add("ERROR", rel(f), f"{tok} {n}개 (허용 {limit})")
    # 비율 예산은 분량이 충분한 문서에만 적용한다.
    # 짧은 페이지에서 1만자당 환산은 노이즈다 (coming-soon 은 1건이 17회로 잡혔다).
    if chars < INV["prose_rules"]["budget_min_chars"]:
        return
    for tok, per10k in INV["prose_rules"]["budget_per_10k_chars"].items():
        n = p.count(tok)
        rate = n / chars * 10000
        if rate > per10k:
            add("WARN", rel(f), f"{tok} {n}회 · 1만자당 {rate:.1f} (예산 {per10k})")


def check_forbidden_aliases(f: Path, html: str) -> None:
    """정본이 아닌 필드명이 정본처럼 쓰이면 안 된다.
    나쁜 예로 인용하는 맥락에는 허용 표지가 함께 있어야 한다."""
    cfg = INV["forbidden_field_aliases"]
    text = visible(html) + " " + " ".join(re.findall(r"<pre>.*?</pre>", html, flags=re.S))
    for alias in cfg["aliases"]:
        for m in re.finditer(re.escape(alias) + r"\s*(?:필드|field)", text):
            window = text[max(0, m.start() - 220): m.end() + 220]
            if not any(k in window for k in cfg["allowed_context_markers"]):
                add("ERROR", rel(f),
                    f"비정본 필드명 「{alias}」을 정본처럼 씀 (나쁜 예 표지 없음): …{window[180:300].strip()}…")


def check_automation_write_policy(f: Path, html: str) -> None:
    """「_reports/ 에만」 같은 배타적 주장은 허용 목록이 둘 이상이면 거짓이 된다."""
    pol = INV["automation_write_policy"]
    if len(pol["allowed"]) <= 1:
        return
    for pat in pol["exclusive_claim_patterns"]:
        if pat in html:
            add("ERROR", rel(f),
                f"배타적 주장 「{pat}」 이 남아 있음. 허용 폴더가 {pol['allowed']} 로 둘 이상임")


def check_status_enum(f: Path, html: str) -> None:
    """status 어휘가 두 벌이므로, 다섯 개를 주장하는 문장은 어느 클래스인지 밝혀야 한다."""
    e = INV["status_enums"]
    text = visible(html)
    for m in re.finditer(r"status[^.]{0,60}?(다섯 개|one of five)", text):
        window = text[max(0, m.start() - 160): m.end() + 60]
        if not re.search(r"과제|기회|project|opportunit", window, re.I):
            add("ERROR", rel(f),
                "status 「다섯 개」 주장에 클래스 한정이 없음 (제품은 네 개다): …"
                + window[-140:].strip() + "…")
    # 두 어휘 집합이 뒤섞여 한 목록에 들어갔는지
    for m in re.finditer(r"\{([^}]{4,80})\}", text):
        vals = {v.strip() for v in re.split(r"[,·/|]", m.group(1)) if v.strip()}
        a, b = set(e["제품"]), set(e["과제_기회"])
        if vals & (a - b) and vals & (b - a):
            add("ERROR", rel(f), f"status 어휘 두 벌이 한 목록에 섞임: {sorted(vals)}")


def check_structure(book: Path) -> None:
    """장·부 개수가 index 와 실제 파일에서 일치하는지.

    불변식은 책별이다. 전역 하나로 뒀다가 다른 책에서 오탐 35건이 났다."""
    s = INV["structure"].get(book.name)
    if not s:
        add("INFO", book.name, "structure 불변식 미등록 (tools/invariants.json 에 추가하면 검사됨)")
        return
    idx = book / "index.html"
    if not idx.exists():
        return
    html = idx.read_text(encoding="utf-8")
    total = s.get("chapters_total")
    if total:
        m = re.search(r"(\d+)개의 챕터", html)
        if m and int(m.group(1)) != total:
            add("ERROR", rel(idx), f"목차 문구가 챕터 {m.group(1)}개 (불변식 {total})")
        cards = len(re.findall(r'class="chapter-card"', html))
        if cards and cards != total:
            add("ERROR", rel(idx), f"챕터 카드 {cards}개 (불변식 {total})")
    for ch in s.get("published_chapters", []):
        for lang in s.get("languages", ["ko"]):
            suffix = ".html" if lang == "ko" else f".{lang}.html"
            p = book / "chapters" / (ch + suffix)
            if not p.exists():
                add("ERROR", book.name, f"{lang} 장 누락: chapters/{ch}{suffix}")


def check_language_pairs(book: Path) -> None:
    """짝이 있는 파일은 hreflang 이 양방향이어야 한다. 짝이 없으면 hreflang 이 없어야 한다."""
    pages = sorted(book.glob("*.html")) + sorted((book / "chapters").glob("*.html"))
    for p in pages:
        html = p.read_text(encoding="utf-8")
        alts = re.findall(r'hreflang="(\w+)" href="([^"]+)"', html)
        counterpart = p.with_name(
            p.name.replace(".en.html", ".html") if ".en." in p.name
            else p.name[:-5] + ".en.html")
        if counterpart.exists():
            if not alts:
                add("ERROR", rel(p), f"짝({counterpart.name})이 있는데 hreflang 없음 → 스위처 안 뜸")
            for _, href in alts:
                back = p.parent / href
                if not back.exists():
                    add("ERROR", rel(p), f"hreflang 대상 없음: {href}")
                elif not re.search(rf'hreflang="\w+" href="{re.escape(p.name)}"',
                                   back.read_text(encoding="utf-8")):
                    add("ERROR", rel(p), f"역방향 hreflang 없음: {href}")
        elif alts:
            add("ERROR", rel(p), f"짝이 없는데 hreflang 있음 → 404 위험: {alts}")


def check_en_korean_leftovers(f: Path, html: str) -> None:
    """영어판에 남은 한글은 필드 값뿐이어야 한다."""
    if ".en." not in f.name:
        return
    keep = set(INV["en_keep_korean"]["tokens"])
    body = re.sub(r"<svg.*?</svg>", "", html, flags=re.S)
    body = re.sub(r'<ul class="nav-list">.*?</ul>', "", body, flags=re.S)
    bad = sorted({t for t in re.findall(r"[가-힣]+", body) if t not in keep})
    if bad:
        add("ERROR", rel(f), f"영어판에 예상 밖 한글: {bad[:8]}")


def check_en_paths(f: Path, html: str) -> None:
    """영어판 경로는 정본 영문 이름을 써야 한다."""
    if ".en." not in f.name:
        return
    for ko, en in INV["en_path_map"].items():
        if ko.startswith("_comment"):
            continue
        if ko in html:
            add("ERROR", rel(f), f"영어판에 한글 경로/이름 「{ko}」 (정본: {en})")


def check_broken_negation(f: Path, html: str) -> None:
    """부정 + 가능성이 충돌하는 형태. 2026-07-30 에 실제로 새어나간 유형."""
    if ".en." in f.name:
        return
    text = visible(html)
    for m in re.finditer(r"(아무것도|아무도|하나도)[^.!?]{0,25}안 [^.!?]{0,15}수 있", text):
        add("ERROR", rel(f), f"부정·가능성 충돌: 「{m.group(0).strip()}」")


def check_constants(f: Path, html: str) -> None:
    """여러 장에 흩어진 상수가 어긋나는지."""
    c = INV["constants"]
    text = visible(html)
    for m in re.finditer(r"(\d+)\s*자/분", text):
        if int(m.group(1)) != c["reading_speed_chars_per_min"]:
            add("WARN", rel(f), f"읽기 속도 {m.group(1)}자/분 (불변식 {c['reading_speed_chars_per_min']})")
    for m in re.finditer(r"(\d+)일 이상[^.]{0,12}방치", text):
        if int(m.group(1)) != c["stale_note_days"]:
            add("WARN", rel(f), f"방치 기준 {m.group(1)}일 (불변식 {c['stale_note_days']})")


# ---------------------------------------------------------------- 실행

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default=None, help="한 권만 검사")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    books = [ROOT / args.book] if args.book else [
        d for d in sorted(ROOT.iterdir())
        if d.is_dir() and (d / "index.html").exists() and d.name not in ("assets", "tools")
    ]

    files = 0
    for book in books:
        if not book.exists():
            add("ERROR", book.name, "폴더 없음")
            continue
        check_structure(book)
        check_language_pairs(book)
        for f in sorted(book.rglob("*.html")):
            html = f.read_text(encoding="utf-8")
            files += 1
            for fn in (check_prose_metrics, check_forbidden_aliases, check_automation_write_policy,
                       check_status_enum, check_en_korean_leftovers, check_en_paths,
                       check_broken_negation, check_constants):
                fn(f, html)

    counts = Counter(lv for lv, _, _ in findings)
    if args.json:
        print(json.dumps({
            "files": files,
            "counts": dict(counts),
            "findings": [{"level": l, "where": w, "message": m} for l, w, m in findings],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"검사 파일 {files}개 · 책 {len(books)}권\n")
        for level in ("ERROR", "WARN", "INFO"):
            group = [(w, m) for l, w, m in findings if l == level]
            if not group:
                continue
            print(f"── {level} {len(group)}건")
            for w, m in group:
                print(f"   {w:46} {m}")
            print()
        if not findings:
            print("불변식 위반 없음")
    return 1 if counts.get("ERROR") else 0


if __name__ == "__main__":
    sys.exit(main())

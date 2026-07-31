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
from html import unescape
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

# 예산 낱말 중 부분 문자열로 세면 다른 구문까지 잡히는 것들. 표는 불변식에 있다.
# 「그것입니다」·「이것입니다」는 지시대명사 + 서술격조사라서, 규약이 겨냥한
# 약한 명사화(「~하는 것입니다」)와 아예 다른 구문이다. 실제로 두 권에서
# 「이유가 그것입니다」와 인용문 안 「역할은 이것입니다」가 위반으로 잡혔다.
# 앞이 그/이/저가 아닐 때만 센다. 「이런 것입니다」는 사이에 공백이 있어 그대로 잡힌다.
BUDGET_PAT = INV["prose_rules"].get("budget_patterns", {})


def check_prose_metrics(f: Path, html: str, budgets: bool = True) -> None:
    """STYLE.md 지표. em dash 와 여러분은 0 이어야 한다.

    budgets=False 는 목록 쪽(서가)에 쓴다. 책 소개 문구를 늘어놓은 쪽이라
    분량은 기준을 넘지만 흐르는 산문이 아니다. 밀도 예산을 그대로 대면
    「수 있습니다」 두 번에 1만자당 13 이 나온다. 무관용 규칙만 본다.
    """
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
    if not budgets or chars < INV["prose_rules"]["budget_min_chars"]:
        return
    for tok, per10k in INV["prose_rules"]["budget_per_10k_chars"].items():
        n = len(re.findall(BUDGET_PAT.get(tok, re.escape(tok)), p))
        rate = n / chars * 10000
        if rate > per10k:
            add("WARN", rel(f), f"{tok} {n}회 · 1만자당 {rate:.1f} (예산 {per10k})")


def check_svg_labels(f: Path, html: str) -> None:
    """그림 안의 글자도 독자가 읽는다.

    산문 지표는 SVG 를 통째로 빼고 세기 때문에 그림 레이블이 사각지대였다.
    실제로 여덟 파일의 레이블에 em dash 27개가 숨어 있었다.

    영어판은 보지 않는다. STYLE.md 제2부 §1 이 「em dash 는 영어에서는 자연스럽다」이고,
    이 규칙은 조판 규칙이 아니라 **한국어 번역투를 걷어내는 규칙**이기 때문이다.
    처음에 영어판까지 검사하게 만들었다가 규약과 어긋나서 되돌렸다.
    """
    if ".en." in f.name:
        return
    labels = " ".join(
        t for svg in re.findall(r"<svg.*?</svg>", html, flags=re.S)
        for t in re.findall(r"<(?:text|tspan)[^>]*>([^<>]*)</(?:text|tspan)>", svg)
    )
    n = labels.count(EM)
    if n:
        add("ERROR", rel(f), f"그림 레이블에 em dash {n}개")


def check_forbidden_aliases(f: Path, html: str) -> None:
    """정본이 아닌 필드명이 정본처럼 쓰이면 안 된다.
    나쁜 예로 인용하는 맥락에는 허용 표지가 함께 있어야 한다."""
    cfg = INV["forbidden_field_aliases"]
    blocks = re.findall(r"<pre>.*?</pre>", html, flags=re.S)
    text = visible(html) + " " + " ".join(blocks)
    for alias in cfg["aliases"]:
        for m in re.finditer(re.escape(alias) + r"\s*(?:필드|field)", text):
            window = text[max(0, m.start() - 220): m.end() + 220]
            if not any(k in window for k in cfg["allowed_context_markers"]):
                add("ERROR", rel(f),
                    f"비정본 필드명 「{alias}」을 정본처럼 씀 (나쁜 예 표지 없음): …{window[180:300].strip()}…")

    # 「필드」라는 말이 옆에 붙어 있을 때만 잡으면 표 셀과 프론트매터를 통째로 놓친다.
    # ch03 의 「| 기회 | OPP- | ... | stage, deadline |」 이 그렇게 빠져나갔다.
    # 그래서 코드 블록 안도 본다. 다만 판정은 판본에 따라 다르다.
    #
    # 한국어판: 코드 블록 안의 홀로 선 영단어는 필드명으로 봐도 된다.
    #   한국어 산문은 deadline 을 보통명사로 쓰지 않는다.
    # 영어판: 같은 규칙을 쓰면 전부 오탐이다. 실제로 3건 전부 오탐이었다
    #   (간트 막대 이름 "Submission deadline", 회의록 원문 "deadline 8/8",
    #    산문 "anything with an owner and a deadline").
    #   그래서 영어판은 YAML 키(`deadline:`)처럼 뜻이 하나뿐인 자리만 잡는다.
    is_en = f.name.endswith(".en.html")
    for blk in blocks:
        body = unescape(re.sub(r"<[^>]+>", "", blk))
        for alias in cfg["aliases"]:
            pat = (r"^\s*-?\s*" + re.escape(alias) + r"\s*:" if is_en
                   else r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])")
            for m in re.finditer(pat, body, flags=re.M if is_en else 0):
                window = body[max(0, m.start() - 220): m.end() + 220]
                if any(k in window for k in cfg["allowed_context_markers"]):
                    continue
                nl = body.find("\n", m.end())
                line = body[body.rfind("\n", 0, m.start()) + 1: nl if nl >= 0 else len(body)]
                add("ERROR", rel(f),
                    f"예제 코드에서 비정본 필드명 「{alias}」 사용: {line.strip()[:110]}")


def check_automation_write_policy(f: Path, html: str) -> None:
    """「_reports/ 에만」 같은 배타적 주장은 허용 목록이 둘 이상이면 거짓이 된다."""
    pol = INV["automation_write_policy"]
    if len(pol["allowed"]) <= 1:
        return
    # 문자 그대로 비교하다가 ch14 의 「<code>_reports/</code>에만 쓴다」를 놓쳤다.
    # 등록해 둔 문구는 「_reports/</code> 폴더에만」 이었고 띄어쓰기와 「폴더」 유무만 달랐다.
    for pat in pol["exclusive_claim_regex"]:
        m = re.search(pat, html)
        if m:
            add("ERROR", rel(f),
                f"배타적 주장 「{m.group(0)}」 이 남아 있음. 허용 폴더가 {pol['allowed']} 로 둘 이상임")


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
        # 히어로 통계는 손으로 적혀 있어 카드 수와 어긋나기 쉽다.
        # gstack-introduction 이 실제로 15 / 14 로 갈려 있었고 세 곳 중 한 곳만 틀렸다.
        for num, label in re.findall(
                r'<span class="stat-number">([^<]+)</span>\s*'
                r'<span class="stat-label">([^<]+)</span>', html, re.S):
            n = num.strip()
            if "챕터" in label and n.isdigit() and int(n) != total:
                add("ERROR", rel(idx), f"히어로 통계가 챕터 {n}개 (불변식 {total})")
        # 사이드바 장 링크 수도 대조한다
        nav = re.search(r'<ul class="nav-list">(.*?)</ul>', html, re.S)
        if nav:
            # 목차에 번호 없는 장이 섞인 책이 있다. 사회연대경제는 「여는 이야기」가
            # 그렇다. 그런 책은 번호가 붙는 장 수를 따로 적어 둔다.
            want = s.get("nav_numbered_chapters", total)
            links = len(re.findall(r'class="nav-link">\s*(?:\d+장|\d+\.)', nav.group(1)))
            if links and links != want:
                add("ERROR", rel(idx), f"사이드바 장 링크 {links}개 (불변식 {want})")
    # 한국어판은 있어야 한다. 없으면 목차가 가리키는 페이지가 없다는 뜻이다.
    for ch in s.get("published_chapters", []):
        p = book / "chapters" / f"{ch}.html"
        if not p.exists():
            add("ERROR", book.name, f"ko 장 누락: chapters/{ch}.html")

    # 번역은 계획된 작업이지 결함이 아니다. ERROR 는 오늘 0으로 만들 수 있는 것만 담는다.
    # (17장이 세운 기준이다. 못 지울 ERROR 가 쌓이면 목록 전체를 안 보게 된다)
    # 그래서 번역 현황은 세어서 알리기만 하고, 빠진 짝은 목차가 알아서 준비 중으로 보낸다.
    for lang in s.get("languages", ["ko"]):
        if lang == "ko":
            continue
        done = [ch for ch in s.get("published_chapters", [])
                if (book / "chapters" / f"{ch}.{lang}.html").exists()]
        todo = [ch for ch in s.get("published_chapters", []) if ch not in done]
        if todo:
            add("INFO", book.name,
                f"{lang} 판 {len(done)}/{len(done) + len(todo)}장. 남은 장: {', '.join(todo)}")


def check_shelf(books: list[Path]) -> None:
    """저장소 첫 화면의 책장 카드가 실제 파일 수와 맞는지.

    아무도 안 보는 곳이라 조용히 틀어진다. 실제로 gstack 입문서가 「15장」으로 적혀
    있었는데 파일은 14장이었고, LLM Wiki 는 전부 쓴 뒤에도 「8장 공개」가 남아 있었다.
    """
    shelf = ROOT / "index.html"
    if not shelf.exists():
        return
    html = shelf.read_text(encoding="utf-8")
    for m in re.finditer(r'<a href="([a-z0-9-]+)/" class="book-row">(.*?)</a>', html, re.S):
        slug, card = m.group(1), m.group(2)
        chapters = ROOT / slug / "chapters"
        if not chapters.is_dir():
            add("ERROR", "index.html", f"책장이 없는 책을 가리킴: {slug}/")
            continue
        ko = [p for p in chapters.glob("*.html") if ".en." not in p.name]
        n_ch = len([p for p in ko if p.name.startswith("ch")])
        n_ap = len([p for p in ko if p.name.startswith("appendix")])
        want = f"{n_ch}장" + (f" · 부록 {n_ap}" if n_ap else "")
        if want not in card:
            claim = re.findall(r"<span>([^<]*장[^<]*)</span>", card)
            add("ERROR", "index.html",
                f"{slug} 책장 표기 {claim or ['없음']} ≠ 실제 「{want}」")


def check_sidebar_identical(book: Path) -> None:
    """한 책의 사이드바 목차는 모든 페이지에서 같아야 한다.

    페이지마다 손으로 들어 있어서 일부만 고치면 두 벌이 된다.
    실제로 skills-creation 에서 아홉 파일만 라벨을 고치는 바람에
    나머지 열두 파일이 옛 목차를 들고 있었다. 독자는 장을 넘길 때마다
    목차가 바뀌는 걸 본다.

    현재 링크 표시(nav-link-active 같은 것)는 페이지마다 달라야 하므로 빼고 본다.
    언어가 다르면 목차도 다르므로 판본별로 나눠 본다.
    """
    groups: dict[str, list[tuple[Path, str]]] = {}
    for p in sorted(book.glob("*.html")) + sorted((book / "chapters").glob("*.html")):
        html = p.read_text(encoding="utf-8")
        m = re.search(r'<ul class="nav-list">(.*?)</ul>', html, re.S)
        if not m:
            continue
        # 라벨만 뽑는다. href 는 index 와 chapters 가 다를 수밖에 없다.
        labels = tuple(re.findall(r'class="nav-(?:link|part)"[^>]*>([^<]*)<', m.group(1))) \
            or tuple(re.findall(r'>([^<>]+)</(?:a|li)>', m.group(1)))
        lang = "en" if ".en." in p.name else "ko"
        groups.setdefault(lang, []).append((p, "".join(labels)))

    for lang, rows in groups.items():
        counts = Counter(sig for _, sig in rows)
        if len(counts) <= 1:
            continue
        major, _ = counts.most_common(1)[0]
        odd = [p for p, sig in rows if sig != major]
        add("ERROR", book.name,
            f"{lang} 사이드바가 {len(counts)}벌이다. 다수와 다른 파일 {len(odd)}개: "
            + ", ".join(p.name for p in odd[:6]))


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
    """영어판에 남은 한글은 필드 값뿐이어야 한다.

    세 자리는 한글이 남아 있는 게 맞다. 번역해 버리면 오히려 망가진다.
      - 「나쁜 예」 코드 블록. 10장이 보여주려는 게 현장 볼트에 굴러다니는
        「진행중 / 거의 다 됐음 / 운영중?」 같은 제각각인 한글 상태값 자체다.
      - 파이썬 소스 안의 정규식 문자 클래스 [A-Za-z_가-힣]. 코드다.
      - 용어 사전의 한국어 대응어 <span class="term-en">(온톨로지)</span>.
        영어 독자가 한국어판으로 건너갈 다리라서 일부러 남긴다.
    """
    if ".en." not in f.name:
        return
    keep = set(INV["en_keep_korean"]["tokens"])
    body = re.sub(r"<svg.*?</svg>", "", html, flags=re.S)
    body = re.sub(r'<ul class="nav-list">.*?</ul>', "", body, flags=re.S)
    body = re.sub(r'<span class="term-en">\([^)]*\)</span>', "", body)
    body = re.sub(r"[\[(][^\[\]()]*가-힣[^\[\]()]*[\])]", "", body)
    markers = INV["forbidden_field_aliases"]["allowed_context_markers"]
    body = re.sub(r"<pre>.*?</pre>",
                  lambda m: "" if any(k in m.group(0) for k in markers) else m.group(0),
                  body, flags=re.S)
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

    check_shelf(books)

    files = 0

    # 루트 서가는 책 폴더가 아니라서 아래 순회에 안 걸린다. 그런데 독자가
    # 가장 먼저 보는 쪽이다. 실제로 문체 규약이 네 권을 훑는 동안 서가에는
    # 한국어 em dash 두 개가 그대로 남아 있었다.
    for f in sorted(ROOT.glob("index*.html")):
        html = f.read_text(encoding="utf-8")
        files += 1
        check_prose_metrics(f, html, budgets=False)
        check_en_korean_leftovers(f, html)

    # README 는 저장소의 첫 인상이라 문체 규약이 그대로 적용된다.
    # 루트 마크다운을 통째로 걸지는 않는다. STYLE.md 가 「나쁜 예」로 em dash 를
    # 27개 들고 있어서, 규약 문서가 자기 규약에 걸리기 때문이다.
    readme = ROOT / "README.md"
    if readme.exists():
        md = re.sub(r"```.*?```", "", readme.read_text(encoding="utf-8"), flags=re.S)
        files += 1
        check_prose_metrics(readme, md, budgets=False)

    for book in books:
        if not book.exists():
            add("ERROR", book.name, "폴더 없음")
            continue
        check_structure(book)
        check_sidebar_identical(book)
        check_language_pairs(book)
        for f in sorted(book.rglob("*.html")):
            html = f.read_text(encoding="utf-8")
            files += 1
            for fn in (check_prose_metrics, check_svg_labels, check_forbidden_aliases, check_automation_write_policy,
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

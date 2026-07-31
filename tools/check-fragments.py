# -*- coding: utf-8 -*-
"""프래그먼트 입고 검사.

빌더에 넣기 전에 돌린다. 여기서 걸리면 조립할 필요가 없다.
`check-consistency.py` 는 조립된 페이지를 보고, 이건 원고를 본다.

사용: python tools/check-fragments.py [tools/frag/ch05.frag.html ...]
      인자가 없으면 tools/frag/ 전체
"""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

# 윈도우 콘솔은 cp949 라 한글·기호를 그냥 찍으면 죽는다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FRAG = ROOT / "tools" / "frag"
INV = json.loads((ROOT / "tools" / "invariants.json").read_text(encoding="utf-8"))

META_RE = re.compile(r"^<!--META\s*(\{.*?\})\s*-->\s*", re.S)
REQUIRED_META = ["file", "num", "title", "subtitle", "desc", "minutes",
                 "prev_href", "prev_label", "next_href", "next_label"]

VOID = {"br", "img", "meta", "link", "input", "hr", "path", "circle", "rect",
        "line", "polygon", "polyline", "use", "stop", "ellipse", "source",
        "col", "area", "base", "marker", "text", "tspan"}

findings: list[tuple[str, str, str]] = []


def add(level: str, where: str, msg: str) -> None:
    findings.append((level, where, msg))


def visible(html: str) -> str:
    """태그와 코드 블록을 걷어낸 산문. 인용된 출력은 산문이 아니다 (STYLE.md §8-1)."""
    s = re.sub(r"<pre.*?</pre>", " ", html, flags=re.S)
    s = re.sub(r"<svg.*?</svg>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return unescape(s)


class Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"짝 없는 </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"안 닫힌 <{self.stack.pop()}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"엉뚱한 </{tag}>")


def check(path: Path) -> None:
    where = path.name
    raw = path.read_text(encoding="utf-8")

    m = META_RE.match(raw)
    if not m:
        add("ERROR", where, "META 주석이 없다. 빌더가 못 읽는다")
        return
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        add("ERROR", where, f"META 가 올바른 JSON 이 아니다: {e}")
        return
    for k in REQUIRED_META:
        if k not in meta:
            add("ERROR", where, f"META 에 {k} 가 없다")

    body = raw[m.end():]

    if body.count("<article>") != 1 or body.count("</article>") != 1:
        add("ERROR", where, "<article> 가 정확히 하나여야 한다")

    bal = Balance()
    bal.feed(body)
    for e in bal.errors[:5]:
        add("ERROR", where, f"태그 균형: {e}")
    if bal.stack:
        add("ERROR", where, f"안 닫힌 태그: {bal.stack[:5]}")

    prose = visible(body)                      # 문체 지표용. 코드·SVG 를 뺀 산문
    # 분량은 지침과 같은 방식으로 잰다. 태그만 걷고 코드 블록은 남긴다.
    # 두 값을 섞으면 코드가 많은 장이 억울하게 짧다고 나온다.
    full = unescape(re.sub(r"<svg.*?</svg>", " ", body, flags=re.S))
    full = re.sub(r"<[^>]+>", " ", full)
    chars = len(re.sub(r"\s+", "", full))

    # 분량. 출간된 장이 3,800~8,800자다(공백 제외, 코드 포함).
    # 도입부 세 장(ch01·02·04)이 짧은 축이라 하한을 그 아래로 둔다.
    # 미작성 장은 설계·템플릿·스크립트가 많아 더 길어지는 게 자연스럽다.
    floor, thin, hi = (3000, 5000, 14000)
    if chars < floor:
        add("ERROR", where, f"본문 {chars}자. 장이라기엔 너무 짧다 (최소 {floor})")
    elif chars < thin:
        add("WARN", where, f"본문 {chars}자. 출간된 장 중 짧은 축이다")
    elif chars > hi:
        add("WARN", where, f"본문 {chars}자. 너무 길다 (권장 상한 {hi})")
    else:
        add("INFO", where, f"본문 {chars}자")

    # 읽는 시간이 분량과 맞는지
    if "minutes" in meta:
        try:
            declared = int(str(meta["minutes"]))
            speed = INV["constants"]["reading_speed_chars_per_min"]
            actual = max(1, round(chars / speed))
            # 읽는 속도는 불변식이 정본이다. 장마다 다른 공식을 쓰면
            # 「약 12분」이 5분짜리 글에 붙는 일이 생긴다. 실제로 그랬다.
            if abs(declared - actual) > 2:
                add("WARN", where, f"읽는 시간 {declared}분, 분량 기준 {actual}분 (분당 {speed}자)")
        except ValueError:
            add("ERROR", where, f"minutes 가 숫자가 아니다: {meta['minutes']}")

    # 무관용 문체
    for tok, limit in INV["prose_rules"]["zero_tolerance"].items():
        needle = "—" if tok == "em_dash" else tok
        n = prose.count(needle)
        if n > limit:
            add("ERROR", where, f"{tok} {n}개 (허용 {limit})")

    # 비율 예산
    if chars >= INV["prose_rules"]["budget_min_chars"]:
        for tok, per10k in INV["prose_rules"]["budget_per_10k_chars"].items():
            rate = prose.count(tok) / chars * 10000
            if rate > per10k:
                add("WARN", where, f"{tok} 1만자당 {rate:.1f} (예산 {per10k})")

    # 인라인 스타일 — 다크 모드에서 깨진다
    n = len(re.findall(r"\sstyle=", body))
    if n:
        add("ERROR", where, f"인라인 style 속성 {n}개")

    # SVG 는 전면 배경 rect 가 있어야 다크 모드에서 글자가 보인다
    for i, svg in enumerate(re.findall(r"<svg[^>]*>.*?</svg>", body, flags=re.S)):
        head = svg[:400]
        if "<rect" not in head or "fill" not in head:
            add("ERROR", where, f"{i + 1}번째 SVG 에 전면 배경 rect 가 없다")

    # 금지 필드명 — 나쁜 예 표시가 곁에 있어야 쓸 수 있다
    cfg = INV["forbidden_field_aliases"]
    for blk in re.findall(r"<pre>.*?</pre>", body, flags=re.S):
        text = unescape(re.sub(r"<[^>]+>", "", blk))
        for alias in cfg["aliases"]:
            for mm in re.finditer(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", text):
                win = text[max(0, mm.start() - 220): mm.end() + 220]
                if not any(k in win for k in cfg["allowed_context_markers"]):
                    add("ERROR", where, f"예제에서 비정본 필드명 「{alias}」 사용")

    # 배타적 주장
    pol = INV["automation_write_policy"]
    if len(pol["allowed"]) > 1:
        for pat in pol["exclusive_claim_patterns"]:
            if pat in body:
                add("ERROR", where, f"배타적 주장 「{pat}」. 허용 폴더는 {pol['allowed']}")

    # 이모지. ✅❌★ 는 이미 출간된 장의 비교표에서 쓰는 기호라 허용한다.
    # 막으려는 것은 글을 꾸미려고 넣는 그림 문자다.
    allowed_marks = set("✅❌★☆→←↑↓·✔✘")
    emoji = [c for c in re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", prose)
             if c not in allowed_marks]
    if emoji:
        add("ERROR", where, f"이모지 {len(emoji)}개: {''.join(sorted(set(emoji))[:6])}")

    # 장 마무리 관례
    for cls, label in (("recap-box", "정리 상자"), ("next-teaser", "다음 장 예고")):
        if cls not in body:
            add("WARN", where, f"{label}({cls})가 없다")


def main() -> int:
    args = [Path(a) for a in sys.argv[1:]]
    files = args or sorted(FRAG.glob("*.frag.html"))
    if not files:
        print("검사할 프래그먼트가 없다")
        return 0
    for f in files:
        check(f)

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x[0]], x[1]))
    counts = {lv: 0 for lv in order}
    for lv, where, msg in findings:
        counts[lv] += 1
    print(f"프래그먼트 {len(files)}개 검사\n")
    for lv in ("ERROR", "WARN", "INFO"):
        rows = [(w, m) for l, w, m in findings if l == lv]
        if not rows:
            continue
        print(f"{lv} {len(rows)}건")
        for w, m in rows:
            print(f"   {w:26s} {m}")
        print()
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())

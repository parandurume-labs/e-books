# -*- coding: utf-8 -*-
"""설명 없이 쓰이는 기술 용어를 찾는다.

왜 있나
  ch10 이 `exit 2` 를 열두 번 쓰고 「이게 핵심」이라 하면서
  종료 코드가 무엇인지는 한 번도 설명하지 않았다.
  사실은 맞는데 독자가 따라올 수 없는 상태였고, 뜻 검수자 넷이 전부 놓쳤다.
  「이 주장이 사실인가」만 보면 이 결함은 안 잡힌다.

무엇을 세나
  **산문 안의 인라인 `<code>`** 에 자주 나오는 토큰 중,
  어디서도 풀어 쓰이지 않은 것.

  코드 블록은 보지 않는다. 거기 있는 이름은 그냥 예제 변수일 뿐이고,
  그것까지 세면 파이썬 키워드가 목록을 덮어 아무도 안 보게 된다
  (처음에 그렇게 만들었다가 부록 B 하나에서 50건이 나왔다).
  산문에서 `exit 2` 처럼 인라인 코드로 가리켰다면, 그건 책이 개념으로 다룬다는 뜻이다.

  「풀어 쓰였다」의 판정은 느슨하다. 그 토큰 근처 산문에
  설명으로 보이는 말(~란, ~이란, ~는 뜻, ~를 말해, 무엇인가 …)이 있으면 통과.
  느슨하게 잡고 사람이 거르는 편이 낫다. 반대로 하면 목록이 길어져 아무도 안 본다.

쓰는 법
  python tools/check-unexplained.py [책폴더 ...]
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from html import unescape
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 설명으로 보이는 말. 이 중 하나가 토큰 근처에 있으면 「풀어 썼다」로 본다.
EXPLAINED = ["란 ", "이란", "라는 뜻", "는 뜻", "라는 말", "를 말해", "을 말해",
             "무엇인가", "뭔가요", "뜻이에요", "뜻입니다", "의미해", "가리켜",
             "라고 해요", "이라고 해요", "라고 부르", "이라고 부르",
             "약속이", "규칙이에요", "역할을 해", "하는 일이", "하는 거예요"]

# 흔한 낱말과 고유명사는 굳이 정의할 필요가 없다.
SKIP = {
    "true", "false", "null", "npm", "git", "python3", "bash", "json", "yaml",
    "md", "html", "css", "js", "sh", "txt", "csv", "png", "http", "https",
    "claude", "gstack", "github", "obsidian", "teams", "onedrive", "sharepoint",
    "read", "write", "edit", "bash", "glob", "grep", "cd", "ls", "dir", "cat",
    "main", "master", "origin", "readme", "src", "env",
}

TOKEN = re.compile(r"[A-Za-z_][\w.\-]{2,28}")


def visible_prose(html: str) -> str:
    """산문만. 코드와 그림을 뺀다."""
    try:
        body = html[html.index("<article>"):html.index("</article>")]
    except ValueError:
        body = html
    body = re.sub(r"<pre.*?</pre>|<svg.*?</svg>", " ", body, flags=re.S)
    return unescape(re.sub(r"<[^>]+>", " ", body))


def inline_code_in_prose(html: str) -> str:
    """산문 안의 인라인 <code> 만. 코드 블록은 뺀다."""
    try:
        body = html[html.index("<article>"):html.index("</article>")]
    except ValueError:
        body = html
    body = re.sub(r"<pre.*?</pre>|<svg.*?</svg>", " ", body, flags=re.S)
    return unescape(" ".join(re.findall(r"<code>(.*?)</code>", body, flags=re.S)))


def scan(path: Path) -> list[tuple[str, int, int]]:
    html = path.read_text(encoding="utf-8")
    prose = visible_prose(html)
    code = inline_code_in_prose(html)

    counts = Counter(t for t in TOKEN.findall(code) if t.lower() not in SKIP)
    out = []
    for tok, n in counts.items():
        if n < 4:                      # 서너 번 넘게 가리켰다면 개념으로 쓰는 것이다
            continue
        # 산문에 그 토큰이 나오는 자리마다 설명이 곁에 있는지
        explained = False
        for m in re.finditer(re.escape(tok), prose):
            win = prose[max(0, m.start() - 160): m.end() + 220]
            if any(k in win for k in EXPLAINED):
                explained = True
                break
        if not explained:
            in_prose = len(re.findall(re.escape(tok), prose))
            out.append((tok, n, in_prose))
    return sorted(out, key=lambda x: -x[1])


def main() -> int:
    args = sys.argv[1:]
    books = [ROOT / a for a in args] if args else [
        d for d in sorted(ROOT.iterdir())
        if d.is_dir() and (d / "index.html").exists() and d.name not in ("assets", "tools")
    ]
    total = 0
    for book in books:
        rows = []
        for p in sorted((book / "chapters").glob("*.html")):
            if ".en." in p.name:
                continue
            for tok, n, in_prose in scan(p):
                rows.append((p.name, tok, n, in_prose))
        if not rows:
            continue
        print(f"\n=== {book.name} ===")
        for name, tok, n, in_prose in rows:
            flag = "  ← 산문에 한 번도 안 나옴" if in_prose == 0 else ""
            print(f"  {name:18s} {tok:24s} 인라인 {n:3d}회 · 산문 {in_prose:2d}회{flag}")
            total += 1
    print(f"\n설명이 안 보이는 토큰 {total}건")
    print("느슨하게 잡은 목록이다. 사람이 읽고 진짜 설명이 필요한 것만 고른다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

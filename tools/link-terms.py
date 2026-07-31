# -*- coding: utf-8 -*-
"""본문 첫 등장 용어에 용어 사전 링크를 단다.

태그 사이의 순수 텍스트 조각만 건드린다. 태그 내부나 속성값은 절대 만지지 않는다
(LEARNINGS L4: 인라인 태그가 섞인 문장에 부분 치환을 하면 문장이 깨진다).
pre/code/a/제목/svg 안은 건너뛴다. 파일마다 용어당 한 번만 링크한다.
"""
import io, re, pathlib, sys

TERMS = [
    # 긴 것부터. 「지식 그래프」가 「그래프」보다 먼저 걸려야 한다.
    ("컨텍스트 윈도우", "context-window"),
    ("단일 진실 공급원", "ssot"),
    ("지식 그래프", "knowledge-graph"),
    ("그래프 순회", "traversal"),
    ("관계 술어", "relation"),
    ("통제 어휘", "controlled-vocab"),
    ("분류 체계", "taxonomy"),
    ("예약 작업", "scheduled-task"),
    ("프론트매터", "frontmatter"),
    ("위키링크", "wikilink"),
    ("온톨로지", "ontology"),
    ("에이전트", "agent"),
    ("임베딩", "embedding"),
    ("식별자", "identifier"),
    ("백링크", "backlink"),
    ("옵시디언", "obsidian"),
    ("환각", "hallucination"),
    ("볼트", "vault"),
    ("LLM Wiki", "llm-wiki"),
    ("RAG", "rag"),
    ("MOC", "moc"),
    ("TRL", "trl"),
    ("AX", "ax"),
]

HANGUL = r"가-힣"
SKIP_TAGS = {"pre", "code", "a", "h1", "h2", "h3", "h4", "h5", "h6",
             "svg", "title", "script", "style", "figcaption"}


def make_pattern(term):
    if re.match(r"^[A-Za-z]", term):          # 영문 약어는 낱말 경계로
        return re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(term) + r"(?![A-Za-z0-9_-])")
    # 한글은 앞뒤에 한글이 붙으면 다른 낱말이다 (예: 「볼트」 vs 「볼트제어」)
    return re.compile(r"(?<![" + HANGUL + r"])" + re.escape(term) + r"(?![" + HANGUL + r"])")


PATS = [(t, a, make_pattern(t)) for t, a in TERMS]


def link_file(path: pathlib.Path) -> int:
    html = io.open(path, encoding="utf-8").read()
    try:
        a0 = html.index("<article>")
        a1 = html.index("</article>")
    except ValueError:
        return 0
    head, body, tail = html[:a0], html[a0:a1], html[a1:]

    done = set()
    out = []
    depth = 0                       # 건너뛸 태그 안에 있는 깊이
    pos = 0
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^>]*)>", body):
        text = body[pos:m.start()]
        if depth == 0 and text.strip():
            for term, anchor, pat in PATS:
                if anchor in done:
                    continue
                mm = pat.search(text)
                if mm:
                    text = (text[:mm.start()]
                            + f'<a href="appendix-a.html#{anchor}" class="term-link">{term}</a>'
                            + text[mm.end():])
                    done.add(anchor)
        out.append(text)
        out.append(m.group(0))
        pos = m.end()

        closing, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag in SKIP_TAGS and not attrs.rstrip().endswith("/"):
            depth += -1 if closing else 1
            depth = max(depth, 0)
    out.append(body[pos:])

    new_body = "".join(out)
    if new_body == body:
        return 0
    io.open(path, "w", encoding="utf-8").write(head + new_body + tail)
    return len(done)


def main():
    total = 0
    for p in sorted(pathlib.Path("building-company-llm-wiki/chapters").glob("ch*.html")):
        if p.name.endswith(".en.html"):
            continue
        n = link_file(p)
        total += n
        print(f"{p.name:16s} 링크 {n}개")
    print("합계", total)


if __name__ == "__main__":
    main()

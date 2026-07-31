# -*- coding: utf-8 -*-
"""회사용 LLM Wiki 만들기 — 이중 언어 챕터 빌더.

하는 일
  1) frag/chNN.frag.html      → chapters/chNN.html      (한국어)
  2) frag-en/chNN.en.frag.html → chapters/chNN.en.html  (영어)
  3) 모든 파일의 <ul class="nav-list"> 를 언어별 정본 목차로 교체
  4) 짝이 있는 파일끼리 <link rel="alternate" hreflang> 를 상호 주입
     (짝이 없으면 안 넣는다 → book.js 가 스위처를 안 만든다 → 404 없음)

사용
  python build.py            전부
  python build.py nav        목차·hreflang 만 갱신 (프래그먼트 무시)
"""
import json
import re
import sys
from pathlib import Path

BOOK = Path(r"c:/Dev/Inhee/e-books/building-company-llm-wiki")
FRAG_KO = Path(__file__).parent / "frag"
FRAG_EN = Path(__file__).parent / "frag-en"

# ---------------------------------------------------------------- 정본 목차
# (한국어 라벨, 영어 라벨, 파일명 또는 None=미작성, 앵커id)
# 파트 헤더는 파일명·앵커가 모두 None.
NAV = [
    ("표지와 목차", "Cover and contents", "__index__", "hero"),
    ("제1부: 왜 필요한가", "Part 1 · Why you need this", None, None),
    ("1장 우리 지식은 어디에", "1. Where our knowledge lives", "ch01.html", "ch1"),
    ("2장 RAG가 아니라 위키다", "2. A wiki, not RAG", "ch02.html", "ch2"),
    ("3장 온톨로지와 위키의 구분", "3. Ontology is not the wiki", "ch03.html", "ch3"),
    ("4장 도구 세 개의 역할", "4. Three tools, three jobs", "ch04.html", "ch4"),
    ("제2부: 준비 · 30분 셋업", "Part 2 · Setup in 30 minutes", None, None),
    ("5장 옵시디언과 볼트", "5. Obsidian and the vault", "ch05.html", "ch5"),
    ("6장 Teams로 팀 연결", "6. Sharing through Teams", "ch06.html", "ch6"),
    ("7장 Cowork에 볼트 연결", "7. Connecting the vault to Cowork", "ch07.html", "ch7"),
    ("제3부: 온톨로지 설계", "Part 3 · Designing the ontology", None, None),
    ("8장 설계 원칙 여섯 개", "8. Six design principles", "ch08.html", "ch8"),
    ("9장 클래스 정하기", "9. Choosing your classes", "ch09.html", "ch9"),
    ("10장 관계와 필드 설계", "10. Relations and fields", "ch10.html", "ch10"),
    ("제4부: 운영", "Part 4 · Running it", None, None),
    ("11장 CLAUDE.md", "11. CLAUDE.md", "ch11.html", "ch11"),
    ("12장 템플릿과 첫 노트", "12. Templates and your first note", "ch12.html", "ch12"),
    ("13장 스킬로 자동화", "13. Automating with skills", "ch13.html", "ch13"),
    ("제5부: 자동화와 시각화", "Part 5 · Automation and visibility", None, None),
    ("14장 스케줄링", "14. Scheduling", "ch14.html", "ch14"),
    ("15장 업무 진행 시각화", "15. Making progress visible", "ch15.html", "ch15"),
    ("16장 자동화 레시피 12선", "16. Twelve automation recipes", "ch16.html", "ch16"),
    ("제6부: 지속", "Part 6 · Keeping it alive", None, None),
    ("17장 품질을 코드로", "17. Quality as code", "ch17.html", "ch17"),
    ("18장 의도와 실행의 대조", "18. Intent versus execution", "ch18.html", "ch18"),
    ("제7부: AX로 확장", "Part 7 · Scaling to AX", None, None),
    ("19장 위키에서 AX로", "19. From wiki to AX", "ch19.html", "ch19"),
    ("부록", "Appendices", None, None),
    ("부록 A: 용어 사전", "Appendix A · Glossary", "appendix-a.html", "appendix-a"),
    ("부록 B: 복붙용 자산", "Appendix B · Copy-paste assets", "appendix-b.html", "appendix-b"),
    ("부록 C: 트러블슈팅", "Appendix C · Troubleshooting", "appendix-c.html", "appendix-c"),
]

COMING = {"ko": "coming-soon.html", "en": "coming-soon.en.html"}


def en_name(ko_file: str) -> str:
    """ch14.html → ch14.en.html · index.html → index.en.html"""
    return ko_file[:-5] + ".en.html"


def nav_html(lang: str, for_index: bool) -> str:
    out = []
    for ko, en, target, anchor in NAV:
        label = ko if lang == "ko" else en
        if target is None and anchor is None:
            out.append(f'      <li class="nav-part">{label}</li>')
            continue
        if for_index:
            href = f"#{anchor}"
        elif target == "__index__":
            href = "../index.html" if lang == "ko" else "../index.en.html"
        elif target is None:
            href = COMING[lang]
        else:
            # 한국어판만 있고 영어판이 아직 없는 장이 있다. 표를 믿지 말고
            # 실제 파일이 있는지 본다. 없으면 coming-soon 으로 보낸다.
            # 이게 없으면 영어 목차가 ch05.en.html 같은 없는 파일을 가리켜 404 가 난다.
            want = target if lang == "ko" else en_name(target)
            href = want if (BOOK / "chapters" / want).exists() else COMING[lang]
        out.append(f'      <li><a href="{href}" class="nav-link">{label}</a></li>')
    return "\n".join(out)


NAV_RE = re.compile(r'(<ul class="nav-list">\n).*?(\n\s*</ul>)', re.S)


def page_lang(path: Path, src: str) -> str:
    if ".en." in path.name:
        return "en"
    m = re.search(r'<html lang="([a-z]{2})"', src)
    return m.group(1) if m else "ko"


def rewrite_nav(path: Path) -> None:
    src = path.read_text(encoding="utf-8")
    lang = page_lang(path, src)
    for_index = path.name.startswith("index")
    new, n = NAV_RE.subn(
        lambda m: m.group(1) + nav_html(lang, for_index) + m.group(2), src, count=1
    )
    if n == 0:
        print(f"  !! nav-list 없음: {path.name}")
        return
    if new != src:
        path.write_text(new, encoding="utf-8")
        print(f"  목차 갱신: {path.name} ({lang})")


ALT_RE = re.compile(r'\n *<link rel="alternate" hreflang="[a-z]{2}"[^>]*>')


def link_alternates() -> None:
    """짝이 있는 파일끼리만 hreflang 을 넣는다."""
    pairs = []
    for ko in sorted(BOOK.glob("*.html")) + sorted((BOOK / "chapters").glob("*.html")):
        if ".en." in ko.name:
            continue
        en = ko.with_name(en_name(ko.name))
        if en.exists():
            pairs.append((ko, en))

    # 먼저 전부 지운다 (짝이 사라졌을 때 유령 링크가 남지 않게)
    for f in sorted(BOOK.glob("*.html")) + sorted((BOOK / "chapters").glob("*.html")):
        s = f.read_text(encoding="utf-8")
        s2 = ALT_RE.sub("", s)
        if s2 != s:
            f.write_text(s2, encoding="utf-8")

    for ko, en in pairs:
        for src_file, other_lang, other_href in (
            (ko, "en", en.name),
            (en, "ko", ko.name),
        ):
            s = src_file.read_text(encoding="utf-8")
            tag = f'\n  <link rel="alternate" hreflang="{other_lang}" href="{other_href}">'
            s = s.replace('\n  <link rel="stylesheet" href=', tag + '\n  <link rel="stylesheet" href=', 1)
            src_file.write_text(s, encoding="utf-8")
    print(f"  hreflang 상호 연결: {len(pairs)}쌍")


# ---------------------------------------------------------------- 챕터 셸
SHELL = """<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_prefix}{num}: {title} · {book}</title>
  <meta name="description" content="{desc}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../assets/css/book.css">
  <link rel="stylesheet" href="../css/theme.css">
  <script>try{{var t=localStorage.getItem('pdm-ebook-theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme:dark)').matches))document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
</head>
<body>
<div class="progress-bar" id="progressBar"></div>
<a class="skip-link" href="#main">{skip}</a>
<header class="mobile-header">
  <button class="hamburger" id="hamburgerBtn" aria-label="{toc_open}"><span></span><span></span><span></span></button>
  <span class="mobile-title">{book}</span>
  <button class="search-trigger" type="button" aria-label="{search_aria}"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg><span>{search}</span><kbd>⌘K</kbd></button>
  <button class="dark-mode-toggle" id="darkModeToggleHeader" type="button" aria-label="{dark}"><svg class="icon-sun" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg><svg class="icon-moon" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg></button>
</header>
<nav class="sidebar" id="sidebar" aria-label="{toc}">
  <div class="sidebar-header">
    <span class="sidebar-logo"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15.5 13a3.5 3.5 0 0 0 0 7h.5a2 2 0 0 0 2-2V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3v14"/><path d="M8.5 13a3.5 3.5 0 0 1 0 7H8a2 2 0 0 1-2-2V6a3 3 0 0 1 3-3 3 3 0 0 1 3 3"/></svg></span>
    <span class="sidebar-title">{toc}</span>
    <button class="sidebar-close" id="sidebarClose" type="button" aria-label="{toc_close}">&times;</button>
  </div>
  <div class="sidebar-content">
    <ul class="nav-list">
{nav}
    </ul>
  </div>
  <div class="sidebar-footer">
    <button class="dark-mode-toggle" id="darkModeToggleSidebar" type="button" aria-label="{dark}"><svg class="icon-sun" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg><svg class="icon-moon" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg><span class="toggle-label">{dark_label}</span></button>
  </div>
</nav>
<div class="sidebar-overlay" id="sidebarOverlay"></div>
<main class="main-content" id="main">
  <div class="chapter-shell">
<div class="chapter-content">
  <header class="chapter-header">
    <span class="chapter-number">{eyebrow} {num}</span>
    <h1>{title}</h1>
    <p class="chapter-subtitle">{subtitle}</p>
    <span class="reading-time"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/></svg>{minutes_label}</span>
  </header>

{article}

  <nav class="chapter-nav">
    <a href="{prev_href}" class="back-to-toc">← {prev_label}</a>
    <a href="{next_href}" class="next">{next_label} →</a>
  </nav>
</div>
    <aside class="rail" id="rail" aria-label="{rail}"></aside>
  </div>
</main>
<div class="palette" id="palette" role="dialog" aria-modal="true" aria-label="{search_aria}">
  <div class="palette-box">
    <input class="palette-input" type="text" placeholder="{search_ph}" aria-label="{search_label}">
    <ul class="palette-results"></ul>
  </div>
</div>
<script src="../../assets/js/book.js"></script>
</body>
</html>
"""

CHROME = {
    "ko": dict(
        book="회사용 LLM Wiki 만들기", title_prefix="Chapter ", eyebrow="CHAPTER",
        skip="본문으로 건너뛰기", toc="목차", toc_open="목차 열기", toc_close="목차 닫기",
        search="검색", search_aria="목차 검색", search_ph="장 제목으로 찾기", search_label="검색어",
        dark="다크모드 전환", dark_label="다크모드", rail="이 장에서",
    ),
    "en": dict(
        book="Building a Company LLM Wiki", title_prefix="Chapter ", eyebrow="CHAPTER",
        skip="Skip to content", toc="Contents", toc_open="Open contents", toc_close="Close contents",
        search="Search", search_aria="Search contents", search_ph="Find a chapter", search_label="Search",
        dark="Toggle dark mode", dark_label="Dark mode", rail="On this page",
    ),
}

META_RE = re.compile(r"^<!--META\s*(\{.*?\})\s*-->\s*", re.S)


def build_fragment(frag_path: Path, lang: str) -> None:
    raw = frag_path.read_text(encoding="utf-8")
    m = META_RE.match(raw)
    if not m:
        sys.exit(f"메타 주석 없음: {frag_path}")
    meta = json.loads(m.group(1))
    article = raw[m.end():].rstrip() + "\n"
    mins = meta["minutes"]
    meta["minutes_label"] = f"약 {mins}분" if lang == "ko" else f"about {mins} min"
    # META 값이 CHROME 기본값을 덮어쓸 수 있게 먼저 합친다.
    # 부록은 title_prefix/eyebrow 를 바꿔서 「Chapter B」 대신 「부록 B」가 되게 한다.
    params = {**CHROME[lang], **meta}
    out = SHELL.format(
        lang=lang, nav=nav_html(lang, False), article=article, **params
    )
    dest = BOOK / "chapters" / meta["file"]
    dest.write_text(out, encoding="utf-8")
    print(f"  생성: {dest.name}  ({len(out) // 1024}KB)")


def all_pages():
    return sorted(BOOK.glob("*.html")) + sorted((BOOK / "chapters").glob("*.html"))


def main() -> None:
    only_nav = "nav" in sys.argv[1:]
    if not only_nav:
        for folder, lang in ((FRAG_KO, "ko"), (FRAG_EN, "en")):
            if not folder.is_dir():
                continue
            for f in sorted(folder.glob("*.frag.html")):
                build_fragment(f, lang)
    print("정본 목차 주입")
    for p in all_pages():
        rewrite_nav(p)
    print("언어 상호 연결")
    link_alternates()


if __name__ == "__main__":
    main()

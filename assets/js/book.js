/* ==========================================================================
   파란두루미 e-book 공용 스크립트 v2.1
   사이드바 · 다크모드(영구 저장) · 진행 바 · 이 장에서 · ⌘K 검색
   v2.1 리더 기능: 복사 버튼 · 이어보기 · 진행률/남은 시간 · 글자 크기 · 키보드 이동
   설계 원칙 — 모든 UI 를 런타임에 심는다. 책의 HTML 은 건드리지 않는다.
   ========================================================================== */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- UI 문자열 ----------
     <html lang> 을 보고 고른다. 영어판이 한국어 UI 를 쓰지 않게 하는 장치. */
  var LANG = (document.documentElement.getAttribute('lang') || 'ko').slice(0, 2) === 'en' ? 'en' : 'ko';
  var STRINGS = {
    ko: {
      railTitle: '이 장에서',
      copy: '복사', copied: '복사됨', copyFail: '직접 선택해 주세요', copyAria: '이 블록 복사',
      tableHint: '→ 표를 좌우로 밀어서 보세요',
      resume: function (p) { return '읽던 곳으로 (' + p + '%)'; },
      startOver: '처음부터', resumeClose: '이어보기 닫기',
      minsLeft: function (m) { return m + '분 남음'; }, finished: '다 읽었습니다',
      about: function (m) { return '약 ' + m + '분'; },
      position: function (n, i) { return n + '장 중 ' + i + '번째'; },
      prevCh: '이전 장', nextCh: '다음 장',
      textSize: '본문 글자 크기', smaller: '글자 작게', larger: '글자 크게',
      noResults: '결과가 없습니다'
    },
    en: {
      railTitle: 'On this page',
      copy: 'Copy', copied: 'Copied', copyFail: 'Select it manually', copyAria: 'Copy this block',
      tableHint: '→ Scroll the table sideways',
      resume: function (p) { return 'Pick up at ' + p + '%'; },
      startOver: 'Start over', resumeClose: 'Dismiss',
      minsLeft: function (m) { return m + ' min left'; }, finished: 'Finished',
      about: function (m) { return 'about ' + m + ' min'; },
      position: function (n, i) { return 'Chapter ' + i + ' of ' + n; },
      prevCh: 'Previous chapter', nextCh: 'Next chapter',
      textSize: 'Text size', smaller: 'Smaller text', larger: 'Larger text',
      noResults: 'No results'
    }
  };
  var T = STRINGS[LANG];

  /* ---------- 다크모드 ---------- */
  var THEME_KEY = 'pdm-ebook-theme';

  function applyTheme(t) {
    if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
  }

  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) {}
    if (saved) {
      applyTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      applyTheme('dark');
    }
    $$('.dark-mode-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch (e) {}
      });
    });
  }

  /* ---------- 사이드바 ---------- */
  function initSidebar() {
    var sidebar = $('#sidebar');
    var overlay = $('#sidebarOverlay');
    if (!sidebar) return;

    function open() {
      sidebar.classList.add('open');
      if (overlay) overlay.classList.add('open');
    }
    function close() {
      sidebar.classList.remove('open');
      if (overlay) overlay.classList.remove('open');
    }

    var burger = $('#hamburgerBtn');
    if (burger) burger.addEventListener('click', open);
    var closeBtn = $('#sidebarClose');
    if (closeBtn) closeBtn.addEventListener('click', close);
    if (overlay) overlay.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });

    $$('.sidebar .nav-link').forEach(function (a) {
      a.addEventListener('click', function () {
        if (window.innerWidth < 1024) close();
      });
    });

    var here = location.pathname.split('/').pop();
    $$('.sidebar .nav-link').forEach(function (a) {
      var target = (a.getAttribute('href') || '').split('/').pop();
      if (target && target === here) a.classList.add('active');
    });

    var active = $('.sidebar .nav-link.active');
    if (active && sidebar.querySelector('.sidebar-content')) {
      var box = sidebar.querySelector('.sidebar-content');
      var top = active.offsetTop - box.clientHeight / 2;
      if (top > 0) box.scrollTop = top;
    }
  }

  /* ---------- 진행 바 ---------- */
  function initProgress() {
    var bar = $('#progressBar');
    if (!bar) return;
    var raf = null;
    function update() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var pct = h > 0 ? (window.scrollY / h) * 100 : 0;
      bar.style.width = Math.min(100, Math.max(0, pct)) + '%';
      raf = null;
    }
    window.addEventListener('scroll', function () {
      if (!raf) raf = window.requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /* ---------- 이 장에서 (우측 레일) ---------- */
  function slug(text, i) {
    var s = text.trim().toLowerCase()
      .replace(/[^\wㄱ-ㅎ가-힣\s-]/g, '')
      .replace(/\s+/g, '-');
    return s ? 'h-' + s : 'h-' + i;
  }

  function initRail() {
    var rail = $('#rail');
    var article = $('.chapter-content article');
    if (!rail || !article) return;

    var heads = $$('h2, h3', article);
    if (heads.length < 3) { rail.style.display = 'none'; return; }

    var ol = document.createElement('ol');
    heads.forEach(function (h, i) {
      if (!h.id) h.id = slug(h.textContent, i);
      var li = document.createElement('li');
      if (h.tagName === 'H3') li.className = 'lv3';
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.textContent;
      a.title = h.textContent; // 레일 라벨은 두 줄로 잘리므로 전문은 툴팁으로
      li.appendChild(a);
      ol.appendChild(li);
    });

    var title = document.createElement('div');
    title.className = 'rail-title';
    title.textContent = T.railTitle;
    rail.appendChild(title);
    rail.appendChild(ol);

    var links = $$('a', ol);
    if (!('IntersectionObserver' in window)) return;

    var seen = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { seen[en.target.id] = en.isIntersecting; });
      var current = null;
      heads.forEach(function (h) { if (seen[h.id] && !current) current = h.id; });
      if (!current) return;
      links.forEach(function (a) {
        a.classList.toggle('active', a.getAttribute('href') === '#' + current);
      });
    }, { rootMargin: '-72px 0px -70% 0px' });

    heads.forEach(function (h) { io.observe(h); });
  }

  /* ---------- 랜딩 목차 하이라이트 ---------- */
  function initScrollSpy() {
    var links = $$('.sidebar .nav-link[href^="#"]');
    if (!links.length || !('IntersectionObserver' in window)) return;

    var map = {};
    links.forEach(function (a) {
      var id = a.getAttribute('href').slice(1);
      var el = document.getElementById(id);
      if (el) map[id] = a;
    });
    var ids = Object.keys(map);
    if (!ids.length) return;

    var visible = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
      var current = ids.filter(function (id) { return visible[id]; })[0];
      if (!current) return;
      links.forEach(function (a) { a.classList.remove('active'); });
      map[current].classList.add('active');
    }, { rootMargin: '-30% 0px -60% 0px' });

    ids.forEach(function (id) { io.observe(document.getElementById(id)); });
  }

  /* ---------- ⌘K 검색 ---------- */
  function initPalette() {
    var pal = $('#palette');
    if (!pal) return;

    var input = $('.palette-input', pal);
    var list = $('.palette-results', pal);

    var items = $$('.sidebar .nav-link').map(function (a) {
      var part = '';
      var node = a.closest('li');
      while (node && node.previousElementSibling) {
        node = node.previousElementSibling;
        if (node.classList && node.classList.contains('nav-part')) { part = node.textContent.trim(); break; }
      }
      return { label: a.textContent.trim(), href: a.getAttribute('href'), part: part };
    });

    function render(q) {
      var ql = q.trim().toLowerCase();
      var hits = ql
        ? items.filter(function (it) {
            return (it.label + ' ' + it.part).toLowerCase().indexOf(ql) !== -1;
          })
        : items.slice(0, 12);

      list.innerHTML = '';
      if (!hits.length) {
        var empty = document.createElement('li');
        empty.className = 'palette-empty';
        empty.textContent = T.noResults;
        list.appendChild(empty);
        return;
      }
      hits.forEach(function (it, i) {
        var li = document.createElement('li');
        if (i === 0) li.className = 'sel';
        var a = document.createElement('a');
        a.href = it.href;
        var strong = document.createElement('span');
        strong.textContent = it.label;
        a.appendChild(strong);
        if (it.part) {
          var p = document.createElement('span');
          p.className = 'palette-part';
          p.textContent = it.part;
          a.appendChild(p);
        }
        li.appendChild(a);
        list.appendChild(li);
      });
    }

    function open() {
      pal.classList.add('open');
      render('');
      input.value = '';
      input.focus();
    }
    function close() { pal.classList.remove('open'); }

    $$('.search-trigger').forEach(function (b) { b.addEventListener('click', open); });

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); open(); return; }
      if (!pal.classList.contains('open')) return;
      if (e.key === 'Escape') { close(); return; }
      if (e.key === 'Enter') {
        var sel = $('.palette-results li.sel a', pal);
        if (sel) location.href = sel.getAttribute('href');
        return;
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        var lis = $$('.palette-results li', pal).filter(function (li) { return !li.classList.contains('palette-empty'); });
        if (!lis.length) return;
        var idx = lis.findIndex(function (li) { return li.classList.contains('sel'); });
        lis.forEach(function (li) { li.classList.remove('sel'); });
        var next = e.key === 'ArrowDown' ? (idx + 1) % lis.length : (idx - 1 + lis.length) % lis.length;
        lis[next].classList.add('sel');
        lis[next].scrollIntoView({ block: 'nearest' });
      }
    });

    input.addEventListener('input', function () { render(input.value); });
    pal.addEventListener('click', function (e) { if (e.target === pal) close(); });
  }

  /* ---------- 표제 앵커 ---------- */
  function initAnchors() {
    var article = $('.chapter-content article');
    if (!article) return;
    $$('h2', article).forEach(function (h, i) {
      if (!h.id) h.id = slug(h.textContent, i);
    });
  }


  /* ---------- 깨진 일러스트 정리 ---------- */
  function initBrokenImages() {
    $$('.illustration img').forEach(function (img) {
      function drop() {
        var fig = img.closest('figure');
        if (fig) fig.remove(); else img.remove();
      }
      if (img.complete && img.naturalWidth === 0) drop();
      else img.addEventListener('error', drop);
    });
  }

  /* ======================================================================
     v2.1 리더 기능
     ====================================================================== */

  var SCALE_KEY = 'pdm-ebook-scale';
  var POS_KEY = 'pdm-ebook-pos';

  function isChapter() { return !!$('.chapter-content article'); }

  function chapterKey() {
    // 책 폴더 + 파일명. 컬렉션 안에서 장이 겹치지 않게.
    var parts = location.pathname.split('/').filter(Boolean);
    return parts.slice(-3).join('/');
  }

  function svgIcon(d) {
    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
           'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
  }

  /* ---------- 언어 스위처 ----------
     <link rel="alternate" hreflang="en" href="ch14.en.html"> 가 있는 페이지에만 생긴다.
     번역이 없는 장에는 스위처가 안 보이므로 깨진 링크가 생기지 않는다. */
  var LANG_KEY = 'pdm-ebook-lang';
  var LANG_LABEL = { ko: '한국어', en: 'English' };
  var LANG_SHORT = { ko: 'KO', en: 'EN' };

  function initLangSwitch() {
    var header = $('.mobile-header');
    if (!header) return;

    var alts = $$('link[rel="alternate"][hreflang]').filter(function (l) {
      return l.getAttribute('hreflang') && l.getAttribute('href');
    });
    if (!alts.length) return;

    var here = (document.documentElement.getAttribute('lang') || 'ko').slice(0, 2);
    var langs = [{ code: here, href: null }];
    alts.forEach(function (l) {
      var code = l.getAttribute('hreflang').slice(0, 2);
      if (code !== here) langs.push({ code: code, href: l.getAttribute('href') });
    });
    // ko 를 항상 앞에 둔다
    langs.sort(function (a, b) { return a.code === 'ko' ? -1 : b.code === 'ko' ? 1 : 0; });

    var box = document.createElement('div');
    box.className = 'lang-switch';
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', here === 'ko' ? '언어' : 'Language');

    langs.forEach(function (l) {
      var el, short = LANG_SHORT[l.code] || l.code.toUpperCase();
      if (!l.href) {
        el = document.createElement('span');
        el.setAttribute('aria-current', 'true');
      } else {
        el = document.createElement('a');
        el.href = l.href;
        el.setAttribute('hreflang', l.code);
        el.title = LANG_LABEL[l.code] || l.code;
        el.addEventListener('click', function () {
          try { localStorage.setItem(LANG_KEY, l.code); } catch (e) {}
        });
      }
      el.textContent = short;
      box.appendChild(el);
    });

    var anchor = $('.reader-tools', header) || $('.search-trigger', header) || $('.dark-mode-toggle', header);
    if (anchor) header.insertBefore(box, anchor);
    else header.appendChild(box);
    // 오른쪽 묶음의 첫 요소가 되었으므로 auto 마진을 넘겨받는다
    box.style.marginLeft = 'auto';
    var tools = $('.reader-tools', header);
    if (tools) tools.style.marginLeft = '0';
  }

  /* ---------- 상단바 리더 도구 (진행률 · 장 이동 · 글자 크기) ---------- */
  function initReaderTools() {
    var header = $('.mobile-header');
    if (!header || !isChapter()) return;

    var tools = document.createElement('div');
    tools.className = 'reader-tools';

    // 이전/다음 장 — 본문 하단 내비게이션에서 그대로 가져온다
    var navPrev = $('.chapter-nav .back-to-toc');
    var navNext = $('.chapter-nav .next');
    function arrow(link, glyph, label) {
      var a = document.createElement('a');
      a.className = 'chapter-arrow';
      a.innerHTML = svgIcon(glyph);
      a.setAttribute('aria-label', label);
      if (link && link.getAttribute('href')) {
        a.href = link.getAttribute('href');
        a.title = link.textContent.replace(/^[←→\s]+|[←→\s]+$/g, '');
      } else {
        a.setAttribute('aria-disabled', 'true');
      }
      return a;
    }
    tools.appendChild(arrow(navPrev, '<path d="M15 5l-7 7 7 7"/>', T.prevCh));
    tools.appendChild(arrow(navNext, '<path d="M9 5l7 7-7 7"/>', T.nextCh));

    var readout = document.createElement('span');
    readout.className = 'reader-progress';
    readout.setAttribute('aria-live', 'off');
    tools.appendChild(readout);

    // 글자 크기 3단계
    var scales = [0.94, 1, 1.09];
    var idx = 1;
    try {
      var saved = parseFloat(localStorage.getItem(SCALE_KEY));
      if (!isNaN(saved)) {
        var found = scales.indexOf(saved);
        if (found !== -1) idx = found;
      }
    } catch (e) {}

    var stepper = document.createElement('div');
    stepper.className = 'font-stepper';
    stepper.setAttribute('role', 'group');
    stepper.setAttribute('aria-label', T.textSize);
    var minus = document.createElement('button');
    minus.type = 'button'; minus.textContent = 'A';
    minus.style.fontSize = '0.75rem';
    minus.setAttribute('aria-label', T.smaller);
    var plus = document.createElement('button');
    plus.type = 'button'; plus.textContent = 'A';
    plus.style.fontSize = '1rem';
    plus.setAttribute('aria-label', T.larger);
    stepper.appendChild(minus);
    stepper.appendChild(plus);

    function applyScale() {
      document.documentElement.style.setProperty('--reader-scale', String(scales[idx]));
      minus.setAttribute('aria-disabled', idx === 0 ? 'true' : 'false');
      plus.setAttribute('aria-disabled', idx === scales.length - 1 ? 'true' : 'false');
      try { localStorage.setItem(SCALE_KEY, String(scales[idx])); } catch (e) {}
    }
    minus.addEventListener('click', function () { if (idx > 0) { idx--; applyScale(); } });
    plus.addEventListener('click', function () { if (idx < scales.length - 1) { idx++; applyScale(); } });
    applyScale();
    tools.appendChild(stepper);

    // 검색 트리거 앞에 끼워 넣어 오른쪽 묶음의 첫 요소가 되게 한다
    var anchor = $('.search-trigger', header) || $('.dark-mode-toggle', header);
    if (anchor) header.insertBefore(tools, anchor);
    else header.appendChild(tools);

    // 남은 시간 계산의 기준: 장 머리의 「약 N분」
    var total = 0;
    var rt = $('.reading-time');
    if (rt) {
      var m = rt.textContent.match(/(\d+)\s*(?:분|min)/);
      if (m) total = parseInt(m[1], 10);
    }

    var raf = null;
    function update() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var pct = h > 0 ? Math.round((window.scrollY / h) * 100) : 0;
      pct = Math.min(100, Math.max(0, pct));
      var html = pct + '%';
      if (total) {
        var left = Math.max(0, Math.round(total * (1 - pct / 100)));
        html += '<span class="reader-left">' + (left ? T.minsLeft(left) : T.finished) + '</span>';
      }
      readout.innerHTML = html;
      raf = null;
    }
    window.addEventListener('scroll', function () {
      if (!raf) raf = window.requestAnimationFrame(update);
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ---------- 장 오프너 보강 (부 이름 · 몇 번째 장인지) ---------- */
  function initChapterMeta() {
    if (!isChapter()) return;

    var active = $('.sidebar .nav-link.active');
    var numEl = $('.chapter-header .chapter-number');
    var rt = $('.reading-time');

    // 읽는 시간을 안 적어둔 책(claude-100x 등)은 본문 글자수로 추정한다.
    // 500자/분 — 이 컬렉션이 손으로 적어둔 값들의 중간값에 맞췄다.
    var header = $('.chapter-header');
    if (!rt && header) {
      var article = $('.chapter-content article');
      var chars = article ? article.innerText.replace(/\s/g, '').length : 0;
      var mins = Math.max(1, Math.round(chars / 500));
      rt = document.createElement('span');
      rt.className = 'reading-time';
      rt.innerHTML = svgIcon('<circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/>') +
                     T.about(mins);
      header.appendChild(rt);
    }

    // 부 이름: 사이드바에서 현재 장 위쪽의 가장 가까운 .nav-part
    if (active && numEl && !$('.chapter-part', numEl)) {
      var node = active.closest('li');
      var part = '';
      while (node && node.previousElementSibling) {
        node = node.previousElementSibling;
        if (node.classList && node.classList.contains('nav-part')) {
          part = node.textContent.trim();
          break;
        }
      }
      if (part) {
        var span = document.createElement('span');
        span.className = 'chapter-part';
        // 「제5부: 자동화와 시각화」 → 「제5부 자동화와 시각화」
        span.textContent = part.replace(/\s*[:·]\s*/, ' ');
        numEl.appendChild(span);
      }
    }

    // 위치: 「19장 중 14번째」
    if (active && rt && !$('.chapter-position', rt)) {
      var links = $$('.sidebar .nav-link').filter(function (a) {
        return /^\d+\s*(?:장|\.)/.test(a.textContent.trim());
      });
      var here = links.indexOf(active);
      if (here !== -1 && links.length) {
        var pos = document.createElement('span');
        pos.className = 'chapter-position';
        pos.textContent = T.position(links.length, here + 1);
        rt.appendChild(pos);
      }
    }
  }

  /* ---------- 코드·프롬프트 복사 ---------- */
  function initCopy() {
    var article = $('.chapter-content article');
    if (!article) return;

    $$('pre, .file-tree', article).forEach(function (block) {
      if (block.parentElement && block.parentElement.classList.contains('code-wrap')) return;

      var wrap = document.createElement('div');
      wrap.className = 'code-wrap';
      if (!block.matches('pre')) wrap.classList.add('is-light');
      block.parentNode.insertBefore(wrap, block);
      wrap.appendChild(block);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-btn';
      var label = T.copy;
      btn.innerHTML = svgIcon('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/>') +
                      '<span>' + label + '</span>';
      btn.setAttribute('aria-label', T.copyAria);

      btn.addEventListener('click', function () {
        var text = block.innerText.replace(/ /g, ' ');

        function done(ok) {
          var span = $('span', btn);
          btn.classList.toggle('done', ok);
          if (span) span.textContent = ok ? T.copied : T.copyFail;
          setTimeout(function () {
            btn.classList.remove('done');
            if (span) span.textContent = label;
          }, ok ? 1600 : 2600);
        }

        // 구형 브라우저·비보안 컨텍스트·권한 거부 대비 폴백
        function legacyCopy() {
          var ta = document.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly', '');
          ta.style.cssText = 'position:fixed;top:0;left:-9999px;opacity:0';
          document.body.appendChild(ta);
          ta.select();
          ta.setSelectionRange(0, text.length);
          var ok = false;
          try { ok = document.execCommand('copy'); } catch (e) {}
          ta.remove();
          return ok;
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(
            function () { done(true); },
            function () { done(legacyCopy()); }   // 거부되면 폴백을 한 번 더 시도
          );
        } else {
          done(legacyCopy());
        }
      });

      wrap.appendChild(btn);
    });
  }

  /* ---------- 표 가로 스크롤 알림 ---------- */
  function initTables() {
    var article = $('.chapter-content article');
    if (!article) return;

    $$('table', article).forEach(function (table) {
      if (table.parentElement && table.parentElement.classList.contains('table-wrap')) return;

      // 구조: .table-wrap(고정) > .table-scroll(스크롤) > table
      // 페이드와 힌트는 스크롤되지 않아야 하므로 바깥 래퍼에 둔다.
      var wrap = document.createElement('div');
      wrap.className = 'table-wrap';
      var scroller = document.createElement('div');
      scroller.className = 'table-scroll';
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(scroller);
      scroller.appendChild(table);

      // 열이 많은 표는 좁은 화면에서 셀이 뭉개지는 대신 스크롤되게 한다.
      // 열 수에 비례한 최소 폭을 주되 40rem 에서 멈춘다.
      // 데스크톱 본문 칸(48rem)보다 좁으므로 넓은 화면에서는 아무 영향이 없다.
      var head = table.querySelector('thead tr') || table.querySelector('tr');
      var cols = head ? head.children.length : 0;
      if (cols >= 4) table.style.minWidth = Math.min(cols * 8.5, 40) + 'rem';

      var hint = document.createElement('p');
      hint.className = 'table-hint';
      hint.textContent = T.tableHint;
      hint.hidden = true;
      wrap.appendChild(hint);

      function sync() {
        var scrollable = scroller.scrollWidth > scroller.clientWidth + 2;
        wrap.classList.toggle('is-scrollable', scrollable);
        hint.hidden = !scrollable;
        wrap.classList.toggle('at-end', scroller.scrollLeft + scroller.clientWidth >= scroller.scrollWidth - 2);
      }
      scroller.addEventListener('scroll', sync, { passive: true });
      window.addEventListener('resize', sync);
      sync();
      // 웹폰트가 늦게 오면 폭이 바뀐다
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(sync);
    });
  }

  /* ---------- 읽던 위치 이어보기 ---------- */
  function initResume() {
    if (!isChapter()) return;

    var key = chapterKey();
    var store = {};
    try { store = JSON.parse(localStorage.getItem(POS_KEY) || '{}'); } catch (e) {}

    var saved = store[key];

    // 5% 이상 읽었고, 끝까지 읽은 게 아니고, 지금 위에 있을 때만 제안한다
    if (saved && saved.pct > 5 && saved.pct < 92 && window.scrollY < 40 && !location.hash) {
      var pill = document.createElement('div');
      pill.className = 'resume-pill';
      pill.setAttribute('role', 'status');
      var go = document.createElement('button');
      go.type = 'button';
      go.textContent = T.resume(saved.pct);
      var close = document.createElement('button');
      close.type = 'button';
      close.className = 'resume-close';
      close.textContent = T.startOver;
      close.setAttribute('aria-label', T.resumeClose);
      pill.appendChild(go);
      pill.appendChild(close);
      document.body.appendChild(pill);

      var timer = setTimeout(function () { pill.remove(); }, 9000);
      go.addEventListener('click', function () {
        clearTimeout(timer);
        var h = document.documentElement.scrollHeight - window.innerHeight;
        window.scrollTo({ top: h * (saved.pct / 100), behavior: 'smooth' });
        pill.remove();
      });
      close.addEventListener('click', function () {
        clearTimeout(timer);
        pill.remove();
      });
    }

    var writeTimer = null;
    function save() {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var pct = h > 0 ? Math.round((window.scrollY / h) * 100) : 0;
      store[key] = { pct: pct, at: Date.now() };
      // 오래된 항목 정리 — 30개까지만 들고 있는다
      var keys = Object.keys(store);
      if (keys.length > 30) {
        keys.sort(function (a, b) { return (store[a].at || 0) - (store[b].at || 0); });
        keys.slice(0, keys.length - 30).forEach(function (k) { delete store[k]; });
      }
      try { localStorage.setItem(POS_KEY, JSON.stringify(store)); } catch (e) {}
    }
    window.addEventListener('scroll', function () {
      if (writeTimer) clearTimeout(writeTimer);
      writeTimer = setTimeout(save, 400);
    }, { passive: true });
    window.addEventListener('pagehide', save);
  }

  /* ---------- 키보드로 장 이동 ---------- */
  function initKeyNav() {
    if (!isChapter()) return;
    document.addEventListener('keydown', function (e) {
      if (e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return;
      var pal = $('#palette');
      if (pal && pal.classList.contains('open')) return;
      var t = e.target;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;

      var sel = e.key === 'ArrowLeft' ? '.chapter-nav .back-to-toc'
              : e.key === 'ArrowRight' ? '.chapter-nav .next' : null;
      if (!sel) return;
      var link = $(sel);
      if (link && link.getAttribute('href')) {
        e.preventDefault();
        location.href = link.getAttribute('href');
      }
    });
  }

  function boot() {
    initTheme();
    initSidebar();
    initProgress();
    initAnchors();
    initRail();
    initScrollSpy();
    initPalette();
    initBrokenImages();
    initChapterMeta();
    initLangSwitch();
    initReaderTools();
    initCopy();
    initTables();
    initResume();
    initKeyNav();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

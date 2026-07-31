/**
 * 사회연대경제 e-book — Interactive JS
 */
(function () {
  'use strict';

  // === DOM References ===
  const progressBar        = document.getElementById('progressBar');
  const sidebar            = document.getElementById('sidebar');
  const sidebarOverlay     = document.getElementById('sidebarOverlay');
  const sidebarClose       = document.getElementById('sidebarClose');
  const hamburgerBtn       = document.getElementById('hamburgerBtn');
  const darkToggleHeader   = document.getElementById('darkModeToggleHeader');
  const darkToggleSidebar  = document.getElementById('darkModeToggleSidebar');
  const navLinks           = document.querySelectorAll('.nav-link');

  // === Dark Mode ===
  function getPreferredTheme() {
    const stored = localStorage.getItem('sse-theme');
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sse-theme', theme);
  }
  function toggleDarkMode() {
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(cur === 'dark' ? 'light' : 'dark');
  }
  setTheme(getPreferredTheme());
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem('sse-theme')) setTheme(e.matches ? 'dark' : 'light');
  });
  if (darkToggleHeader)  darkToggleHeader.addEventListener('click', toggleDarkMode);
  if (darkToggleSidebar) darkToggleSidebar.addEventListener('click', toggleDarkMode);

  // === Mobile Sidebar ===
  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
    if (hamburgerBtn)   hamburgerBtn.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
    if (hamburgerBtn)   hamburgerBtn.classList.remove('active');
    document.body.style.overflow = '';
  }
  if (hamburgerBtn)  hamburgerBtn.addEventListener('click', () => sidebar.classList.contains('open') ? closeSidebar() : openSidebar());
  if (sidebarClose)  sidebarClose.addEventListener('click', closeSidebar);
  if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });
  navLinks.forEach(l => l.addEventListener('click', () => { if (window.innerWidth <= 1024) closeSidebar(); }));

  // === Progress Bar ===
  function updateProgress() {
    if (!progressBar) return;
    const scrollTop  = window.scrollY;
    const docHeight  = document.documentElement.scrollHeight - window.innerHeight;
    progressBar.style.width = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) + '%' : '0%';
  }

  // === Active Nav ===
  function updateActiveNav() {
    if (!navLinks.length) return;
    const sections = [];
    navLinks.forEach(link => {
      const id = link.getAttribute('data-section');
      if (id) { const el = document.getElementById(id); if (el) sections.push({ id, el, link }); }
    });
    if (!sections.length) return;
    const scrollPos = window.scrollY + 150;
    let current = sections[0];
    sections.forEach(s => { if (s.el.offsetTop <= scrollPos) current = s; });
    navLinks.forEach(l => l.classList.remove('active'));
    if (current) current.link.classList.add('active');
  }

  // === Scroll (Throttled) ===
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => { updateProgress(); updateActiveNav(); ticking = false; });
      ticking = true;
    }
  }, { passive: true });
  updateProgress();
  updateActiveNav();

  // === Smooth Scroll ===
  document.addEventListener('click', e => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    const targetId = link.getAttribute('href').slice(1);
    if (!targetId) return;
    const target = document.getElementById(targetId);
    if (!target) return;
    e.preventDefault();
    const offset = window.innerWidth <= 1024 ? 70 : 20;
    window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - offset, behavior: 'smooth' });
    history.pushState(null, '', '#' + targetId);
  });

  // === Fade-in ===
  const fadeEls = document.querySelectorAll('.toc-part, .cta-section');
  fadeEls.forEach(el => el.classList.add('fade-in'));
  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); obs.unobserve(entry.target); } });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    fadeEls.forEach(el => obs.observe(el));
  } else {
    fadeEls.forEach(el => el.classList.add('visible'));
  }

  // === Resize ===
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (window.innerWidth > 1024) closeSidebar(); }, 150);
  });

  // === Quiz Logic ===
  document.querySelectorAll('.quiz-question').forEach(question => {
    const options  = question.querySelectorAll('.quiz-option');
    const feedback = question.querySelector('.quiz-feedback');
    let answered   = false;

    options.forEach(option => {
      option.addEventListener('click', () => {
        if (answered) return;
        answered = true;
        const isCorrect = option.dataset.correct === 'true';

        options.forEach(o => {
          if (o.dataset.correct === 'true') o.classList.add('correct');
          else if (o === option && !isCorrect) o.classList.add('wrong');
          o.style.cursor = 'default';
        });

        if (feedback) {
          feedback.classList.add('show');
          feedback.classList.add(isCorrect ? 'correct-fb' : 'wrong-fb');
          feedback.textContent = isCorrect
            ? '✅ ' + (feedback.dataset.correct || '정답입니다!')
            : '❌ ' + (feedback.dataset.wrong || '다시 생각해보세요.');
        }
      });
    });
  });

})();

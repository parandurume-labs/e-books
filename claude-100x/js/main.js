/**
 * Claude 100배 활용법 — E-Book Interactions
 */

(function () {
  'use strict';

  // ==========================================================================
  // DOM References
  // ==========================================================================
  const progressBar = document.getElementById('progressBar');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const sidebarClose = document.getElementById('sidebarClose');
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const darkModeToggleHeader = document.getElementById('darkModeToggleHeader');
  const darkModeToggleSidebar = document.getElementById('darkModeToggleSidebar');
  const navLinks = document.querySelectorAll('.nav-link');

  // ==========================================================================
  // Dark Mode
  // ==========================================================================
  function getPreferredTheme() {
    const stored = localStorage.getItem('theme');
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  function toggleDarkMode() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? 'light' : 'dark');
  }

  // Initialize theme
  setTheme(getPreferredTheme());

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      setTheme(e.matches ? 'dark' : 'light');
    }
  });

  // Toggle buttons
  if (darkModeToggleHeader) {
    darkModeToggleHeader.addEventListener('click', toggleDarkMode);
  }
  if (darkModeToggleSidebar) {
    darkModeToggleSidebar.addEventListener('click', toggleDarkMode);
  }

  // ==========================================================================
  // Mobile Sidebar
  // ==========================================================================
  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
    if (hamburgerBtn) hamburgerBtn.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
    if (hamburgerBtn) hamburgerBtn.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', () => {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (sidebarClose) {
    sidebarClose.addEventListener('click', closeSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // Close sidebar on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      closeSidebar();
    }
  });

  // Close sidebar when a nav link is clicked (mobile)
  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 1024) {
        closeSidebar();
      }
    });
  });

  // ==========================================================================
  // Reading Progress Bar
  // ==========================================================================
  function updateProgressBar() {
    if (!progressBar) return;
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (docHeight <= 0) {
      progressBar.style.width = '0%';
      return;
    }
    const progress = Math.min((scrollTop / docHeight) * 100, 100);
    progressBar.style.width = progress + '%';
  }

  // ==========================================================================
  // Active Section Tracking (Sidebar Highlight)
  // ==========================================================================
  function updateActiveNav() {
    if (!navLinks.length) return;

    const sections = [];
    navLinks.forEach((link) => {
      const sectionId = link.getAttribute('data-section');
      if (sectionId) {
        const el = document.getElementById(sectionId);
        if (el) {
          sections.push({ id: sectionId, el, link });
        }
      }
    });

    if (!sections.length) return;

    const scrollPos = window.scrollY + 150;
    let currentSection = sections[0];

    for (const section of sections) {
      if (section.el.offsetTop <= scrollPos) {
        currentSection = section;
      }
    }

    navLinks.forEach((link) => link.classList.remove('active'));
    if (currentSection) {
      currentSection.link.classList.add('active');

      // Scroll the active link into view within sidebar
      const sidebarContent = document.querySelector('.sidebar-content');
      if (sidebarContent && currentSection.link) {
        const linkRect = currentSection.link.getBoundingClientRect();
        const sidebarRect = sidebarContent.getBoundingClientRect();

        if (linkRect.top < sidebarRect.top || linkRect.bottom > sidebarRect.bottom) {
          currentSection.link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
      }
    }
  }

  // ==========================================================================
  // Scroll Event (Throttled)
  // ==========================================================================
  let ticking = false;

  function onScroll() {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        updateProgressBar();
        updateActiveNav();
        ticking = false;
      });
      ticking = true;
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });

  // Initial call
  updateProgressBar();
  updateActiveNav();

  // ==========================================================================
  // Smooth Scroll for Anchor Links
  // ==========================================================================
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;

    const targetId = link.getAttribute('href').slice(1);
    if (!targetId) return;

    const target = document.getElementById(targetId);
    if (!target) return;

    e.preventDefault();

    const offset = window.innerWidth <= 1024 ? 70 : 20;
    const targetPosition = target.getBoundingClientRect().top + window.scrollY - offset;

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth',
    });

    // Update URL without triggering scroll
    history.pushState(null, '', '#' + targetId);
  });

  // ==========================================================================
  // Fade-in on Scroll (Intersection Observer)
  // ==========================================================================
  function setupFadeIn() {
    const elements = document.querySelectorAll('.toc-part, .cta-section');

    if (!elements.length) return;

    // Add fade-in class
    elements.forEach((el) => el.classList.add('fade-in'));

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('visible');
              observer.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
      );

      elements.forEach((el) => observer.observe(el));
    } else {
      // Fallback: show all immediately
      elements.forEach((el) => el.classList.add('visible'));
    }
  }

  setupFadeIn();

  // ==========================================================================
  // Handle window resize (close mobile sidebar if resizing to desktop)
  // ==========================================================================
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (window.innerWidth > 1024) {
        closeSidebar();
      }
    }, 150);
  });
})();

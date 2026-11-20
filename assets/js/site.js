(function () {
  'use strict';

  var bar = document.getElementById('progress');
  var top = document.getElementById('backtop');

  function scrollTop() {
    return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  }

  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = scrollTop();
    if (bar) bar.style.width = (max > 0 ? y / max * 100 : 0) + '%';
    if (top) top.classList.toggle('show', y > 600);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (top) {
    top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  function initTocHighlight() {
    var tocLinks = [].slice.call(document.querySelectorAll('.toc a[href^="#"]'));
    var sections = tocLinks
      .map(function (a) { return document.querySelector(a.getAttribute('href')); })
      .filter(Boolean);

    if (!('IntersectionObserver' in window) || !sections.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        tocLinks.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });
    sections.forEach(function (section) { observer.observe(section); });
  }

  var navKey = location.protocol === 'file:'
    ? 'youchai-courses-file'
    : 'youchai-courses-http';
  var current = document.body.getAttribute('data-page');

  function readVisited() {
    try {
      return JSON.parse(window.localStorage.getItem(navKey) || '{}') || {};
    } catch (e) {
      return {};
    }
  }

  function writeVisited(data) {
    try {
      window.localStorage.setItem(navKey, JSON.stringify(data));
    } catch (e) {
      /* Private browsing or file:// restrictions are safe to ignore. */
    }
  }

  if (current) {
    var visited = readVisited();
    visited[current] = true;
    writeVisited(visited);
  }

  function initPage() {
    initTocHighlight();
    var visited = readVisited();
    [].forEach.call(document.querySelectorAll('[data-visited-marker]'), function (el) {
      var key = el.getAttribute('data-visited-marker');
      if (visited[key]) el.textContent = '已读';
    });
  }

  window.YOUCHAI_INIT_PAGE = initPage;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }
})();

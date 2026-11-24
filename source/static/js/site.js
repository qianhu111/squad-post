(function () {
  'use strict';

  var THEME_KEY = 'youchai-theme';
  var PROGRESS_KEY = 'youchai-courses-progress';
  var LEGACY_PROGRESS_KEYS = ['youchai-courses-file', 'youchai-courses-http'];

  function readStore(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function writeStore(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (e) {
      /* file:// and private mode may refuse storage; ignore safely. */
    }
  }

  function readVisited() {
    var raw = readStore(PROGRESS_KEY);
    if (raw === null) {
      for (var i = 0; i < LEGACY_PROGRESS_KEYS.length; i += 1) {
        raw = readStore(LEGACY_PROGRESS_KEYS[i]);
        if (raw !== null) {
          writeStore(PROGRESS_KEY, raw);
          break;
        }
      }
    }
    try {
      return JSON.parse(raw || '{}') || {};
    } catch (e) {
      return {};
    }
  }

  function writeVisited(data) {
    writeStore(PROGRESS_KEY, JSON.stringify(data));
  }

  function scrollTop() {
    return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  }

  var progress = document.getElementById('progress');
  var backtop = document.getElementById('backtop');
  var lessonProgress = document.getElementById('lesson-progress');
  var ticking = false;

  function paintProgress() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - doc.clientHeight;
    var y = scrollTop();
    if (progress) {
      progress.firstElementChild.style.width = (max > 0 ? y / max * 100 : 0) + '%';
    }
    if (backtop) {
      backtop.classList.toggle('show', y > 620);
    }
    if (lessonProgress) {
      var article = document.querySelector('.prose');
      if (article) {
        var rect = article.getBoundingClientRect();
        var total = Math.max(1, rect.height - window.innerHeight + 160);
        var done = Math.min(total, Math.max(0, -rect.top + 120));
        lessonProgress.firstElementChild.style.width = (done / total * 100) + '%';
      }
    }
    ticking = false;
  }

  function requestPaint() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(paintProgress);
    }
  }

  window.addEventListener('scroll', requestPaint, { passive: true });
  window.addEventListener('resize', requestPaint, { passive: true });
  paintProgress();

  if (backtop) {
    backtop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  var THEMES = ['light', 'dark', 'sepia', 'contrast'];
  var THEME_LABELS = { light: '浅色', dark: '深色', sepia: '纸张', contrast: '高对比' };

  function initTheme() {
    var button = document.getElementById('theme-toggle');
    if (!button) return;
    function paint() {
      var current = document.documentElement.getAttribute('data-theme') || 'light';
      var label = THEME_LABELS[current] || current;
      button.setAttribute('aria-label', '切换主题，当前' + label);
      button.title = '切换主题（当前' + label + '）';
    }
    paint();
    button.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-theme') || 'light';
      var index = THEMES.indexOf(current);
      var next = THEMES[(index < 0 ? 0 : index + 1) % THEMES.length];
      document.documentElement.setAttribute('data-theme', next);
      writeStore(THEME_KEY, next);
      paint();
    });
  }

  function initReadingMode() {
    var button = document.getElementById('reading-toggle');
    if (!button) return;
    var root = document.documentElement;
    function paint() {
      var on = root.getAttribute('data-reading') === '1';
      button.setAttribute('aria-pressed', on ? 'true' : 'false');
      button.setAttribute('aria-label', on ? '退出阅读模式' : '进入阅读模式');
      button.title = on ? '退出阅读模式' : '进入阅读模式';
    }
    paint();
    button.addEventListener('click', function () {
      var on = root.getAttribute('data-reading') === '1';
      if (on) root.removeAttribute('data-reading');
      else root.setAttribute('data-reading', '1');
      writeStore('youchai-reading', on ? '0' : '1');
      paint();
    });
  }

  function initFontScale() {
    var button = document.getElementById('font-toggle');
    if (!button) return;
    var root = document.documentElement;
    var scales = ['1', '1.08', '1.16'];
    function current() {
      var value = root.style.getPropertyValue('--reading-scale').trim();
      return scales.indexOf(value) >= 0 ? value : '1';
    }
    function paint() {
      var percent = Math.round(parseFloat(current()) * 100);
      button.setAttribute('aria-label', '切换正文字号，当前 ' + percent + '%');
      button.title = '切换正文字号（当前 ' + percent + '%）';
    }
    paint();
    button.addEventListener('click', function () {
      var index = scales.indexOf(current());
      var next = scales[(index + 1) % scales.length];
      root.style.setProperty('--reading-scale', next);
      writeStore('youchai-font', next);
      paint();
    });
  }

  function initSidebar() {
    var toggle = document.getElementById('sidebar-toggle');
    var inner = document.getElementById('sidebar-inner');
    if (!toggle || !inner) return;
    function setOpen(open) {
      inner.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      var label = toggle.querySelector('span');
      if (label) label.textContent = open ? '收起' : '展开';
    }
    toggle.addEventListener('click', function () {
      setOpen(!inner.classList.contains('open'));
    });
    toggle.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        setOpen(!inner.classList.contains('open'));
      }
    });
  }

  function initCopy() {
    var buttons = [].slice.call(document.querySelectorAll('[data-copy]'));
    if (!buttons.length) return;
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var text = button.getAttribute('data-copy') || '';
        var original = button.textContent;
        function done() {
          button.classList.add('copied');
          button.textContent = '已复制 ' + text;
          window.setTimeout(function () {
            button.classList.remove('copied');
            button.textContent = original;
          }, 1600);
        }
        function fallback() {
          try {
            var field = document.createElement('textarea');
            field.value = text;
            field.setAttribute('readonly', '');
            field.style.position = 'fixed';
            field.style.opacity = '0';
            document.body.appendChild(field);
            field.select();
            document.execCommand('copy');
            document.body.removeChild(field);
            done();
          } catch (e) {
            window.prompt('复制群号', text);
          }
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, fallback);
        } else {
          fallback();
        }
      });
    });
  }

  function initHomeResume() {
    if (!document.body || document.body.getAttribute('data-page') !== 'home') return;
    var link = document.getElementById('hero-primary');
    var data = window.YOUCHAI_COURSES;
    if (!link || !data || !data.courses || !data.courses.length) return;
    var visited = readVisited();
    var done = 0;
    var next = null;
    data.courses.forEach(function (course) {
      if (visited[course.id]) done += 1;
      else if (!next) next = course;
    });
    if (!done) return;
    if (next) {
      link.href = pageHref(next.file);
      link.textContent = '继续第 ' + String(next.num).padStart(2, '0') + ' 课';
      link.setAttribute('title', next.title);
    } else {
      link.href = pageHref('progress/');
      link.textContent = '查看学习进度';
      link.removeAttribute('title');
    }
  }

  function initVisited() {
    var marker = document.querySelector('[data-visited-marker]');
    if (!marker) return;
    var key = marker.getAttribute('data-key') || marker.getAttribute('data-visited-marker');
    paintVisited();

    marker.addEventListener('click', function () {
      var data = readVisited();
      if (data[key]) delete data[key];
      else data[key] = true;
      writeVisited(data);
      paintVisited();
    });

    function paintVisited() {
      var data = readVisited();
      var done = !!data[key];
      marker.classList.toggle('done', done);
      var text = marker.querySelector('.marker-text');
      if (text) text.textContent = done ? '已完成' : '标记完成';
      marker.setAttribute('aria-label', done ? '取消本课完成标记' : '标记本课完成');
      [].forEach.call(document.querySelectorAll('[data-visited-course]'), function (link) {
        if (link.getAttribute('data-visited-course') === key) {
          if (done) link.setAttribute('data-visited', 'true');
          else link.removeAttribute('data-visited');
        }
      });
    }
  }

  function initTocHighlight() {
    var links = [].slice.call(document.querySelectorAll('#local-toc a[href^="#"]'));
    if (!links.length || !('IntersectionObserver' in window)) return;
    var targets = links
      .map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); })
      .filter(Boolean);
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-18% 0px -70% 0px', threshold: 0 });
    targets.forEach(function (target) { observer.observe(target); });
  }

  var pageInitialized = false;

  function initFileLinks() {
    if (location.protocol !== 'file:') return;
    var links = document.querySelectorAll('a[href]');
    [].forEach.call(links, function (link) {
      var href = link.getAttribute('href');
      if (!href || /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(href)) return;
      if (href.charAt(0) === '/') {
        var siteRoot = (document.body && document.body.getAttribute('data-root')) || './';
        href = siteRoot + href.slice(1);
      }
      if (/\.[a-z0-9]+(?:[?#]|$)/i.test(href)) return;
      var hash = '';
      var hashIndex = href.indexOf('#');
      if (hashIndex >= 0) {
        hash = href.slice(hashIndex);
        href = href.slice(0, hashIndex);
      }
      var query = '';
      var queryIndex = href.indexOf('?');
      if (queryIndex >= 0) {
        query = href.slice(queryIndex);
        href = href.slice(0, queryIndex);
      }
      if (href.charAt(href.length - 1) === '/') href += 'index.html';
      else href += '.html';
      link.setAttribute('href', href + query + hash);
    });
  }

  function initNavDropdowns() {
    var groups = [].slice.call(document.querySelectorAll('.nav-group'));
    if (!groups.length) return;
    [].forEach.call(groups, function (group) {
      var btn = group.querySelector('.nav-group-btn');
      if (!btn) return;
      btn.addEventListener('click', function () {
        var open = group.classList.toggle('open');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.addEventListener('click', function (event) {
      [].forEach.call(groups, function (group) {
        if (!group.contains(event.target)) {
          group.classList.remove('open');
          var btn = group.querySelector('.nav-group-btn');
          if (btn) btn.setAttribute('aria-expanded', 'false');
        }
      });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      [].forEach.call(groups, function (group) {
        group.classList.remove('open');
        var btn = group.querySelector('.nav-group-btn');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  function initPage() {
    if (pageInitialized) return;
    pageInitialized = true;
    paintProgress();
    initVisited();
    initHomeResume();
    initTocHighlight();
    initFileLinks();
    initNavDropdowns();
  }

  window.YOUCHAI_INIT_PAGE = initPage;
  window.YOUCHAI_READ_VISITED = readVisited;
  window.YOUCHAI_WRITE_VISITED = writeVisited;
  window.YOUCHAI_PROGRESS_KEY = PROGRESS_KEY;

  var panel = document.getElementById('search-panel');
  var openBtn = document.getElementById('search-open');
  var closeBtn = document.getElementById('search-close');
  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var lastFocus = null;
  var SEARCH_INDEX_KEY = 'youchai-search-index';
  var searchIndexState = window.YOUCHAI_SEARCH_INDEX ? 'ready' : 'loading';

  function ensureSearchIndex(callback) {
    if (window.YOUCHAI_SEARCH_INDEX) {
      searchIndexState = 'ready';
      callback();
      return;
    }
    if (searchIndexState === 'error') {
      callback();
      return;
    }
    var root = (document.body && document.body.getAttribute('data-root')) || './';
    var src = root + 'assets/js/' + SEARCH_INDEX_KEY + '.js';
    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = function () {
      searchIndexState = 'ready';
      callback();
    };
    script.onerror = function () {
      searchIndexState = 'error';
      callback();
    };
    document.head.appendChild(script);
  }

  function rootPrefix() {
    return (document.body && document.body.getAttribute('data-root')) || './';
  }

  function pageHref(path) {
    var href = rootPrefix() + path;
    if (location.protocol === 'file:') {
      if (href.charAt(href.length - 1) === '/') return href + 'index.html';
      if (!/\.[a-z0-9]+$/i.test(href)) return href + '.html';
    }
    return href;
  }

  function indexItems() {
    return window.YOUCHAI_SEARCH_INDEX || [];
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  var EXCERPT_LENGTH = 86;

  function includesEvery(haystack, terms) {
    for (var i = 0; i < terms.length; i += 1) {
      if (haystack.indexOf(terms[i]) < 0) return false;
    }
    return true;
  }

  function highlight(safeText, terms) {
    var out = safeText;
    for (var i = 0; i < terms.length; i += 1) {
      var term = escapeHtml(terms[i]);
      if (term) out = out.split(term).join('<mark>' + term + '</mark>');
    }
    return out;
  }

  function excerpt(text, terms) {
    var lower = text.toLowerCase();
    var at = -1;
    for (var i = 0; i < terms.length; i += 1) {
      var found = lower.indexOf(terms[i]);
      if (found >= 0 && (at < 0 || found < at)) at = found;
    }
    var start = at > 32 ? at - 32 : 0;
    var slice = text.slice(start, start + EXCERPT_LENGTH);
    if (start > 0) slice = '…' + slice;
    if (start + EXCERPT_LENGTH < text.length) slice += '…';
    return slice;
  }

  function searchItems(terms) {
    var hits = [];
    indexItems().forEach(function (item) {
      var head = [
        String(item.num || ''),
        '第' + String(item.num || '') + '课',
        item.title || '',
        item.subtitle || '',
        item.stage || '',
        (item.keywords || []).join(' '),
        (item.tags || []).join(' '),
        (item.tags || []).map(function (tag) { return '#' + tag; }).join(' ')
      ].join(' ').toLowerCase();
      var headHit = includesEvery(head, terms);
      var sections = item.sections || [];
      var matchedSections = [];
      for (var i = 0; i < sections.length; i += 1) {
        var section = sections[i];
        var title = String(section.title || '').toLowerCase();
        var text = String(section.text || '').toLowerCase();
        var inTitle = includesEvery(title, terms);
        var inText = !!text && includesEvery(text, terms);
        if (inTitle || inText) {
          matchedSections.push({
            id: section.id,
            title: section.title,
            snippet: inText && !inTitle ? excerpt(section.text, terms) : '',
            rank: inTitle ? 1 : 2,
          });
        }
      }
      if (headHit) {
        hits.push({
          num: item.num,
          path: item.path,
          title: item.title,
          stage: item.stage,
          subtitle: item.subtitle,
          section: null,
          rank: 0,
        });
      } else if (matchedSections.length) {
        hits.push({
          num: item.num,
          path: item.path,
          title: item.title,
          stage: item.stage,
          subtitle: item.subtitle,
          section: matchedSections[0],
          rank: matchedSections[0].rank,
        });
      }
    });
    hits.sort(function (a, b) {
      if (a.rank !== b.rank) return a.rank - b.rank;
      return a.num - b.num;
    });
    return hits.slice(0, 12);
  }

  function renderResults(query) {
    if (!results) return;
    var q = query.trim().toLowerCase();
    if (!q) {
      results.innerHTML = '<div class="search-hint">输入课次、标题、小节、正文或关键词开始搜索。</div>';
      return;
    }
    if (!window.YOUCHAI_SEARCH_INDEX) {
      if (searchIndexState === 'error') {
        results.innerHTML = '<div class="search-empty">搜索索引加载失败，请刷新页面重试。</div>';
      } else {
        results.innerHTML = '<div class="search-hint">正在加载搜索索引…</div>';
        ensureSearchIndex(function () { renderResults(query); });
      }
      return;
    }
    var terms = q.split(/\s+/);
    var matched = searchItems(terms);

    if (!matched.length) {
      results.innerHTML = '<div class="search-empty">没有找到匹配内容。换个关键词，或打开课程总览按课次找。</div>';
      return;
    }

    results.innerHTML = matched.map(function (item) {
      var href = pageHref(item.path) + (item.section ? '#' + item.section.id : '');
      var detail = item.section ? '§ ' + item.section.title : item.subtitle;
      var snippet = item.section && item.section.snippet
        ? '<em class="search-snippet">' + highlight(escapeHtml(item.section.snippet), terms) + '</em>'
        : '';
      return '<a class="search-result" href="' + escapeHtml(href) + '">' +
        '<strong>' + String(item.num).padStart(2, '0') + ' · ' + escapeHtml(item.title) + '</strong>' +
        '<small>' + escapeHtml(item.stage) + ' · ' + escapeHtml(detail) + '</small>' +
        snippet + '</a>';
    }).join('');
  }

  function openSearch() {
    if (!panel) return;
    lastFocus = document.activeElement;
    panel.hidden = false;
    if (input) {
      input.value = '';
      renderResults('');
      input.focus();
    }
    if (!window.YOUCHAI_SEARCH_INDEX && searchIndexState !== 'error') {
      ensureSearchIndex(function () { if (input && input.value.trim()) renderResults(input.value); });
    }
  }

  function closeSearch() {
    if (!panel || panel.hidden) return;
    panel.hidden = true;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  if (openBtn) openBtn.addEventListener('click', openSearch);
  if (closeBtn) closeBtn.addEventListener('click', closeSearch);
  if (panel) {
    [].forEach.call(panel.querySelectorAll('[data-search-close]'), function (el) {
      el.addEventListener('click', closeSearch);
    });
  }
  if (input) input.addEventListener('input', function () { renderResults(input.value); });
  document.addEventListener('keydown', function (event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openSearch();
    } else if (event.key === 'Escape') {
      closeSearch();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }

  initTheme();
  initSidebar();
  initCopy();
  initReadingMode();
  initFontScale();
})();

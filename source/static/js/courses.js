(function () {
  'use strict';

  var data = window.YOUCHAI_COURSES || { stages: [], courses: [] };
  var courses = data.courses || [];
  var stages = data.stages || [];
  var currentId = document.body ? document.body.getAttribute('data-page') : '';
  var current = null;
  var currentIndex = -1;
  var rootPrefix = (document.body && document.body.getAttribute('data-root')) || '../../';

  courses.forEach(function (course, index) {
    if (course.id === currentId) {
      current = course;
      currentIndex = index;
    }
  });

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function pad(num) {
    return String(num).padStart(2, '0');
  }

  function pageHref(path) {
    var href = rootPrefix + path;
    if (location.protocol === 'file:') {
      if (href.charAt(href.length - 1) === '/') return href + 'index.html';
      if (!/\.[a-z0-9]+$/i.test(href)) return href + '.html';
    }
    return href;
  }

  function stageName(stageId) {
    for (var i = 0; i < stages.length; i += 1) {
      if (stages[i].id === stageId) return stages[i];
    }
    return null;
  }

  function buildLadder() {
    var root = document.getElementById('course-toc');
    if (!root || !current) return;
    stages.forEach(function (stage) {
      var section = el('div', 'ladder-stage');
      var head = el('div', 'ladder-head');
      head.appendChild(el('span', 'ladder-num', stage.num));
      head.appendChild(el('span', 'ladder-name', stage.name));
      section.appendChild(head);
      var links = el('div', 'ladder-links');
      courses.forEach(function (course) {
        if (course.stage !== stage.id) return;
        var link = el('a', 'ladder-link', pad(course.num) + ' · ' + course.title);
        link.href = pageHref(course.file);
        link.setAttribute('aria-label', '第 ' + course.num + ' 课 ' + course.title);
        link.setAttribute('data-visited-course', course.id);
        if (course.id === current.id) {
          link.classList.add('active');
          link.setAttribute('aria-current', 'page');
        }
        links.appendChild(link);
      });
      section.appendChild(links);
      root.appendChild(section);
    });
  }

  function buildLocalToc() {
    var root = document.getElementById('local-toc');
    if (!root) return;
    var headings = [].slice.call(document.querySelectorAll('.prose section[id] > h2, .prose section[id] > h3'));
    if (!headings.length) return;
    var title = el('div', 'local-title', '本课小节');
    var list = el('div', 'local-links');
    headings.forEach(function (heading) {
      var clone = heading.cloneNode(true);
      var anchor = clone.querySelector('.heading-anchor');
      if (anchor) anchor.parentNode.removeChild(anchor);
      var link = el('a', 'local-link', clone.textContent.trim());
      if (heading.tagName === 'H3') link.classList.add('indent');
      link.href = '#' + heading.parentNode.id;
      list.appendChild(link);
    });
    root.appendChild(title);
    root.appendChild(list);
  }

  function setNav(id, course, direction) {
    var node = document.getElementById(id);
    if (!node) return;
    if (!course) return;
    var stage = stageName(course.stage);
    node.classList.remove('disabled');
    node.href = pageHref(course.file);
    node.setAttribute('aria-label', direction + '：第 ' + course.num + ' 课 ' + course.title);
    var label = node.querySelector('span');
    var title = node.querySelector('strong');
    if (label) {
      label.textContent = (direction === '上一课' ? '← 上一课 · ' : '下一课 · ') + pad(course.num) +
        (direction === '上一课' ? '' : ' →') + (stage ? ' · ' + stage.name : '');
    }
    if (title) title.textContent = course.title;
  }

  function buildLessonNav() {
    if (!current || currentIndex < 0) return;
    setNav('prev-lesson', courses[currentIndex - 1], '上一课');
    setNav('next-lesson', courses[currentIndex + 1], '下一课');
  }

  buildLadder();
  buildLocalToc();
  buildLessonNav();

  if (typeof window.YOUCHAI_INIT_PAGE === 'function') {
    window.YOUCHAI_INIT_PAGE();
  }
})();

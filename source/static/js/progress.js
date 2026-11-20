(function () {
  'use strict';

  var data = window.YOUCHAI_COURSES || { stages: [], courses: [] };
  var stages = data.stages || [];
  var courses = data.courses || [];
  var KEY = window.YOUCHAI_PROGRESS_KEY || 'youchai-courses-progress';
  var storageOk = true;

  function testStorage() {
    try {
      var probe = '__youchai_probe__';
      window.localStorage.setItem(probe, '1');
      window.localStorage.removeItem(probe);
      return true;
    } catch (e) {
      return false;
    }
  }

  function readVisited() {
    if (typeof window.YOUCHAI_READ_VISITED === 'function') {
      return window.YOUCHAI_READ_VISITED() || {};
    }
    try {
      return JSON.parse(window.localStorage.getItem(KEY) || '{}') || {};
    } catch (e) {
      return {};
    }
  }

  function writeVisited(value) {
    if (typeof window.YOUCHAI_WRITE_VISITED === 'function') {
      window.YOUCHAI_WRITE_VISITED(value);
    } else {
      try {
        window.localStorage.setItem(KEY, JSON.stringify(value));
      } catch (e) {
        storageOk = false;
      }
    }
  }

  function pad(num) {
    return String(num).padStart(2, '0');
  }

  function pageHref(path) {
    var root = (document.body && document.body.getAttribute('data-root')) || '../';
    var href = root + path;
    if (location.protocol === 'file:') {
      if (href.charAt(href.length - 1) === '/') return href + 'index.html';
      if (!/\.[a-z0-9]+$/i.test(href)) return href + '.html';
    }
    return href;
  }

  function coursesFor(stageId) {
    return courses.filter(function (course) {
      return course.stage === stageId;
    });
  }

  function setWarning(show) {
    var warning = document.getElementById('progress-warning');
    if (warning) warning.hidden = !show;
    var reset = document.getElementById('progress-reset');
    if (reset) reset.disabled = show;
    [].forEach.call(document.querySelectorAll('[data-progress-toggle]'), function (button) {
      button.disabled = show;
    });
  }

  function paint() {
    var visited = readVisited();
    var total = courses.length;
    var done = 0;
    var next = null;

    courses.forEach(function (course) {
      if (visited[course.id]) done += 1;
      else if (!next) next = course;
    });

    var percent = total ? Math.round(done / total * 100) : 0;
    var ring = document.getElementById('progress-ring');
    var percentEl = document.getElementById('progress-percent');
    var countEl = document.getElementById('progress-count');
    var barEl = document.getElementById('progress-bar-fill');
    var nextEl = document.getElementById('progress-next');
    var continueBtn = document.getElementById('progress-continue');

    if (ring) ring.style.setProperty('--p', percent + '%');
    if (percentEl) percentEl.textContent = percent + '%';
    if (countEl) countEl.textContent = done + ' / ' + total + ' 课';
    if (barEl) barEl.style.width = percent + '%';

    if (nextEl) {
      if (next) {
        nextEl.textContent = '下一课：第 ' + pad(next.num) + ' 课 · ' + next.title;
      } else {
        nextEl.textContent = total + ' 课已全部标记完成，去做能力自检 Ⅱ。';
      }
    }
    if (continueBtn) {
      if (next) {
        continueBtn.href = pageHref(next.file);
        continueBtn.textContent = '继续第 ' + pad(next.num) + ' 课';
      } else {
        continueBtn.href = pageHref('quiz/advanced');
        continueBtn.textContent = '去做能力自检 Ⅱ';
      }
    }

    [].forEach.call(document.querySelectorAll('[data-progress-course]'), function (row) {
      var id = row.getAttribute('data-progress-course');
      var isDone = !!visited[id];
      var button = row.querySelector('[data-progress-toggle]');
      var text = button ? button.querySelector('.check-text') : null;
      row.classList.toggle('done', isDone);
      if (button) {
        button.setAttribute('aria-pressed', isDone ? 'true' : 'false');
        var course = null;
        for (var i = 0; i < courses.length; i += 1) {
          if (courses[i].id === id) {
            course = courses[i];
            break;
          }
        }
        var num = course ? pad(course.num) : '';
        button.setAttribute('aria-label', isDone ? '取消第 ' + num + ' 课的完成标记' : '标记第 ' + num + ' 课完成');
        if (text) text.textContent = isDone ? '已完成' : '标记完成';
      }
    });

    stages.forEach(function (stage) {
      var list = coursesFor(stage.id);
      var stageDone = 0;
      list.forEach(function (course) {
        if (visited[course.id]) stageDone += 1;
      });
      var count = document.querySelector('[data-stage-count="' + stage.id + '"]');
      var bar = document.querySelector('[data-stage-bar="' + stage.id + '"]');
      if (count) count.textContent = stageDone + ' / ' + list.length;
      if (bar) bar.style.width = (list.length ? stageDone / list.length * 100 : 0) + '%';
    });

    setWarning(!storageOk);
  }

  document.addEventListener('click', function (event) {
    var node = event.target;
    while (node && node !== document) {
      if (node.getAttribute && node.hasAttribute('data-progress-toggle')) break;
      node = node.parentNode;
    }
    if (!node || node === document || !storageOk) return;
    var id = node.getAttribute('data-progress-toggle');
    var visited = readVisited();
    if (visited[id]) delete visited[id];
    else visited[id] = true;
    writeVisited(visited);
    paint();
  });

  var reset = document.getElementById('progress-reset');
  if (reset) {
    reset.addEventListener('click', function () {
      if (!storageOk) return;
      if (!window.confirm('清空全部 36 课的完成标记？这个操作不能撤销。')) return;
      writeVisited({});
      paint();
    });
  }

  window.addEventListener('storage', function (event) {
    if (!event.key || event.key === KEY) paint();
  });

  storageOk = testStorage();
  paint();
})();

window.YOUCHAI_COURSES = {
  beginner: [
    { id: 'b01', file: '01-first-match.html', title: '第一局怎么打', subtitle: '目标、基本流程与常见死法' },
    { id: 'b02', file: '02-controls-interface.html', title: '界面、键位与地图', subtitle: '把常用键练成条件反射' },
    { id: 'b03', file: '03-roles-and-survival.html', title: '兵种与生存', subtitle: '步枪兵、医疗兵和保命原则' },
    { id: 'b04', file: '04-read-battlefield.html', title: '读懂战场', subtitle: '威胁范围、锋线腰线与四类区域' },
    { id: 'b05', file: '05-sound-observation-reporting.html', title: '听声、观察与报点', subtitle: '把看到的东西说成可执行信息' },
    { id: 'b06', file: '06-spawns-fob-hab.html', title: '复活点入门', subtitle: '主基、FOB、HAB 与队包' },
    { id: 'b07', file: '07-tickets-supplies.html', title: '票数、补给与占领', subtitle: '看懂队伍为什么突然回防' },
    { id: 'b08', file: '08-teamplay-basics.html', title: '基础协同', subtitle: '跟随、掩护、补枪与救人的顺序' }
  ],
  advanced: [
    { id: 'a01', file: '01-squad-leader.html', title: '小队长职责', subtitle: '带队节奏与队伍类型' },
    { id: 'a02', file: '02-fireteams-formations.html', title: '火力组与队形', subtitle: '三三制、1-2/2-1 与接敌流程' },
    { id: 'a03', file: '03-defense-area-control.html', title: '防御与区域控制', subtitle: '分方向、分兵力、分层防守' },
    { id: 'a04', file: '04-fob-selection-logistics.html', title: 'FOB 选址与后勤', subtitle: '工事、补给和撤退路线' },
    { id: 'a05', file: '05-ticket-math.html', title: '票数账本', subtitle: '把每个决定换算成票' },
    { id: 'a06', file: '06-combined-arms.html', title: '兵种协同与反载具', subtitle: '步载协同、筒子、机枪与特射' },
    { id: 'a07', file: '07-mortar-spotting.html', title: '迫击炮引导', subtitle: '刻度、修正与通信流程' },
    { id: 'a08', file: '08-urban-warfare.html', title: '城市作战与巷战', subtitle: '房间、楼层、街道与交叉火力' },
    { id: 'a09', file: '09-terrain-analysis.html', title: '地形与地图分析', subtitle: '林地、荒漠、混合地形' },
    { id: 'a10', file: '10-review-and-training.html', title: '复盘与训练', subtitle: '训练路线、模板和常见指挥错误' }
  ]
};

(function () {
  function currentKey() {
    return document.body.getAttribute('data-page') || '';
  }

  function routeFor(key) {
    if (key.indexOf('b') === 0) return { prefix: '', list: window.YOUCHAI_COURSES.beginner };
    if (key.indexOf('a') === 0) return { prefix: '', list: window.YOUCHAI_COURSES.advanced };
    return null;
  }

  function build() {
    var key = currentKey();
    var route = routeFor(key);
    if (!route) return;

    var toc = document.getElementById('course-toc');
    if (toc) {
      var index = route.list.findIndex(function (item) { return item.id === key; });
      var html = '<h2>课程目录</h2>';
      html += '<div class="toc-group">' + (key[0] === 'b' ? '新人线' : '进阶线') + '</div><ol>';
      route.list.forEach(function (item, i) {
        var active = item.id === key ? ' class="active"' : '';
        var mark = i === index ? ' data-visited-marker="' + item.id + '"' : '';
        html += '<li><a href="' + route.prefix + item.file + '"' + active + mark + '>' +
          (i + 1) + '. ' + item.title + '</a></li>';
      });
      html += '</ol><div class="toc-group">本课小节</div><ol id="local-toc"></ol>';
      toc.innerHTML = html;
      if (window.YOUCHAI_INIT_PAGE) {
        window.YOUCHAI_INIT_PAGE();
      }
    }

    var local = document.getElementById('local-toc');
    if (local) {
      [].forEach.call(document.querySelectorAll('.content section[id] h2'), function (heading) {
        var section = heading.parentNode;
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.setAttribute('href', '#' + section.id);
        a.className = 'lvl2';
        a.textContent = heading.textContent;
        li.appendChild(a);
        local.appendChild(li);
      });
    }

    var prev = document.getElementById('prev-lesson');
    var next = document.getElementById('next-lesson');
    var i = route.list.findIndex(function (item) { return item.id === key; });
    if (prev && i > 0) {
      var p = route.list[i - 1];
      prev.href = route.prefix + p.file;
      prev.innerHTML = '<span>← 上一课</span><strong>' + p.title + '</strong>';
    } else if (prev) {
      prev.style.visibility = 'hidden';
    }
    if (next && i > -1 && i < route.list.length - 1) {
      var n = route.list[i + 1];
      next.href = route.prefix + n.file;
      next.innerHTML = '<span>下一课 →</span><strong>' + n.title + '</strong>';
    } else if (next) {
      next.style.visibility = 'hidden';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();

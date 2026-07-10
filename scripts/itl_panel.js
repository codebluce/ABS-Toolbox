/* ═══ 投资台账面板逻辑（vanilla JS · 命名空间 ITL · 读 window.ITL_DATA）═══ */
(function () {
  var DATA = window.ITL_DATA || [];
  // 六个筛选字段统一为下拉选框：pick=true 的点击即展开全量选项，其余支持关键词联想
  var SEL = [
    { key: 'asset', label: '资产类型', col: 'D', pick: true },
    { key: 'layer', label: '分层情况', col: 'P', pick: true },
    { key: 'mgr', label: '计划管理人', col: 'G' },
    { key: 'underwriter', label: '联席承销商', col: 'H' },
    { key: 'custodian', label: '托管行', col: 'I' },
    { key: 'inst', label: '认购机构', col: 'U' }
  ];
  // 评级 rating 无筛选 UI，但保留在状态里：仍是分组/透视维度，智能问答可通过 applySpec 按评级过滤
  var DIMS = [
    { key: 'inst', label: '认购机构' },
    { key: 'mgr', label: '计划管理人' },
    { key: 'underwriter', label: '联席承销商' },
    { key: 'custodian', label: '托管行' },
    { key: 'asset', label: '资产类型' },
    { key: 'rating', label: '评级' },
    { key: 'layer', label: '分层情况' }
  ];

  var st = {
    selKw: { asset: [], layer: [], rating: [], mgr: [], underwriter: [], custodian: [], inst: [] },
    activeKw: null,
    dateFrom: '', dateTo: '', shareMin: '', shareMax: '',
    view: 'group', groupDim: 'inst', sortKey: 'share', sortDir: 'desc',
    pivotRow: 'inst', pivotCol: 'asset'
  };

  // ── helpers ──
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function fmtShare(v) { return (v == null ? 0 : v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function fmtPct(v) { return (v == null || isNaN(v)) ? '—' : (v * 100).toFixed(2) + '%'; }
  function fmtInt(v) { return v.toLocaleString('en-US'); }
  function dimLabel(k) { for (var i = 0; i < DIMS.length; i++) if (DIMS[i].key === k) return DIMS[i].label; return k; }
  function distinctCounts(key) { var m = new Map(); for (var i = 0; i < DATA.length; i++) { var v = DATA[i][key]; if (v == null || v === '') continue; m.set(v, (m.get(v) || 0) + 1); } return m; }

  function filtered() {
    return DATA.filter(function (r) {
      for (var k in st.selKw) { var s = st.selKw[k]; if (s.length && s.indexOf(r[k]) < 0) return false; }
      if (st.dateFrom) { if (!r.date || r.date < st.dateFrom) return false; }
      if (st.dateTo) { if (!r.date || r.date > st.dateTo) return false; }
      if (st.shareMin !== '') { if (r.share == null || r.share < +st.shareMin) return false; }
      if (st.shareMax !== '') { if (r.share == null || r.share > +st.shareMax) return false; }
      return true;
    });
  }

  function activeCount() {
    var n = 0;
    for (var k in st.selKw) n += st.selKw[k].length ? 1 : 0;
    if (st.dateFrom || st.dateTo) n += 1;
    if (st.shareMin !== '' || st.shareMax !== '') n += 1;
    return n;
  }

  function suggestions(field) {
    var q = (getInput(field).value || '').trim();
    var sel = st.selKw[field];
    var counts = distinctCounts(field);
    var arr = [];
    counts.forEach(function (c, v) { if (sel.indexOf(v) < 0 && (!q || v.indexOf(q) >= 0)) arr.push([v, c]); });
    arr.sort(function (a, b) { return b[1] - a[1]; });
    return arr.slice(0, 20);
  }

  function groupData() {
    var recs = filtered(), dim = st.groupDim, m = new Map(), total = 0;
    recs.forEach(function (r) {
      var k = r[dim] || '（未标注）';
      if (!m.has(k)) m.set(k, { key: k, count: 0, share: 0, cs: 0, cn: 0, ss: 0, sn: 0 });
      var g = m.get(k); g.count++;
      if (r.share != null) { g.share += r.share; total += r.share; }
      if (r.cost != null) { g.cs += r.cost; g.cn++; }
      if (r.spread != null) { g.ss += r.spread; g.sn++; }
    });
    var arr = [];
    m.forEach(function (g) { arr.push({ key: g.key, count: g.count, share: g.share, pct: total ? g.share / total : 0, avgCost: g.cn ? g.cs / g.cn : null, avgSpread: g.sn ? g.ss / g.sn : null }); });
    var dir = st.sortDir === 'desc' ? -1 : 1, sk = st.sortKey;
    arr.sort(function (a, b) {
      if (sk === 'key') return dir * String(a.key).localeCompare(String(b.key), 'zh');
      var av = a[sk] == null ? -Infinity : a[sk], bv = b[sk] == null ? -Infinity : b[sk];
      return dir * (av - bv);
    });
    return arr;
  }

  function pivotData() {
    var recs = filtered(), rk = st.pivotRow, ck = st.pivotCol;
    var rowShare = new Map(), colShare = new Map();
    recs.forEach(function (r) {
      var s = r.share || 0, rv = r[rk] || '（未标注）', cv = r[ck] || '（未标注）';
      rowShare.set(rv, (rowShare.get(rv) || 0) + s); colShare.set(cv, (colShare.get(cv) || 0) + s);
    });
    function top(m, n) { var a = []; m.forEach(function (v, k) { a.push([k, v]); }); a.sort(function (x, y) { return y[1] - x[1]; }); return a.slice(0, n).map(function (e) { return e[0]; }); }
    var topRows = top(rowShare, 14), topCols = top(colShare, 9);
    var rowSet = new Set(topRows), colSet = new Set(topCols), cell = {}, hasOR = false, hasOC = false;
    recs.forEach(function (r) {
      var rr = rowSet.has(r[rk] || '（未标注）') ? (r[rk] || '（未标注）') : '其他';
      var cc = colSet.has(r[ck] || '（未标注）') ? (r[ck] || '（未标注）') : '其他';
      if (rr === '其他') hasOR = true; if (cc === '其他') hasOC = true;
      var key = rr + '\u0001' + cc; cell[key] = (cell[key] || 0) + (r.share || 0);
    });
    var rowLabels = topRows.slice(); if (hasOR) rowLabels.push('其他');
    var colLabels = topCols.slice(); if (hasOC) colLabels.push('其他');
    var colTotals = colLabels.map(function () { return 0; }), grand = 0;
    var rows = rowLabels.map(function (rl) {
      var cells = colLabels.map(function (cl, i) { var v = cell[rl + '\u0001' + cl] || 0; colTotals[i] += v; return v; });
      var total = cells.reduce(function (a, c) { return a + c; }, 0); grand += total;
      return { label: rl, cells: cells, total: total };
    });
    return { rows: rows, cols: colLabels, colTotals: colTotals, grand: grand };
  }

  // ── DOM refs ──
  var root, inputs = {};
  function getInput(f) { return inputs[f]; }

  function renderKw(field) {
    // dropdown
    var drop = document.getElementById('itl-drop-' + field);
    if (st.activeKw === field) {
      var sug = suggestions(field);
      drop.innerHTML = sug.length
        ? sug.map(function (e) { return '<div class="itl-drop-item" data-act="add" data-field="' + field + '" data-val="' + esc(e[0]) + '"><span>' + esc(e[0]) + '</span><span class="c">' + e[1] + ' 条</span></div>'; }).join('')
        : '<div class="itl-drop-empty">无匹配项</div>';
      drop.classList.add('show');
    } else { drop.classList.remove('show'); }
    // selected chips
    document.getElementById('itl-chips-sel-' + field).innerHTML = st.selKw[field].map(function (v) {
      return '<span class="itl-selchip">' + esc(v) + '<span class="x" data-act="rmkw" data-field="' + field + '" data-val="' + esc(v) + '">×</span></span>';
    }).join('');
  }
  function renderAllKw() { SEL.forEach(function (f) { renderKw(f.key); }); }

  function renderBadge() { document.getElementById('itl-badge').textContent = activeCount() + ' 项生效'; }

  function renderCards() {
    var recs = filtered();
    var totalAll = DATA.reduce(function (a, r) { return a + (r.share || 0); }, 0);
    var shareSum = recs.reduce(function (a, r) { return a + (r.share || 0); }, 0);
    var projSet = new Set(); recs.forEach(function (r) { if (r.proj) projSet.add(r.proj); });
    var ca = recs.filter(function (r) { return r.cost != null; }); var avgCost = ca.length ? ca.reduce(function (a, r) { return a + r.cost; }, 0) / ca.length : null;
    var sa = recs.filter(function (r) { return r.spread != null; }); var avgSpread = sa.length ? sa.reduce(function (a, r) { return a + r.spread; }, 0) / sa.length : null;
    var cards = [
      { l: '记录数', v: fmtInt(recs.length), u: '条', s: '全量 ' + fmtInt(DATA.length) + ' 条', c: '#0d1b2e' },
      { l: '认购份额合计', v: fmtShare(shareSum), u: '亿', s: totalAll ? '占全量 ' + (shareSum / totalAll * 100).toFixed(1) + '%' : '', c: '#1a3a5c' },
      { l: '覆盖项目数', v: fmtInt(projSet.size), u: '个', s: '不同项目名称', c: '#0d1b2e' },
      { l: '平均成本', v: fmtPct(avgCost), u: '', s: ca.length + ' 条含成本', c: '#0d1b2e' },
      { l: '平均利差', v: fmtPct(avgSpread), u: '', s: '成本 − 国股CD', c: '#0d1b2e' }
    ];
    document.getElementById('itl-cards').innerHTML = cards.map(function (c) {
      return '<div class="itl-card-box itl-metric"><div class="m-label">' + c.l + '</div><div class="m-value" style="color:' + c.c + '">' + c.v + '<span class="u">' + c.u + '</span></div><div class="m-sub">' + c.s + '</div></div>';
    }).join('');
  }

  function arrow(k) { return st.sortKey === k ? (st.sortDir === 'desc' ? ' ▾' : ' ▴') : ''; }

  function renderResult() {
    // view tabs
    document.querySelectorAll('#itl-vtabs .itl-vtab').forEach(function (b) { b.classList.toggle('on', b.dataset.view === st.view); });
    var pane = document.getElementById('itl-pane');
    if (st.view === 'group') pane.innerHTML = renderGroup();
    else if (st.view === 'pivot') pane.innerHTML = renderPivot();
    else pane.innerHTML = renderDetail();
  }

  function dimButtons(act, cur) {
    return DIMS.map(function (d) { return '<button class="itl-dim' + (cur === d.key ? ' on' : '') + '" data-act="' + act + '" data-key="' + d.key + '">' + d.label + '</button>'; }).join('');
  }

  function renderGroup() {
    var gd = groupData(), max = Math.max.apply(null, gd.map(function (g) { return g.share; }).concat([0.0001]));
    var rows = gd.slice(0, 200).map(function (g, i) {
      return '<tr><td class="itl-num" style="text-align:right;padding:8px 10px;color:#a3adba">' + (i + 1) + '</td>'
        + '<td style="text-align:left;padding:8px 10px;font-weight:600;color:#0d1b2e">' + esc(g.key) + '</td>'
        + '<td class="itl-num" style="text-align:right;padding:8px 10px;color:#556">' + fmtInt(g.count) + '</td>'
        + '<td class="itl-num itl-accent" style="text-align:right;padding:8px 10px;font-weight:700">' + fmtShare(g.share) + '</td>'
        + '<td style="padding:8px 10px"><div class="itl-bar-wrap"><div class="itl-bar-bg"><div class="itl-bar-fill" style="width:' + (g.share / max * 100).toFixed(1) + '%"></div></div><span class="itl-bar-pct">' + (g.pct * 100).toFixed(1) + '%</span></div></td>'
        + '<td class="itl-num" style="text-align:right;padding:8px 10px;color:#556">' + fmtPct(g.avgCost) + '</td>'
        + '<td class="itl-num" style="text-align:right;padding:8px 10px;color:#556">' + fmtPct(g.avgSpread) + '</td></tr>';
    }).join('');
    var foot = '按「' + dimLabel(st.groupDim) + '」分组，共 ' + gd.length + ' 组' + (gd.length > 200 ? '（表内显示前 200 组，导出为全部）' : '') + ' · 点击表头可排序';
    return '<div class="itl-dimrow"><span class="lab">分组维度</span>' + dimButtons('gdim', st.groupDim) + '</div>'
      + '<table class="itl-table"><thead><tr>'
      + '<th style="text-align:right;width:44px">#</th>'
      + '<th class="s" data-act="sort" data-key="key" style="text-align:left">' + dimLabel(st.groupDim) + arrow('key') + '</th>'
      + '<th class="s" data-act="sort" data-key="count" style="text-align:right;width:90px">记录数' + arrow('count') + '</th>'
      + '<th class="s" data-act="sort" data-key="share" style="text-align:right;width:150px">认购份额(亿)' + arrow('share') + '</th>'
      + '<th style="text-align:left;width:150px">占比</th>'
      + '<th class="s" data-act="sort" data-key="avgCost" style="text-align:right;width:100px">平均成本' + arrow('avgCost') + '</th>'
      + '<th class="s" data-act="sort" data-key="avgSpread" style="text-align:right;width:100px">平均利差' + arrow('avgSpread') + '</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table><div class="itl-foot">' + foot + '</div>';
  }

  function renderPivot() {
    var pv = pivotData();
    var head = '<th class="rowhdr">' + dimLabel(st.pivotRow) + ' ＼ ' + dimLabel(st.pivotCol) + '</th>'
      + pv.cols.map(function (c) { return '<th>' + esc(c) + '</th>'; }).join('') + '<th class="tot">合计</th>';
    var body = pv.rows.map(function (r) {
      var cells = r.cells.map(function (v) { return '<td style="color:' + (v ? '#334' : '#d0d6de') + '">' + (v ? fmtShare(v) : '·') + '</td>'; }).join('');
      return '<tr><td class="rowlab">' + esc(r.label) + '</td>' + cells + '<td class="tot">' + fmtShare(r.total) + '</td></tr>';
    }).join('');
    var totrow = '<tr class="totrow"><td class="rowlab">合计</td>' + pv.colTotals.map(function (v) { return '<td>' + fmtShare(v) + '</td>'; }).join('') + '<td class="grand">' + fmtShare(pv.grand) + '</td></tr>';
    return '<div class="itl-dimrow"><span class="lab">行</span>' + dimButtons('prow', st.pivotRow) + '</div>'
      + '<div class="itl-dimrow"><span class="lab">列</span>' + dimButtons('pcol', st.pivotCol) + '<span style="font-size:11.5px;color:#a3adba">单元格 = 认购份额合计（亿）</span></div>'
      + '<div class="itl-pivot-scroll"><table class="itl-pivot"><thead><tr>' + head + '</tr></thead><tbody>' + body + totrow + '</tbody></table></div>'
      + '<div class="itl-foot">行取份额前 14 项、列取前 9 项，其余归入「其他」 · 空单元格以 · 表示</div>';
  }

  function renderDetail() {
    var recs = filtered().slice().sort(function (a, b) { return (b.share || 0) - (a.share || 0); });
    var note = '筛选后 ' + fmtInt(recs.length) + ' 条投资记录（按认购份额降序）' + (recs.length > 500 ? ' · 表内显示前 500 条，导出为全部' : '');
    var rows = recs.slice(0, 500).map(function (r) {
      return '<tr><td style="font-weight:600;color:#0d1b2e">' + esc(r.proj || '—') + '</td><td style="color:#556">' + esc(r.asset || '—') + '</td><td style="color:#556">' + esc(r.layer || '—') + '</td><td style="color:#556">' + esc(r.rating || '—') + '</td><td style="color:#0d1b2e">' + esc(r.inst || '—') + '</td><td class="r itl-accent" style="font-weight:700">' + fmtShare(r.share) + '</td><td class="r" style="color:#556">' + fmtPct(r.cost) + '</td><td class="r" style="color:#556">' + fmtPct(r.spread) + '</td><td style="color:#889">' + esc(r.date || '—') + '</td><td style="color:#556">' + esc(r.mgr || '—') + '</td></tr>';
    }).join('');
    return '<div style="font-size:12px;color:#8894a4;margin-bottom:10px">' + note + '</div>'
      + '<div class="itl-detail-scroll"><table class="itl-detail"><thead><tr>'
      + '<th>项目名称</th><th>资产类型</th><th>分层</th><th>评级</th><th>认购机构</th><th class="r">认购份额</th><th class="r">成本</th><th class="r">利差</th><th>簿记时间</th><th>计划管理人</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table></div>';
  }

  function exportCSV() {
    var rows = [], name = 'ABS投资台账';
    if (st.view === 'group') {
      name = '投资台账_按' + dimLabel(st.groupDim) + '汇总';
      rows.push([dimLabel(st.groupDim), '记录数', '认购份额(亿)', '占比', '平均成本', '平均利差']);
      groupData().forEach(function (r) { rows.push([r.key, r.count, r.share.toFixed(4), (r.pct * 100).toFixed(2) + '%', fmtPct(r.avgCost), fmtPct(r.avgSpread)]); });
    } else if (st.view === 'pivot') {
      name = '投资台账_透视表'; var pv = pivotData();
      rows.push([dimLabel(st.pivotRow) + '＼' + dimLabel(st.pivotCol)].concat(pv.cols).concat(['合计']));
      pv.rows.forEach(function (r) { rows.push([r.label].concat(r.cells.map(function (v) { return v ? v.toFixed(4) : ''; })).concat([r.total.toFixed(4)])); });
      rows.push(['合计'].concat(pv.colTotals.map(function (v) { return v.toFixed(4); })).concat([pv.grand.toFixed(4)]));
    } else {
      name = '投资台账_明细';
      rows.push(['项目名称', '资产类型', '分层', '评级', '认购机构', '认购份额(亿)', '成本', '利差', '簿记时间', '计划管理人', '联席承销商', '托管行', '发行场所', '规模(亿)']);
      filtered().forEach(function (r) { rows.push([r.proj, r.asset, r.layer, r.rating, r.inst, r.share, fmtPct(r.cost), fmtPct(r.spread), r.date, r.mgr, r.underwriter, r.custodian, r.venue, r.scale]); });
    }
    var csv = rows.map(function (row) { return row.map(function (c) { var t = c == null ? '' : String(c); return /[",\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t; }).join(','); }).join('\r\n');
    var blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name + '.csv'; document.body.appendChild(a); a.click(); a.remove();
  }

  function reset() {
    st.selKw = { asset: [], layer: [], rating: [], mgr: [], underwriter: [], custodian: [], inst: [] };
    st.dateFrom = ''; st.dateTo = ''; st.shareMin = ''; st.shareMax = '';
    SEL.forEach(function (f) { inputs[f.key].value = ''; });
    inputs.dateFrom.value = ''; inputs.dateTo.value = '';
    renderAllKw(); renderBadge(); renderCards(); renderResult();
  }

  function build(container) {
    root = container;
    var kwHtml = SEL.map(function (f) {
      var n = distinctCounts(f.key).size;
      var hint = f.pick ? '（' + n + ' 类）' : '（' + n + ' 家）';
      var ph = f.pick ? '点击选择…' : '输入联想…';
      return '<div class="itl-kwfield"><div class="itl-kwlab">' + f.label + '<span class="col"> ' + f.col + '</span><span class="hint">' + hint + '</span></div>'
        + '<input class="itl-kwinput" type="text" id="itl-in-' + f.key + '" placeholder="' + ph + '" autocomplete="off">'
        + '<div class="itl-drop" id="itl-drop-' + f.key + '"></div>'
        + '<div class="itl-selchips" id="itl-chips-sel-' + f.key + '"></div></div>';
    }).join('');

    root.className = 'itl-wrap';
    root.innerHTML =
      '<div class="itl-banner"><div class="itl-banner-title">投资台账 · 多维筛选统计</div>'
      + '<div class="itl-banner-sub">勾选 / 检索任意字段组合 → 实时统计认购份额、成本与利差 · 字段内多选取「或」，跨字段取「且」</div></div>'
      + '<div class="itl-body">'
      + '<div class="itl-card-box itl-filter"><div class="itl-filter-head"><div class="itl-filter-title"><span class="itl-tick"></span>筛选条件<span class="itl-badge" id="itl-badge">0 项生效</span></div><button class="itl-reset" id="itl-reset">清空全部</button></div>'
      + '<div class="itl-filter-body"><div class="itl-kwgrid">' + kwHtml + '</div>'
      + '<div class="itl-ranges" style="margin-top:12px">'
      + '<div class="itl-range"><span class="lab">簿记时间 <span class="col">L</span></span><input type="date" id="itl-date-from"><span class="itl-arrow">→</span><input type="date" id="itl-date-to"></div>'
      + '</div></div></div>'
      + '<div class="itl-cards" id="itl-cards"></div>'
      + '<div class="itl-card-box itl-result"><div class="itl-result-head"><div class="itl-vtabs" id="itl-vtabs">'
      + '<button class="itl-vtab on" data-view="group">分组统计</button><button class="itl-vtab" data-view="pivot">透视表</button><button class="itl-vtab" data-view="detail">明细清单</button>'
      + '</div><button class="itl-export" id="itl-export">⭳ 导出 CSV</button></div><div class="itl-pane" id="itl-pane"></div></div>'
      + '<div class="itl-footer">数据来源：' + esc(window.ITL_SOURCE || '2026年ABS发行台账-0703-定稿.xlsx') + '（' + fmtInt(DATA.length) + ' 条投资记录，穿透优先口径，已剔除自持 / 黑名单机构） · 分析报告员 Peizhi Wu</div>'
      + '</div>';

    // persistent input refs
    SEL.forEach(function (f) { inputs[f.key] = document.getElementById('itl-in-' + f.key); });
    inputs.dateFrom = document.getElementById('itl-date-from');
    inputs.dateTo = document.getElementById('itl-date-to');

    // input listeners
    SEL.forEach(function (f) {
      var inp = inputs[f.key];
      inp.addEventListener('input', function () { st.activeKw = f.key; renderKw(f.key); });
      inp.addEventListener('focus', function () { st.activeKw = f.key; renderKw(f.key); });
      inp.addEventListener('blur', function () { setTimeout(function () { if (st.activeKw === f.key) { st.activeKw = null; renderKw(f.key); } }, 150); });
    });
    inputs.dateFrom.addEventListener('input', function () { st.dateFrom = this.value; onFilterChange(); });
    inputs.dateTo.addEventListener('input', function () { st.dateTo = this.value; onFilterChange(); });
    document.getElementById('itl-reset').addEventListener('click', reset);
    document.getElementById('itl-export').addEventListener('click', exportCSV);

    // delegated clicks
    root.addEventListener('mousedown', function (e) {
      var el = e.target.closest('[data-act]'); if (!el) return;
      var act = el.dataset.act;
      if (act === 'add') { e.preventDefault(); var f = el.dataset.field, v = el.dataset.val; if (st.selKw[f].indexOf(v) < 0) st.selKw[f].push(v); inputs[f].value = ''; renderKw(f); onFilterChange(); }
    });
    root.addEventListener('click', function (e) {
      var el = e.target.closest('[data-act]'); if (!el) return;
      var act = el.dataset.act;
      if (act === 'rmkw') { var ff = el.dataset.field, vv = el.dataset.val, arr = st.selKw[ff], k = arr.indexOf(vv); if (k >= 0) arr.splice(k, 1); renderKw(ff); onFilterChange(); }
      else if (act === 'gdim') { st.groupDim = el.dataset.key; renderResult(); }
      else if (act === 'prow') { st.pivotRow = el.dataset.key; renderResult(); }
      else if (act === 'pcol') { st.pivotCol = el.dataset.key; renderResult(); }
      else if (act === 'sort') { var kk = el.dataset.key; if (st.sortKey === kk) st.sortDir = st.sortDir === 'desc' ? 'asc' : 'desc'; else { st.sortKey = kk; st.sortDir = 'desc'; } renderResult(); }
    });
    document.getElementById('itl-vtabs').addEventListener('click', function (e) {
      var b = e.target.closest('.itl-vtab'); if (!b) return; st.view = b.dataset.view; renderResult();
    });

    renderAllKw(); renderBadge(); renderCards(); renderResult();
  }

  function onFilterChange() { renderBadge(); renderCards(); renderResult(); }

  // ── 对外控制接口（供 Chatbox 联动）──────────────────────────────
  // applySpec：把一段结构化筛选规格写进面板状态并重渲染
  //   spec = { filters:{asset:[],layer:[],rating:[],mgr:[],underwriter:[],custodian:[],inst:[]},
  //            dateFrom, dateTo, shareMin, view, groupBy }
  function applySpec(spec) {
    spec = spec || {};
    var f = spec.filters || {};
    st.selKw = { asset: [], layer: [], rating: [], mgr: [], underwriter: [], custodian: [], inst: [] };
    st.dateFrom = spec.dateFrom || ''; st.dateTo = spec.dateTo || '';
    st.shareMin = (spec.shareMin != null && spec.shareMin !== '') ? String(spec.shareMin) : '';
    st.shareMax = '';
    ['asset', 'layer', 'rating', 'mgr', 'underwriter', 'custodian', 'inst'].forEach(function (k) { if (f[k] && f[k].length) st.selKw[k] = f[k].slice(); });
    if (spec.groupBy && DIMS.some(function (d) { return d.key === spec.groupBy; })) {
      st.view = 'group'; st.groupDim = spec.groupBy; st.sortKey = 'share'; st.sortDir = 'desc';
    } else if (spec.view) { st.view = spec.view; }
    if (root) {
      SEL.forEach(function (kf) { if (inputs[kf.key]) inputs[kf.key].value = ''; });
      if (inputs.dateFrom) { inputs.dateFrom.value = st.dateFrom; inputs.dateTo.value = st.dateTo; }
      renderAllKw(); renderBadge(); renderCards(); renderResult();
    }
  }

  window.ITL = {
    build: build,
    applySpec: applySpec,
    getData: function () { return DATA; },
    fields: { sel: SEL, dims: DIMS },
    distinctCounts: distinctCounts
  };
})();

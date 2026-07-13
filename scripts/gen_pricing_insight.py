"""ABS 定价测试 + 洞察面板 —— 新版双栏布局渲染器"""
import json
import os

PRICING_INSIGHT_CSS = """\

* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f0f2f5; font-family: "PingFang SC","Microsoft YaHei",sans-serif; font-size:14px; color:#1a1a2e; }

/* === Banner === */
.tool-banner { background: linear-gradient(135deg,#0d1b2e,#1a3a5c,#0d2a40); color:#fff; padding:18px 32px 16px; }
.banner-tag { font-size:11px; letter-spacing:2px; color:#7db8e8; margin-bottom:4px; }
.banner-title { font-size:19px; font-weight:700; }
.banner-sub { font-size:12px; color:#a0bfd4; margin-top:3px; }
.lab-badge { display:inline-block; background:#e8a838; color:#000; font-size:10px; padding:2px 8px; border-radius:3px; margin-left:12px; font-weight:700; }

/* === Top Controls: full-width === */
.ctrl-row-wrap { padding:16px 24px 0; }
.ctrl-panel { background:#fff; border-radius:8px; padding:18px 24px; box-shadow:0 1px 4px rgba(0,0,0,.08); }
.ctrl-row { display:flex; align-items:flex-end; gap:16px; flex-wrap:wrap; }
.ctrl-group { display:flex; flex-direction:column; gap:6px; }
.ctrl-label { font-size:12px; color:#6b7a95; letter-spacing:1px; text-transform:uppercase; }
select { height:38px; border:1px solid #d0d8e4; border-radius:5px; padding:0 12px; font-size:14px; font-family:inherit; color:#1a1a2e; background:#fafbfc; outline:none; cursor:pointer; min-width:170px; }
select:focus { border-color:#2563a8; }
select#tenorSelect { min-width:120px; }
.cost-ctrl { display:flex; align-items:center; gap:6px; }
.cost-input { width:72px; height:38px; border:1.5px solid #d0d8e4; border-radius:5px; text-align:center; font-size:15px; font-weight:600; font-family:inherit; color:#1a1a2e; background:#fff; outline:none; transition:border-color .2s; }
.cost-input:focus { border-color:#2563a8; }
.cost-input::-webkit-inner-spin-button, .cost-input::-webkit-outer-spin-button { -webkit-appearance:none; margin:0; }
.cost-input[type=number] { -moz-appearance:textfield; }
.cost-btn { width:32px; height:32px; border-radius:50%; border:1.5px solid #c0392b; background:#fff; color:#c0392b; font-size:19px; font-weight:600; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:background .15s,color .15s; flex-shrink:0; line-height:1; }
.cost-btn:hover { background:#c0392b; color:#fff; }
.cost-btn:active { background:#a93226; }
.btn { height:38px; padding:0 24px; background:#c0392b; color:#fff; border:none; border-radius:5px; font-size:14px; font-weight:600; font-family:inherit; cursor:pointer; letter-spacing:.5px; transition:background .2s; }
.btn:hover { background:#a93226; }

/* === Layout: insight LEFT, detail RIGHT, same row === */
.main-layout { display:flex; gap:20px; padding:20px 24px; margin:0 auto; align-items:stretch; }
.left-panel { flex:0 0 33.333%; min-width:0; max-width:33.333%; }
.right-panel { flex:1; min-width:0; display:flex; flex-direction:column; }

/* === Left: Insight Panel === */
.insight-panel { background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; display:flex; flex-direction:column; height:100%; }
.insight-header { background:linear-gradient(135deg,#0d2a40,#1a4a6e); color:#fff; padding:16px 20px 14px; flex-shrink:0; }
.insight-header .ih-title { font-size:18px; font-weight:700; }
.insight-header .ih-sub { font-size:12px; color:#7db8e8; margin-top:4px; letter-spacing:1px; }

.insight-tabs { display:flex; border-bottom:1px solid #e0e4ea; flex-shrink:0; }
.insight-tab { flex:1; padding:12px 0; text-align:center; font-size:14px; font-weight:600; color:#6b7a95; cursor:pointer; border-bottom:2px solid transparent; background:#fafbfc; transition:all .15s; }
.insight-tab:hover { color:#1a3a5c; background:#eef3fa; }
.insight-tab.active { color:#0d1b2e; background:#fff; border-bottom-color:#0d1b2e; }

.insight-body { padding:14px 18px; overflow-y:auto; flex:1; }

/* Window summary - horizontal layout */
.window-summary { background:#f0f5fb; border:1px solid #d0dce8; border-radius:6px; padding:12px 16px; margin-bottom:14px; display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
.window-summary .ws-badge { padding:5px 14px; border-radius:4px; font-size:13px; font-weight:700; letter-spacing:.5px; flex-shrink:0; }
.window-summary .ws-badge.week { background:#fff3e0; color:#e65100; }
.window-summary .ws-badge.month { background:#e3f2fd; color:#0d47a1; }
.window-summary .ws-stat { display:flex; flex-direction:column; align-items:center; min-width:50px; }
.window-summary .ws-stat-label { font-size:11px; color:#8a9ab5; letter-spacing:.3px; }
.window-summary .ws-stat-val { font-weight:600; color:#1a3a5c; font-size:14px; }
.window-summary .ws-divider { width:1px; height:28px; background:#d0dce8; flex-shrink:0; }

/* Inst cards grid */
.inst-cards { display:flex; flex-direction:column; gap:12px; }
.inst-card { background:#fafbfc; border:1px solid #e4e8ee; border-radius:5px; padding:9px 14px; display:flex; align-items:center; gap:0; }
.inst-card .ic-left { display:flex; align-items:center; gap:4px; flex-shrink:0; width:115px; overflow:hidden; }
.inst-card .ic-name { font-weight:600; font-size:14px; color:#1a2a40; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:85px; }
.inst-card .ic-badge { font-size:9px; padding:2px 5px; border-radius:3px; font-weight:600; flex-shrink:0; white-space:nowrap; }
.inst-card .ic-badge.new { background:#e8f5e9; color:#2e7d32; }
.inst-card .ic-stats { display:flex; flex:1; }
.inst-card .ic-stat { flex:1; text-align:center; min-width:0; }
.inst-card .ic-stat-label { color:#8a9ab5; font-size:11px; }
.inst-card .ic-stat-val { font-weight:600; color:#1a3a5c; font-size:13px; }

.no-insight { text-align:center; padding:24px 0; color:#9aa5b5; font-size:13px; }

/* === Right: Detail Table === */
.result-area { display:none; }
.result-area.show { display:block; }
.detail-header { background:linear-gradient(135deg,#0d2a40,#1a4a6e); color:#fff; padding:16px 20px 14px; border-radius:8px 8px 0 0; flex-shrink:0; }
.detail-header .dh-title { font-size:17px; font-weight:700; }
.detail-header .dh-sub { font-size:11px; color:#7db8e8; margin-top:4px; letter-spacing:1px; }

.hint-bar { padding:12px 16px; background:#e8f0fc; font-size:13px; color:#2a4a7c; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; flex-shrink:0; }
.hint-bar strong { color:#1a3a5c; font-size:15px; }
.res-table-wrap { background:#fff; border-radius:0 0 8px 8px; overflow:auto; box-shadow:0 1px 4px rgba(0,0,0,.08); }
.res-table { width:100%; border-collapse:collapse; min-width:680px; }
.res-table thead th { background:#1a3a5c; color:#fff; padding:10px 8px; text-align:center; font-size:12px; font-weight:600; letter-spacing:.3px; white-space:nowrap; position:sticky; top:0; }
.res-table tbody td { padding:9px 8px; font-size:13px; border-bottom:1px solid #eaeef4; text-align:center; white-space:nowrap; }
.res-table tbody tr:nth-child(even) { background:#f7f9fc; }
.res-table tbody tr:hover { background:#eef3fa; }
.rank-num { color:#6b7a95; }
.inst-cell { font-weight:500; color:#1a2a40; text-align:left !important; }
.date-cell { color:#6b7a95; font-size:12px; }
.cost-cell { font-weight:600; font-variant-numeric:tabular-nums; }
.spread-cell { color:#c0392b; font-weight:500; font-variant-numeric:tabular-nums; }
.ratio-cell { font-weight:500; color:#1a3a5c; }
.project-cell { text-align:left !important; color:#4a5a7a; font-size:12px; max-width:120px; overflow:hidden; text-overflow:ellipsis; }
.summary-row td { font-weight:600; color:#1a3a5c; background:#f0f4fa !important; border-top:2px solid #d0d8e4; }
.tenor-badge { display:inline-block; background:#c9ddef; color:#1a3a5c; padding:2px 10px; border-radius:3px; font-size:12px; font-weight:600; margin:0 4px; }
.empty-state { text-align:center; padding:60px 0; color:#9aa5b5; font-size:14px; }

/* Footer */
.lab-global-note { margin:20px 24px 0; padding:12px 18px; background:#fffbec; border:1px solid #ffe58f; border-radius:6px; font-size:11px; color:#7a6010; line-height:1.7; }
\
"""

_PRICING_INSIGHT_JS = """\
// ====== HELPERS ======
function getDataLatestDate() {
  const dates = ALL_DATA.map(r => r.date).filter(Boolean).sort();
  return dates[dates.length - 1] || '';
}

function addDays(dateStr, days) {
  const d = new Date(dateStr + 'T00:00:00');
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function fmtRange(s, e) { return s.slice(5) + ' ~ ' + e.slice(5); }

// ====== INIT ======
function populateProducts(products) {
  const sel = document.getElementById('productSelect');
  sel.innerHTML = '<option value="">—— 选择 ——</option>';
  products.forEach(p => {
    const o = document.createElement('option');
    o.value = p; o.textContent = p; sel.appendChild(o);
  });
}

function onTenorChange() {
  const tenor = document.getElementById('tenorSelect').value;
  if (tenor === '') populateProducts(ALL_PRODUCTS);
  else populateProducts(ALL_PRODUCTS.filter(p => p.startsWith(tenor)));
  document.getElementById('productSelect').value = '';
}

function adjCost(delta) {
  const inp = document.getElementById('costInput');
  let v = parseFloat(inp.value); if (isNaN(v)) v = 1.80;
  v = Math.round((v + delta) * 100) / 100;
  v = Math.max(1.50, Math.min(2.50, v));
  inp.value = v.toFixed(2); inp.select();
}

// ====== INSIGHT ======
let currentInsightData = null;
let currentTab = 'week';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.insight-tab').forEach(t => {
    t.classList.toggle('active', (tab === 'week' && t.textContent === '前一周') || (tab === 'month' && t.textContent === '前一个月'));
  });
  if (currentInsightData) renderInsight(currentInsightData, tab);
}

function computeWindowStats(instList, startDate, endDate) {
  const instSet = new Set(instList);
  const stats = {};
  instSet.forEach(inst => { stats[inst] = { count: 0, share: 0, costs: [], spreadSum: 0, spreadCount: 0, products: new Set(), dates: new Set(), ratios: [] }; });
  ALL_DATA.forEach(r => {
    if (r.date >= startDate && r.date <= endDate && stats[r.inst]) {
      const s = stats[r.inst];
      s.count++;
      s.share = parseFloat((s.share + r.share).toFixed(4));
      s.costs.push(r.cost);
      s.spreadSum += r.spread;
      s.spreadCount++;
      s.products.add(r.product);
      s.dates.add(r.date);
      const ts = PROJECT_SIZES[r.project];
      if (ts && ts > 0) s.ratios.push(r.share / ts * 100);
    }
  });
  return stats;
}

function buildInsight(filteredInsts, product, costLimit, latestDataDate) {
  const wrapper = document.getElementById('insightPanelWrapper');
  const tabs = document.getElementById('insightTabs');
  const empty = document.getElementById('insightEmpty');

  if (filteredInsts.length === 0) {
    wrapper.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  const weekStart = addDays(latestDataDate, -6);
  const monthStart = addDays(latestDataDate, -29);
  currentInsightData = {
    filteredInsts, product, costLimit, latestDataDate,
    weekStart, monthStart,
    weekStats: computeWindowStats(filteredInsts, weekStart, latestDataDate),
    monthStats: computeWindowStats(filteredInsts, monthStart, latestDataDate),
  };

  tabs.style.display = 'flex';
  currentTab = 'week';
  document.querySelectorAll('.insight-tab').forEach((t, i) => { t.classList.toggle('active', i === 0); });

  wrapper.style.display = 'flex';
  empty.style.display = 'none';
  renderInsight(currentInsightData, 'week');
}

function renderInsight(d, tab) {
  const body = document.getElementById('insightBody');
  const { filteredInsts, product, costLimit, latestDataDate, weekStart, monthStart, weekStats, monthStats } = d;

  const isWeek = tab === 'week';
  const stats = isWeek ? weekStats : monthStats;
  const startDate = isWeek ? weekStart : monthStart;
  const label = isWeek ? '前一周' : '前一个月';
  const badgeClass = isWeek ? 'week' : 'month';

  const sorted = filteredInsts.filter(i => stats[i].count > 0).sort((a, b) => stats[b].share - stats[a].share);
  const totalInsts = sorted.length;
  const totalShare = Object.values(stats).reduce((s, v) => s + v.share, 0);
  const activeInWindow = filteredInsts.filter(i => stats[i].count > 0).length;
  const inactiveCount = filteredInsts.length - activeInWindow;

  let html = '';

  // --- 品种洞察 (above summary) ---
  html += '<div style="margin-bottom:12px;padding:12px 14px;background:#fefdf5;border:1px solid #e8e0c0;border-radius:5px;font-size:12px;color:#5a4a20;line-height:1.7;">';
  html += '<div style="font-weight:700;color:#3a2a00;margin-bottom:6px;">品种洞察</div>';

  if (sorted.length === 0) {
    html += '该时段无认购记录。';
  } else {
    const top3 = sorted.slice(0, Math.min(3, sorted.length));
    const topNames = top3.join('、');
    const totalFiltered = filteredInsts.length;
    const activeRate = totalFiltered > 0 ? (sorted.length / totalFiltered * 100).toFixed(0) : 0;
    const allCosts = [];
    sorted.forEach(function(x) { allCosts.push.apply(allCosts, stats[x].costs); });
    const minAll = allCosts.length > 0 ? Math.min.apply(null, allCosts).toFixed(2) : '--';
    const maxAll = allCosts.length > 0 ? Math.max.apply(null, allCosts).toFixed(2) : '--';
    const allRatios = [];
    sorted.forEach(function(x) { allRatios.push.apply(allRatios, stats[x].ratios); });
    const avgAllRatio = allRatios.length > 0 ? (allRatios.reduce(function(a,b){return a+b;},0) / allRatios.length).toFixed(1) : '--';
    const avgEntries = sorted.length > 0 ? (sorted.reduce(function(s,x){return s + stats[x].count;},0) / sorted.length).toFixed(1) : 0;
    const levelText = activeRate >= 80 ? '较高' : activeRate >= 50 ? '一般' : '偏低';
    html += '在' + label + '（' + fmtRange(startDate, latestDataDate) + '）内，';
    html += '筛选的 ' + totalFiltered + ' 家机构中，有 <strong>' + sorted.length + ' 家</strong>（' + activeRate + '%）参与认购，';
    html += '主要集中在 <strong>' + topNames + '</strong>。';
    html += '利率区间 <strong>' + minAll + '% ~ ' + maxAll + '%</strong>，';
    html += '机构投标活跃度' + levelText + '，';
    html += '平均每家参与 ' + avgEntries + ' 次，';
    html += '平均单期认购比例 <strong>' + avgAllRatio + '%</strong>。';
  }
  html += '</div>';

  // Horizontal summary bar
  html += '<div class="window-summary">';
  html += '<span class="ws-badge ' + badgeClass + '">' + label + '</span>';
  html += '<div class="ws-stat"><div class="ws-stat-label">筛选机构</div><div class="ws-stat-val">' + filteredInsts.length + ' 家</div></div>';
  html += '<div class="ws-divider"></div>';
  html += '<div class="ws-stat"><div class="ws-stat-label">' + label + '活跃</div><div class="ws-stat-val" style="color:#2e7d32;">' + activeInWindow + ' 家</div></div>';
  if (inactiveCount > 0 || true) {
    html += '<div class="ws-stat"><div class="ws-stat-label">无投标</div><div class="ws-stat-val" style="color:#9aa5b5;">' + inactiveCount + ' 家</div></div>';
  }
  html += '<div class="ws-divider"></div>';
  html += '<div class="ws-stat"><div class="ws-stat-label">合计申购</div><div class="ws-stat-val">' + totalShare.toFixed(2) + ' 亿</div></div>';
  html += '<span style="font-size:10px;color:#8a9ab5;margin-left:auto;">' + fmtRange(startDate, latestDataDate) + '</span>';
  html += '</div>';

  if (sorted.length === 0) {
    html += '<div class="no-insight">该时段无认购记录</div>';
  } else {
    html += '<div class="inst-cards">';
    sorted.forEach(function(inst, idx) {
      const s = stats[inst];
      if (s.count === 0) return;

      const minCost = s.costs.length > 0 ? Math.min(...s.costs).toFixed(2) : '--';
      const maxCost = s.costs.length > 0 ? Math.max(...s.costs).toFixed(2) : '--';
      const rangeStr = minCost === maxCost ? minCost + '%' : minCost + '~' + maxCost + '%';
      const avgCost = s.costs.length > 0 ? (s.costs.reduce((a,b)=>a+b,0) / s.costs.length).toFixed(2) : '--';
      const avgRatio = s.ratios.length > 0 ? (s.ratios.reduce((a,b)=>a+b,0) / s.ratios.length).toFixed(1) : '--';
      const isNew = !isWeek && weekStats[inst].count > 0;

      html += '<div class="inst-card">';
      html += '<div class="ic-left">';
      html += '<span class="ic-name" title="' + inst + '">' + inst + '</span>';
      if (isNew) html += '<span class="ic-badge new">前一周</span>';
      html += '</div>';
      html += '<div class="ic-stats">';
      html += '<div class="ic-stat"><div class="ic-stat-label">次数</div><div class="ic-stat-val">' + s.count + '次</div></div>';
      
      html += '<div class="ic-stat"><div class="ic-stat-label">规模</div><div class="ic-stat-val">' + s.share.toFixed(2) + '亿</div></div>';
      html += '<div class="ic-stat"><div class="ic-stat-label">利率区间</div><div class="ic-stat-val">' + rangeStr + '</div></div>';
      html += '<div class="ic-stat"><div class="ic-stat-label">均价</div><div class="ic-stat-val">' + avgCost + '%</div></div>';
      html += '<div class="ic-stat"><div class="ic-stat-label">均单期比</div><div class="ic-stat-val">' + avgRatio + '%</div></div>';
      html += '</div></div>';
    });
    html += '</div>';


  }

  body.innerHTML = html;
}

// ====== SEARCH ======
function doSearch() {
  const product = document.getElementById('productSelect').value;
  const costLimit = parseFloat(document.getElementById('costInput').value);
  const resultArea = document.getElementById('resultArea');
  const detailEmpty = document.getElementById('detailEmpty');
  const tbody = document.getElementById('resultBody');
  const wrapper = document.getElementById('insightPanelWrapper');
  const insightEmpty = document.getElementById('insightEmpty');

  if (!product || isNaN(costLimit)) {
    alert('请选择产品类型并输入投标利率上限');
    return;
  }

  const latestDataDate = getDataLatestDate();

  const filtered = ALL_DATA
    .filter(r => r.product === product && r.cost <= costLimit)
    .sort(function(a, b) {
      if (a.date !== b.date) return a.date < b.date ? 1 : -1;
      return a.cost - b.cost;
    });

  const filteredInsts = [...new Set(filtered.map(r => r.inst))];

  // Detail header
  document.getElementById('dhTitle').textContent = '定价明细';
  document.getElementById('dhSub').textContent = product + ' · ≤' + costLimit.toFixed(2) + '% · ' + filtered.length + ' 条记录';

  const latestMonth = [...new Set(filtered.map(r => r.date ? r.date.slice(0, 7) : null))].filter(Boolean).sort().reverse()[0] || '——';
  const tenorLabel = filtered.length > 0 ? filtered[0].tenor : '——';

  document.getElementById('hintText').innerHTML =
    '<strong>' + product + '</strong> | 不高于 <strong>' + costLimit.toFixed(2) + '%</strong>' +
    ' <span class="tenor-badge">' + tenorLabel + '</span>';
  document.getElementById('metaTag').textContent =
    '最新月份：' + latestMonth + ' | ' + filteredInsts.length + ' 家穿透机构';

  if (filtered.length === 0) {
    resultArea.style.display = 'none';
    detailEmpty.style.display = 'block';
    detailEmpty.textContent = '该产品暂无投标利率不高于 ' + costLimit.toFixed(2) + '% 的记录';
    wrapper.style.display = 'none';
    insightEmpty.style.display = 'block';
    return;
  }

  const totalShare = filtered.reduce((s, r) => s + r.share, 0).toFixed(2);
  const rows = filtered.map(function(r, i) {
    const totalSize = PROJECT_SIZES[r.project];
    const ratio = (totalSize && totalSize > 0) ? (r.share / totalSize * 100).toFixed(1) + '%' : '--';
    return '<tr>' +
      '<td class="rank-num">' + (i+1) + '</td>' +
      '<td class="inst-cell">' + r.inst + '</td>' +
      '<td class="project-cell" title="' + r.project + '">' + r.project + '</td>' +
      '<td class="date-cell">' + r.date + '</td>' +
      '<td class="cost-cell">' + r.cost.toFixed(2) + '%</td>' +
      '<td class="spread-cell">+' + r.spread.toFixed(2) + '%</td>' +
      '<td>' + r.share.toFixed(2) + '</td>' +
      '<td class="ratio-cell">' + ratio + '</td>' +
    '</tr>';
  }).join('');

  tbody.innerHTML = rows +
    '<tr class="summary-row">' +
      '<td colspan="7" style="text-align:right;font-size:12px;color:#6b7a95;padding-right:16px">' +
        filtered.length + ' 条记录 · 合计' +
      '</td>' +
      '<td>' + totalShare + '</td>' +
    '</tr>';

  resultArea.style.display = 'block';
  detailEmpty.style.display = 'none';
  insightEmpty.style.display = 'none';
  buildInsight(filteredInsts, product, costLimit, latestDataDate);
}

// ====== DEFAULT VIEW ======
// 页面首次加载时自动展示一个默认查询结果（1年期赊销白条 · ≤1.80%），
// 让用户不做任何筛选也能了解这个面板展示什么信息；找不到该具体产品时
// 退化为"1年期"下的第一个产品，避免因数据变化导致默认视图失效。
function initDefaultView() {
  const defaultTenor = '1年期';
  const preferredProduct = ALL_PRODUCTS.find(p => p.startsWith(defaultTenor) && p.indexOf('赊销白条') >= 0)
    || ALL_PRODUCTS.find(p => p.startsWith(defaultTenor))
    || ALL_PRODUCTS[0];
  if (!preferredProduct) return;
  document.getElementById('tenorSelect').value = defaultTenor;
  onTenorChange();
  document.getElementById('productSelect').value = preferredProduct;
  document.getElementById('costInput').value = '1.80';
  doSearch();
}

populateProducts(ALL_PRODUCTS);
initDefaultView();
\
"""

_PRICING_INSIGHT_HTML = """\
<div class="tool-banner">
  <div class="banner-tag">ABS Investor Intelligence Tool <span class="lab-badge">LAB v5</span></div>
  <div class="banner-title">发行定价测试</div>
  <div class="banner-sub">筛选贯穿顶部 → 洞察（左）｜ 明细（右）对齐排列</div>
</div>

<!-- === Top Controls: full-width === -->
<div class="ctrl-row-wrap">
  <div class="ctrl-panel">
    <div class="ctrl-row">
      <div class="ctrl-group">
        <div class="ctrl-label">期限</div>
        <select id="tenorSelect" onchange="onTenorChange()">
          <option value="">全部</option>
          <option value="1年期">1年期</option>
          <option value="超1年期">超1年期</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">产品类型</div>
        <select id="productSelect">
          <option value="">—— 选择 ——</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">投标利率上限（%）</div>
        <div class="cost-ctrl">
          <button class="cost-btn" onclick="adjCost(-0.01)">&#8722;</button>
          <input type="number" id="costInput" class="cost-input" min="1.50" max="2.50" step="0.01" value="1.80" onclick="this.select()">
          <button class="cost-btn" onclick="adjCost(0.01)">+</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">&nbsp;</div>
        <button class="btn" onclick="doSearch()">查询</button>
      </div>
    </div>
  </div>
</div>

<!-- === Main: Insight LEFT, Detail RIGHT === -->
<div class="main-layout">
  <!-- LEFT: Insight -->
  <div class="left-panel">
    <div class="insight-panel" id="insightPanelWrapper" style="display:none;">
      <div class="insight-header">
        <div class="ih-title">投资动态洞察</div>
        <div class="ih-sub">仅统计分层为「优先A / 优先级 / 优先A1 / 优先A2」的机构</div>
      </div>
      <div class="insight-tabs" id="insightTabs" style="display:none;">
        <div class="insight-tab active" onclick="switchTab('week')">前一周</div>
        <div class="insight-tab" onclick="switchTab('month')">前一个月</div>
      </div>
      <div class="insight-body" id="insightBody">
        <div class="no-insight">点击"查询"后自动生成</div>
      </div>
    </div>
    <div style="text-align:center;padding:60px 0;color:#9aa5b5;font-size:14px;" id="insightEmpty">
      选择产品类型和利率上限，点击查询
    </div>
  </div>

  <!-- RIGHT: Detail -->
  <div class="right-panel">
    <div class="result-area" id="resultArea">
      <div class="detail-header" id="detailHeader">
        <div class="dh-title" id="dhTitle">定价明细</div>
        <div class="dh-sub" id="dhSub">——</div>
      </div>
      <div class="hint-bar">
        <span id="hintText"></span>
        <span id="metaTag" style="font-size:12px;color:#5a7aa8"></span>
      </div>
      <div class="res-table-wrap">
        <table class="res-table">
          <thead>
            <tr>
              <th style="width:32px">#</th>
              <th style="text-align:left">穿透机构</th>
              <th style="text-align:left">项目名称</th>
              <th>簿记日期</th>
              <th>投标利率</th>
              <th>基准利差</th>
              <th>申购规模（亿）</th>
              <th style="width:80px">单期比例</th>
            </tr>
          </thead>
          <tbody id="resultBody"></tbody>
        </table>
      </div>
    </div>
    <div class="empty-state" id="detailEmpty">
      选择产品类型和利率上限，点击查询
    </div>
  </div>
</div>

<div class="lab-global-note">
  Lab v5：筛选框贯穿顶部全宽，与洞察/明细解耦。洞察摘要横向排列。机构卡片数字字号统一，列均匀分布占满宽度。洞察与明细同一水平线。
</div>\
"""


def render_pricing_panel(data):
    """渲染定价测试面板（新版双栏：洞察左1/3 + 明细右2/3）"""
    products_js = data['products_js']
    data_js = data['data_js']
    proj_sizes_js = data.get('proj_sizes_js', '{}')
    xlsx_basename = data['xlsx_basename']

    body = _PRICING_INSIGHT_HTML.replace('{xlsx_basename}', xlsx_basename)

    script = (
        '<script>\n'
        'const ALL_PRODUCTS = ' + products_js + ';\n'
        'const ALL_DATA = ' + data_js + ';\n'
        'const PROJECT_SIZES = ' + proj_sizes_js + ';\n'
        '\n'
        + _PRICING_INSIGHT_JS +
        '\n</script>'
    )

    return body + script

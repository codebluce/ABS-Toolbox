/* ABS 综合看板 · 手机视图（纯 JS，无依赖）
   数据来源：window.PROG_QUICK（机构画像预计算）+ 本文件内静态口径数据 */
(function () {
  'use strict';

  var S = {
    q: '', owner: '', cat: '', sel: null, limit: 24, openPr: {}, prAll: false,
    tab: 'progress', sub: 'quick', sheet: null,
    assetSide: 'consume', caliber: false,
    peerView: 'overview', peerOpen: {}, peerCaliber: false
  };

  var INJ = (typeof window !== 'undefined' && window.ABS_MOBILE_DATA) || {};
  var META = INJ.meta || { snapshot: '2026-08-16', assetDate: '08-14', peerDate: '08-14', progYear: 2026 };

  // 资产集团配色优先取电脑端图例(gen_mobile_dashboard 从 peer_issuance_panel
  // 渲染出的图例回读注入),电脑端调色手机端自动跟随。下面只是解析失败时的兜底,
  // 取值须与 peer_issuance_panel.ASSET_FAMILY_COLORS 一致:
  // 京东系固定用 #cf6b6b 红,字节系用 #0d1b2e 深蓝。
  var CG_FALLBACK = { '京东系': '#cf6b6b', '蚂蚁系': '#2a78d6', '网商系': '#4e9f8b', '腾讯系': '#7c6eb0', '微众系': '#c98747', '字节系': '#0d1b2e', '美团系': '#6f8e45', '其他': '#98a1ad', '未知资产': '#98a1ad' };
  var CG = (INJ.peer && INJ.peer.colors) || CG_FALLBACK;

  var ASSET = INJ.asset || {
    kpis: [
      { label: '消费贷', val: '1,412', d: -8, p: -0.55 },
      { label: '现金贷', val: '4,279', d: 9, p: 0.21 },
      { label: '消金合计', val: '5,691', d: 1, p: 0.02 }
    ],
    consume: {
      note: '白条消费 + 分分卡',
      groups: [
        { title: '资产类型结构', rows: [
          { label: '白条消费', amount: '1,208 亿', w: 85.6, share: '86%', d: -6, p: -0.49 },
          { label: '分分卡', amount: '203 亿', w: 14.4, share: '14%', d: -2, p: -0.88 }
        ] },
        { title: '资金类型结构', rows: [
          { label: '赊销', amount: '730 亿', w: 51.73, share: '52%', d: -1, p: -0.14 },
          { label: '助贷合计', amount: '366 亿', w: 25.94, share: '26%', d: -5, p: -1.46 },
          { label: '信托', amount: '272 亿', w: 19.29, share: '19%', d: 0, p: 0.01 },
          { label: '小贷', amount: '43 亿', w: 3.03, share: '3%', d: -1, p: -3.04 }
        ] }
      ]
    },
    cash: {
      note: '金条 + 白取',
      groups: [
        { title: '资产类型结构', rows: [
          { label: '金条', amount: '3,735 亿', w: 87.28, share: '87%', d: 7, p: 0.19 },
          { label: '白取', amount: '544 亿', w: 12.72, share: '13%', d: 2, p: 0.38 }
        ] },
        { title: '资金类型结构', rows: [
          { label: '助贷合计', amount: '2,208 亿', w: 51.6, share: '52%', d: 9, p: 0.42 },
          { label: '信托', amount: '1,910 亿', w: 44.65, share: '45%', d: 5, p: 0.24 },
          { label: '小贷', amount: '161 亿', w: 3.75, share: '4%', d: -5, p: -2.92 }
        ] }
      ]
    }
  };

  var PEER = INJ.peer || {
    groups: [
      { label: '网商系', w: 22.58, amt: '681 亿 · 23%', ly: '287 亿', d: 394, p: 137.28 },
      { label: '蚂蚁系', w: 19.90, amt: '600 亿 · 20%', ly: '579 亿', d: 21, p: 3.63 },
      { label: '美团系', w: 12.60, amt: '380 亿 · 13%', ly: '383 亿', d: -3, p: -0.78 },
      { label: '腾讯系', w: 12.57, amt: '379 亿 · 13%', ly: '361 亿', d: 18, p: 4.87 },
      { label: '微众系', w: 8.66, amt: '261 亿 · 9%', ly: '105 亿', d: 156, p: 148.57 },
      { label: '字节系', w: 7.69, amt: '232 亿 · 8%', ly: '50 亿', d: 182, p: 364.00 },
      { label: '其他', w: 16.01, amt: '483 亿 · 16%', ly: '465 亿', d: 17, p: 3.72 }
    ],
    trust: [
      { name: '国投信托', total: '714 亿 · 29%', segs: [['蚂蚁系', 260, 36], ['网商系', 240, 34], ['腾讯系', 84, 12], ['字节系', 80, 11], ['其他', 50, 7]] },
      { name: '华能信托', total: '553 亿 · 23%', segs: [['腾讯系', 109, 20], ['微众系', 176, 32], ['字节系', 40, 7], ['美团系', 127, 23], ['其他', 101, 18]] },
      { name: '华鑫信托', total: '354 亿 · 14%', segs: [['蚂蚁系', 95, 27], ['网商系', 180, 51], ['字节系', 10, 3], ['美团系', 56, 16], ['其他', 13, 4]] },
      { name: '外贸信托', total: '351 亿 · 14%', segs: [['网商系', 136, 39], ['微众系', 60, 17], ['字节系', 10, 3], ['美团系', 30, 9], ['其他', 115, 33]] },
      { name: '中信信托', total: '236 亿 · 10%', segs: [['蚂蚁系', 155, 66], ['网商系', 5, 2], ['美团系', 40, 17], ['其他', 36, 15]] },
      { name: '其他渠道（合并 3 家）', total: '242 亿 · 10%', segs: [['蚂蚁系', 90, 37], ['网商系', 120, 50], ['字节系', 20, 8], ['其他', 12, 5]] }
    ],
    top: [
      { name: '网商贷', cat: '小微toB', amt: '681 亿', terms: '68 期', rows: [['国投信托', '240 亿 · 35%', 35, '7月 40 → 8月 10（-30 亿）', -1], ['华鑫信托', '180 亿 · 26%', 26, '7月 10 → 8月 30（+20 亿）', 1], ['外贸信托', '136 亿 · 20%', 20, '7月 40 → 8月 0（-40 亿）', -1], ['上海信托', '120 亿 · 18%', 18, '7月 80 → 8月 0（-80 亿）', -1], ['中信信托', '5 亿 · 1%', 1, '7月 0 → 8月 5（新增 5 亿）', 1]] },
      { name: '蚂蚁花呗', cat: '消金分期类', amt: '490 亿', terms: '49 期', rows: [['国投信托', '180 亿 · 37%', 37, '7月 40 → 8月 0（-40 亿）', -1], ['中信信托', '155 亿 · 32%', 32, '7月 20 → 8月 40（+20 亿）', 1], ['华鑫信托', '65 亿 · 13%', 13, '7月 5 → 8月 10（+5 亿）', 1], ['上海信托', '60 亿 · 12%', 12, '7月 0 → 8月 20（新增 20 亿）', 1], ['厦门信托', '30 亿 · 6%', 6, '7月 0 → 8月 0（0 亿）', 0]] },
      { name: '腾讯分付', cat: '消金分期类', amt: '379 亿', terms: '46 期', rows: [['财付通小贷', '185 亿 · 49%', 49, '7月 40 → 8月 32（-8 亿）', -1], ['华能信托', '109 亿 · 29%', 29, '7月 15 → 8月 9（-6 亿）', -1], ['国投信托', '84 亿 · 22%', 22, '7月 11 → 8月 8（-4 亿）', -1]] },
      { name: '微众银行微粒贷', cat: '消金提现类', amt: '216 亿', terms: '24 期', rows: [['华能信托', '156 亿 · 72%', 72, '7月 30 → 8月 0（-30 亿）', -1], ['外贸信托', '60 亿 · 28%', 28, '7月 0 → 8月 0（0 亿）', 0]] },
      { name: '美团月付', cat: '消金分期类', amt: '188 亿', terms: '22 期', rows: [['美团小贷', '60 亿 · 32%', 32, '7月 0 → 8月 0（0 亿）', 0], ['华能信托', '55 亿 · 29%', 29, '7月 20 → 8月 0（-20 亿）', -1], ['中信信托', '40 亿 · 21%', 21, '7月 15 → 8月 10（-5 亿）', -1], ['华鑫信托', '33 亿 · 18%', 18, '7月 0 → 8月 0（0 亿）', 0]] },
      { name: '抖音放心借·小微', cat: '小微toC', amt: '175 亿', terms: '17 期', rows: [['国投信托', '80 亿 · 46%', 46, '7月 20 → 8月 10（-10 亿）', -1], ['华能信托', '40 亿 · 23%', 23, '7月 10 → 8月 0（-10 亿）', -1], ['中融小贷', '35 亿 · 20%', 20, '7月 15 → 8月 0（-15 亿）', -1], ['华鑫信托', '10 亿 · 6%', 6, '7月 0 → 8月 0（0 亿）', 0], ['外贸信托', '10 亿 · 6%', 6, '7月 0 → 8月 0（0 亿）', 0]] },
      { name: '美团生活费', cat: '消金提现类', amt: '148 亿', terms: '28 期', rows: [['华能信托', '55 亿 · 37%', 37, '7月 4 → 8月 0（-4 亿）', -1], ['美团小贷', '40 亿 · 27%', 27, '7月 0 → 8月 0（0 亿）', 0], ['外贸信托', '30 亿 · 20%', 20, '7月 3 → 8月 0（-3 亿）', -1], ['华鑫信托', '23 亿 · 16%', 16, '7月 8 → 8月 0（-8 亿）', -1]] },
      { name: '度小满满易贷', cat: '消金提现类', amt: '140 亿', terms: '18 期', rows: [['外贸信托', '70 亿 · 50%', 50, '7月 20 → 8月 35（+15 亿）', 1], ['度小满小贷', '70 亿 · 50%', 50, '7月 0 → 8月 0（0 亿）', 0]] }
    ]
  };

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function num(v) { return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function dText(d, p) { return (d > 0 ? '+' : (d < 0 ? '' : '±')) + d + ' 亿（' + (p > 0 ? '+' : '') + p.toFixed(2) + '%）'; }
  function dColor(d) { return d > 0 ? '#1c7a4f' : (d < 0 ? '#b3452f' : '#6b7a95'); }
  function data() { return window.PROG_QUICK || []; }

  function fmtDate(raw) {
    var s = String(raw || '').trim();
    if (!s) return '';
    var full = s.match(/(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})/);
    if (full) return full[1] + '年' + (+full[2]) + '月' + (+full[3]) + '日';
    var parts = s.split(/[-~—至]/).map(function (x) { return x.trim(); }).filter(Boolean);
    var last = parts[parts.length - 1] || s;
    var md = last.match(/^(\d{2})(\d{2})$/);
    if (md) return '2026年' + (+md[1]) + '月' + (+md[2]) + '日';
    var cn = last.match(/(\d{1,2})月(\d{1,2})/);
    if (cn) return '2026年' + (+cn[1]) + '月' + (+cn[2]) + '日';
    return s;
  }

  function filtered() {
    var q = S.q.trim().toLowerCase();
    return data().filter(function (r) {
      if (S.owner && r.o !== S.owner) return false;
      if (S.cat && r.c !== S.cat) return false;
      if (!q) return true;
      if (String(r.n).toLowerCase().indexOf(q) >= 0) return true;
      if (String(r.c || '').toLowerCase().indexOf(q) >= 0) return true;
      if (String(r.o || '').toLowerCase().indexOf(q) >= 0) return true;
      return (r.ct || []).some(function (c) { return (c.name + c.dept).toLowerCase().indexOf(q) >= 0; });
    }).sort(function (a, b) { return b.tot - a.tot; });
  }

  /* ---------- shared style fragments ---------- */
  var CARD = 'background:#fff; border-radius:13px; box-shadow:0 1px 2px rgba(13,27,46,.06);';
  var H2 = 'font-size:13px; font-weight:700; color:#0d1b2e; letter-spacing:.4px;';
  var SUB = 'font-size:11px; color:#6b7a95;';
  var STICKY = 'position:sticky; top:0; z-index:30; background:#f2f4f8; padding:2px 0 10px; box-shadow:0 8px 12px -8px rgba(13,27,46,.16);';

  function pill(label, on, act) {
    return '<div data-act="' + act + '" style="flex:0 0 auto; padding:7px 14px; border-radius:16px; font-size:12.5px; font-weight:' +
      (on ? '600' : '500') + '; background:' + (on ? '#0d1b2e' : '#fff') + '; color:' + (on ? '#fff' : '#6b7a95') +
      '; border:1px solid ' + (on ? '#0d1b2e' : '#e4e8ee') + '; min-height:32px; display:flex; align-items:center;">' + esc(label) + '</div>';
  }
  function fold(open) {
    return '<svg width="9" height="6" viewBox="0 0 9 6" fill="none" stroke="#6b7a95" stroke-width="1.7" stroke-linecap="round" style="transform:' +
      (open ? 'rotate(180deg)' : 'none') + ';"><path d="M1 1.4 4.5 4.8 8 1.4"></path></svg>';
  }
  function barRow(label, amount, w, subLeft, subRight, subRightColor, color) {
    return '<div style="margin-bottom:14px;">' +
      '<div style="display:flex; align-items:baseline; justify-content:space-between; gap:8px;">' +
        '<span style="font-size:13px; font-weight:600; color:#0d1b2e; white-space:nowrap;">' + label + '</span>' +
        '<span style="font-size:13px; font-weight:700; color:#0d1b2e; font-variant-numeric:tabular-nums; white-space:nowrap;">' + esc(amount) + '</span>' +
      '</div>' +
      '<div style="margin-top:6px; height:6px; border-radius:3px; background:#eef1f6; overflow:hidden;">' +
        '<div style="height:100%; width:' + w + '; background:' + color + '; border-radius:3px;"></div>' +
      '</div>' +
      '<div style="margin-top:5px; display:flex; align-items:baseline; justify-content:space-between; gap:8px;">' +
        '<span style="' + SUB + ' font-variant-numeric:tabular-nums;">' + subLeft + '</span>' +
        '<span style="font-size:11px; font-weight:600; color:' + subRightColor + '; font-variant-numeric:tabular-nums;">' + esc(subRight) + '</span>' +
      '</div>' +
    '</div>';
  }

  /* ---------- 机构画像 · 列表 ---------- */
  function viewQuickList() {
    var h = '<div>' +
      '<div style="' + STICKY + '">' +
        '<div style="padding:0 20px; display:flex; align-items:baseline; justify-content:space-between;">' +
          '<div style="font-size:23px; font-weight:700; color:#0d1b2e; letter-spacing:.5px;">机构画像</div>' +
          '<div style="' + SUB + ' letter-spacing:.2px;">快照 ' + META.snapshot + '</div>' +
        '</div>' +
        '<div class="noscroll" style="margin-top:11px; padding:0 20px; display:flex; gap:7px; overflow-x:auto;">' +
          // 子标签与电脑端 gen_integrated_dashboard.sub_label_map 保持一致:
          // 理财子分析/非标额度已于 0820 暂时下线,机构统计为新增
          pill('机构速查', S.sub === 'quick', 'sub:quick') +
          pill('机构统计', false, 'sub:inst_stats') +
          pill('授信总额度', false, 'sub:credit_total') +
        '</div>' +
        '<div style="padding:0 20px; margin-top:11px;">' +
          '<div style="display:flex; align-items:center; gap:9px; height:44px; background:#fff; border:1px solid #e4e8ee; border-radius:12px; padding:0 13px;">' +
            '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#9aa5b5" stroke-width="1.7" stroke-linecap="round"><circle cx="7" cy="7" r="5"></circle><path d="M10.8 10.8 14 14"></path></svg>' +
            '<input id="m-q" type="text" value="' + esc(S.q) + '" placeholder="搜索机构、联系人、负责人" style="flex:1; border:none; outline:none; font-size:15px; color:#0d1b2e; background:transparent; font-family:inherit; min-width:0;">' +
            (S.q ? '<div data-act="q:clear" style="width:20px; height:20px; border-radius:10px; background:#e4e8ee; color:#6b7a95; font-size:13px; display:flex; align-items:center; justify-content:center; flex:0 0 auto;">×</div>' : '') +
          '</div>' +
        '</div>' +
        '<div style="padding:0 20px; margin-top:9px; display:flex; gap:8px;">' +
          filterBtn(S.owner || '负责人', !!S.owner, 'sheet:owner') +
          filterBtn(S.cat || '机构类型', !!S.cat, 'sheet:cat') +
        '</div>' +
      '</div>' +
      '<div id="m-list">' + quickListBody() + '</div></div>';
    return h;
  }

  function quickListBody() {
    var rows = filtered(), shown = rows.slice(0, S.limit);
    var h = '<div style="padding:10px 20px 4px; display:flex; align-items:baseline; justify-content:space-between;">' +
        '<div style="' + SUB + '">' + rows.length + ' 家机构</div>' +
        '<div style="' + SUB + '">按累计投资规模排序</div>' +
      '</div>' +
      '<div style="padding:0 20px 18px; display:flex; flex-direction:column; gap:8px;">';

    shown.forEach(function (r) {
      h += '<div data-act="open:' + esc(r.n) + '" style="' + CARD + ' padding:12px 14px; display:flex; align-items:center; gap:12px; min-height:64px;">' +
        '<div style="flex:1; min-width:0;">' +
          '<div style="font-size:14.5px; font-weight:600; color:#0d1b2e; line-height:1.35; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(r.n) + '</div>' +
          '<div style="margin-top:5px; display:flex; align-items:center; gap:6px;">' +
            '<span style="font-size:11px; color:#1a3a5c; background:#eaf0f8; border-radius:4px; padding:2px 6px; white-space:nowrap;">' + esc(r.o) + '</span>' +
            '<span style="font-size:11px; color:#6b7a95; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(r.c) + '</span>' +
          '</div>' +
        '</div>' +
        '<div style="flex:0 0 auto; text-align:right;">' +
          '<div style="font-size:17px; font-weight:700; color:' + (r.tot > 0 ? '#0d1b2e' : '#c3cbd8') + '; font-variant-numeric:tabular-nums; line-height:1;">' + (r.tot > 0 ? num(r.tot) : '—') + '</div>' +
          '<div style="font-size:11px; color:#6b7a95; margin-top:4px;">' + (r.tot > 0 ? '累计投资（亿）' : (r.pn > 0 ? r.pn + ' 条进展' : '暂无台账')) + '</div>' +
        '</div>' +
        '<svg width="7" height="12" viewBox="0 0 7 12" fill="none" stroke="#c3cbd8" stroke-width="1.8" stroke-linecap="round" style="flex:0 0 auto;"><path d="M1 1 6 6 1 11"></path></svg>' +
      '</div>';
    });

    if (rows.length > shown.length) {
      h += '<div data-act="more" style="min-height:44px; display:flex; align-items:center; justify-content:center; font-size:13px; color:#1a3a5c; font-weight:500; background:#fff; border-radius:13px; border:1px solid #e4e8ee;">加载更多（还有 ' + (rows.length - shown.length) + ' 家）</div>';
    }
    if (!rows.length) {
      h += '<div style="padding:56px 20px; text-align:center;">' +
        '<div style="font-size:14px; color:#6b7a95; font-weight:500;">未找到匹配机构</div>' +
        '<div style="font-size:12px; color:#9aa5b5; margin-top:7px; line-height:1.6;">换个关键词，或清除负责人 / 类型筛选</div></div>';
    }
    return h + '</div>';
  }

  function filterBtn(label, on, act) {
    return '<div data-act="' + act + '" style="flex:1; min-height:36px; display:flex; align-items:center; justify-content:space-between; gap:6px; padding:0 12px; border-radius:10px; font-size:12.5px; font-weight:500; background:' +
      (on ? '#0d1b2e' : '#fff') + '; color:' + (on ? '#fff' : '#6b7a95') + '; border:1px solid ' + (on ? '#0d1b2e' : '#e4e8ee') + ';">' +
      '<span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(label) + '</span>' +
      '<svg width="9" height="6" viewBox="0 0 9 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" style="flex:0 0 auto;"><path d="M1 1.4 4.5 4.8 8 1.4"></path></svg></div>';
  }

  /* ---------- 机构画像 · 详情 ---------- */
  function viewDetail() {
    var rec = data().filter(function (r) { return r.n === S.sel; })[0];
    if (!rec) return '';
    var cr = rec.cr, hasQuota = !!(cr && cr.t != null), hasApproval = !!(cr && cr.ap);
    var used = hasQuota && cr.t > 0 ? (cr.t - cr.r) / cr.t * 100 : 0;
    var byYear = {}; (rec.pf || []).forEach(function (y) { byYear[String(y.y)] = y.tot; });

    var h = '<div style="animation:mPageIn .22s ease both; padding-bottom:20px;">' +
      '<div style="position:sticky; top:0; z-index:30; background:linear-gradient(150deg,#0d1b2e 0%,#1a3a5c 72%,#12314c 100%); padding:2px 18px 15px; border-radius:0 0 20px 20px;">' +
        '<div data-act="back" style="min-height:36px; display:flex; align-items:center; gap:5px; color:#a9c6e2; font-size:13.5px; font-weight:500;">' +
          '<svg width="7" height="12" viewBox="0 0 7 12" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M6 1 1 6l5 5"></path></svg><span>机构列表</span></div>' +
        '<div style="margin-top:3px; display:flex; align-items:baseline; gap:8px; flex-wrap:wrap;">' +
          '<div style="font-size:19px; font-weight:700; color:#fff; line-height:1.3; text-wrap:pretty;">' + esc(rec.n) + '</div>' +
          '<div style="display:flex; align-items:center; gap:6px; flex:0 0 auto;">' +
            '<span style="font-size:10.5px; color:#d5e5f3; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.2); border-radius:4px; padding:2.5px 7px; white-space:nowrap;">' + esc(rec.o) + '</span>' +
            '<span style="font-size:10.5px; color:#c5dcef; white-space:nowrap;">' + esc(rec.c) + '</span>' +
          '</div>' +
        '</div>' +
        '<div style="margin-top:12px; display:flex; gap:8px;">';
    var yrs = [String(META.progYear), String(META.progYear - 1), String(META.progYear - 2)];
    yrs.forEach(function (y) {
      var v = byYear[y], has = v != null && v > 0;
      h += '<div style="flex:1; background:rgba(255,255,255,.11); border-radius:9px; padding:8px 10px;">' +
        '<div style="font-size:10.5px; color:#c5dcef; letter-spacing:.3px;">' + y + ' 年投资</div>' +
        '<div style="font-size:17px; font-weight:700; color:' + (has ? '#fff' : 'rgba(255,255,255,.42)') + '; font-variant-numeric:tabular-nums; margin-top:3px; line-height:1;">' + (has ? num(v) : '—') + '</div></div>';
    });
    h += '</div></div><div style="padding:16px 18px 0; display:flex; flex-direction:column; gap:14px;">';

    /* 最近进展 */
    var pr = rec.pr || [], list = S.prAll ? pr : pr.slice(0, 2);
    h += '<div><div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px;">' +
      '<div style="' + H2 + '">最近进展</div><div style="' + SUB + '">' + (pr.length ? '更新至 ' + fmtDate(pr[0].d) : '') + '</div></div>' +
      '<div style="display:flex; flex-direction:column; gap:8px;">';
    list.forEach(function (p, i) {
      var open = !!S.openPr[i], longTxt = String(p.t || '').length > 60;
      h += '<div data-act="pr:' + i + '" style="' + CARD + ' padding:11px 13px;">' +
        '<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">' +
          '<div style="font-size:11px; font-weight:600; color:#1a3a5c; background:#eaf0f8; border-radius:4px; padding:2.5px 7px; font-variant-numeric:tabular-nums;">' + esc(p.d) + '</div>' +
          '<div style="' + SUB + '">' + (longTxt ? (open ? '收起' : '展开') : '') + '</div></div>' +
        '<div style="font-size:12.5px; color:#33405a; line-height:1.7; text-wrap:pretty; overflow:hidden; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:' + (open ? 99 : 4) + ';">' + esc(p.t) + '</div></div>';
    });
    if (pr.length > 2) {
      h += '<div data-act="prAll" style="min-height:42px; display:flex; align-items:center; justify-content:center; gap:5px; background:#fff; border-radius:13px; border:1px solid #e4e8ee; font-size:12.5px; font-weight:500; color:#1a3a5c;"><span>' +
        (S.prAll ? '收起进展' : '展开其余 ' + (pr.length - 2) + ' 条进展') + '</span>' + fold(S.prAll) + '</div>';
    }
    if (!pr.length) h += '<div style="' + CARD + ' padding:26px; text-align:center; font-size:12.5px; color:#6b7a95;">暂无进展记录</div>';
    h += '</div></div>';

    /* 各年投资画像 */
    h += '<div><div style="display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px;">' +
      '<div style="' + H2 + '">各年投资画像</div><div style="' + SUB + '">联动投资台账</div></div>';
    (rec.pf || []).forEach(function (y) {
      var rws = y.rows.map(function (r) {
        return { a: r.a, s: num(r.s), p: r.p.toFixed(1) + '%', sp: r.sp != null ? r.sp + 'bp' : '—', spFg: r.sp != null ? '#1a3a5c' : '#c3cbd8', bg: '#fff', fw: '500' };
      });
      rws.push({ a: '合计', s: num(y.tot), p: '100.0%', sp: y.avg != null ? y.avg + 'bp' : '—', spFg: y.avg != null ? '#0d1b2e' : '#c3cbd8', bg: '#f7f9fc', fw: '700' });
      h += '<div style="' + CARD + ' overflow:hidden; margin-bottom:9px;">' +
        '<div style="display:flex; align-items:center; justify-content:space-between; padding:10px 13px; background:#f7f9fc; border-bottom:1px solid #eef1f6;">' +
          '<div style="font-size:13.5px; font-weight:700; color:#1a3a5c; font-variant-numeric:tabular-nums;">' + y.y + ' 年</div>' +
          '<div style="' + SUB + '">' + num(y.tot) + ' 亿 · ' + y.rows.length + ' 类' + (y.avg != null ? ' · 均利差 ' + y.avg + 'bp' : '') + '</div></div>' +
        '<div class="noscroll" style="overflow-x:auto; -webkit-overflow-scrolling:touch;"><div style="width:max-content; min-width:100%;">' +
          '<div style="display:flex; align-items:center; background:#fbfcfe; border-bottom:1px solid #eef1f6;">' +
            '<div style="position:sticky; left:0; z-index:2; flex:0 0 132px; padding:7px 8px 7px 13px; background:#fbfcfe; box-shadow:7px 0 8px -7px rgba(13,27,46,.22); font-size:10.5px; color:#6b7a95; letter-spacing:.3px;">资产类型</div>' +
            '<div style="flex:0 0 88px; text-align:right; padding:7px; font-size:10.5px; color:#6b7a95;">规模(亿)</div>' +
            '<div style="flex:0 0 72px; text-align:right; padding:7px; font-size:10.5px; color:#6b7a95;">占比</div>' +
            '<div style="flex:0 0 92px; text-align:right; padding:7px 13px 7px 7px; font-size:10.5px; color:#6b7a95;">平均利差</div></div>';
      rws.forEach(function (r) {
        h += '<div style="display:flex; align-items:center; border-bottom:1px solid #f2f5f9; background:' + r.bg + ';">' +
          '<div style="position:sticky; left:0; z-index:2; flex:0 0 132px; padding:9px 8px 9px 13px; background:' + r.bg + '; box-shadow:7px 0 8px -7px rgba(13,27,46,.22); font-size:12.5px; color:#0d1b2e; font-weight:' + r.fw + '; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(r.a) + '</div>' +
          '<div style="flex:0 0 88px; text-align:right; padding:9px 7px; font-size:12.5px; font-weight:600; color:#0d1b2e; font-variant-numeric:tabular-nums;">' + r.s + '</div>' +
          '<div style="flex:0 0 72px; text-align:right; padding:9px 7px; font-size:11.5px; color:#6b7a95; font-variant-numeric:tabular-nums;">' + r.p + '</div>' +
          '<div style="flex:0 0 92px; text-align:right; padding:9px 13px 9px 7px; font-size:11.5px; color:' + r.spFg + '; font-variant-numeric:tabular-nums; font-weight:500;">' + r.sp + '</div></div>';
      });
      h += '</div></div>' +
        '<div style="padding:6px 13px 8px; font-size:10.5px; color:#8a96ab; display:flex; align-items:center; gap:4px;">' +
        '<svg width="11" height="8" viewBox="0 0 11 8" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M1 4h8"></path><path d="M6.6 1.4 9.6 4l-3 2.6"></path></svg>' +
        '<span>左右滑动查看占比与利差</span></div></div>';
    });
    if (!(rec.pf || []).length) h += '<div style="' + CARD + ' padding:26px; text-align:center; font-size:12.5px; color:#9aa5b5;">暂无台账投资记录</div>';
    else h += '<div style="' + SUB + ' line-height:1.65; padding:0 2px;">利差口径：仅统计优先A / 优先级 / 优先A1 / 优先A2 · 规模含全部档位</div>';
    h += '</div>';

    /* 授信统计 */
    h += '<div><div style="' + H2 + ' margin-bottom:8px;">授信统计</div><div style="' + CARD + ' padding:13px;">';
    if (hasQuota) {
      h += '<div><div style="display:flex; gap:9px;">' +
        '<div style="flex:1; background:#f7f9fc; border-radius:9px; padding:10px 11px;"><div style="' + SUB + '">授信总额</div>' +
          '<div style="font-size:19px; font-weight:700; color:#0d1b2e; font-variant-numeric:tabular-nums; margin-top:4px; line-height:1;">' + num(cr.t) + '</div></div>' +
        '<div style="flex:1; background:#f1f8f4; border-radius:9px; padding:10px 11px;"><div style="font-size:11px; color:#5f8a72;">剩余授信</div>' +
          '<div style="font-size:19px; font-weight:700; color:#1c7a4f; font-variant-numeric:tabular-nums; margin-top:4px; line-height:1;">' + num(cr.r) + '</div></div></div>' +
        '<div style="margin-top:11px; height:6px; border-radius:3px; background:#e9edf3; overflow:hidden;">' +
          '<div style="height:100%; width:' + used.toFixed(1) + '%; background:linear-gradient(90deg,#1a3a5c,#2f6fb0); border-radius:3px;"></div></div>' +
        '<div style="margin-top:6px; ' + SUB + '">已用 ' + num(cr.t - cr.r) + ' 亿（' + used.toFixed(0) + '%）</div></div>';
    } else if (hasApproval) {
      h += '<div><div style="' + SUB + ' margin-bottom:5px;">批复情况</div>' +
        '<div style="font-size:12.5px; color:#0d1b2e; line-height:1.65; text-wrap:pretty;">' + esc(cr.ap + (cr.q ? ' · ' + cr.q : '')) + '</div></div>';
    } else {
      h += '<div style="padding:8px 0; text-align:center; font-size:12.5px; color:#6b7a95;">暂无授信数据</div>';
    }
    h += '</div></div>';

    /* 联系人 */
    h += '<div><div style="' + H2 + ' margin-bottom:8px;">联系人</div>' +
      '<div style="' + CARD + ' padding:11px 13px; display:flex; flex-wrap:wrap; gap:7px;">';
    if ((rec.ct || []).length) {
      rec.ct.forEach(function (c) {
        h += '<div style="display:flex; align-items:baseline; gap:5px; background:#f4f7fb; border-radius:7px; padding:6px 10px;">' +
          '<span style="font-size:13px; color:#0d1b2e; font-weight:600; white-space:nowrap;">' + esc(c.name) + '</span>' +
          '<span style="' + SUB + ' white-space:nowrap;">' + esc(c.dept || '') + '</span></div>';
      });
    } else {
      h += '<div style="width:100%; padding:4px 0; text-align:center; font-size:12.5px; color:#6b7a95;">暂无联系人</div>';
    }
    return h + '</div></div></div></div>';
  }

  /* ---------- 资产大盘 ---------- */
  function viewAsset() {
    var isCash = S.assetSide === 'cash', side = isCash ? ASSET.cash : ASSET.consume;
    var h = '<div><div style="' + STICKY + '">' +
      '<div style="padding:0 20px; display:flex; align-items:baseline; justify-content:space-between;">' +
        '<div style="font-size:23px; font-weight:700; color:#0d1b2e; letter-spacing:.5px;">消金资产</div>' +
        '<div style="' + SUB + ' letter-spacing:.2px;">统计日 ' + META.assetDate + '</div></div>' +
      '<div style="padding:0 20px; margin-top:11px; display:flex; gap:6px;">' +
        segBtn('消费贷', !isCash, 'side:consume') + segBtn('现金贷', isCash, 'side:cash') +
      '</div></div>' +
      '<div style="padding:2px 20px 18px;"><div style="display:flex; gap:8px;">';
    ASSET.kpis.forEach(function (k) {
      h += '<div style="flex:1; ' + CARD + ' padding:11px 10px;">' +
        '<div style="' + SUB + '">' + k.label + '</div>' +
        '<div style="margin-top:5px; display:flex; align-items:baseline; gap:2px;">' +
          '<span style="font-size:19px; font-weight:700; color:#0d1b2e; font-variant-numeric:tabular-nums; line-height:1;">' + k.val + '</span>' +
          '<span style="font-size:10.5px; color:#6b7a95;">亿</span></div>' +
        '<div style="margin-top:6px; font-size:11px; font-weight:600; color:' + dColor(k.d) + '; font-variant-numeric:tabular-nums;">' + dText(k.d, k.p) + '</div></div>';
    });
    h += '</div><div style="margin-top:16px; display:flex; align-items:baseline; justify-content:space-between;">' +
      '<div style="' + H2 + '">' + (isCash ? '现金贷资产及资金结构' : '消费贷资产及资金结构') + '</div>' +
      '<div style="' + SUB + '">' + side.note + '</div></div>';
    side.groups.forEach(function (g) {
      h += '<div style="margin-top:9px; ' + CARD + ' padding:12px 14px 6px;">' +
        '<div style="font-size:11.5px; font-weight:600; color:#1a3a5c; letter-spacing:.3px; margin-bottom:10px;">' + g.title + '</div>';
      g.rows.forEach(function (r) {
        h += barRow(esc(r.label), r.amount, r.w.toFixed(2) + '%', '占比 ' + r.share, dText(r.d, r.p), dColor(r.d), r.w >= 50 ? '#1a3a5c' : '#2f6fb0');
      });
      h += '</div>';
    });
    h += caliberBox('caliber', S.caliber, [
      '消费贷 = 白条消费 + 分分卡。 现金贷 = 金条 + 白取。 消金资产合计 = 消费贷 + 现金贷。',
      '现金贷助贷合计 = 金条助贷 + 白取助贷100% + 白取助贷联合贷。',
      '白条侧、金条侧均严格对比各自最新统计日前第 5 天；现金贷及消金资产合计为按来源最新可用统计日汇总的混合统计日口径。',
      '白条消费 / 分分卡 / 白取：统计日 2026-08-14 · 对比 2026-08-09。金条：统计日 2026-08-13 · 对比 2026-08-08。'
    ]);
    return h + '</div></div>';
  }

  function segBtn(label, on, act) {
    return '<div data-act="' + act + '" style="flex:1; min-height:34px; display:flex; align-items:center; justify-content:center; border-radius:9px; font-size:13px; font-weight:600; background:' +
      (on ? '#0d1b2e' : '#fff') + '; color:' + (on ? '#fff' : '#6b7a95') + '; border:1px solid ' + (on ? '#0d1b2e' : '#e4e8ee') + ';">' + label + '</div>';
  }
  function caliberBox(act, open, lines) {
    var h = '<div data-act="' + act + '" style="margin-top:14px; ' + CARD + ' padding:12px 14px;">' +
      '<div style="display:flex; align-items:center; justify-content:space-between;">' +
      '<span style="font-size:12.5px; font-weight:600; color:#1a3a5c;">数据口径</span>' + fold(open) + '</div>';
    if (open) {
      h += '<div style="margin-top:9px; display:flex; flex-direction:column; gap:7px;">';
      lines.forEach(function (t) { h += '<div style="font-size:11.5px; color:#4a5a75; line-height:1.7; text-wrap:pretty;">' + t + '</div>'; });
      h += '</div>';
    }
    return h + '</div>';
  }

  /* ---------- 同业发行 ---------- */
  function viewPeer() {
    var h = '<div><div style="' + STICKY + '">' +
      '<div style="padding:0 20px; display:flex; align-items:baseline; justify-content:space-between;">' +
        '<div style="font-size:23px; font-weight:700; color:#0d1b2e; letter-spacing:.5px;">同业发行</div>' +
        '<div style="' + SUB + ' letter-spacing:.2px;">更新至 ' + META.peerDate + '</div></div>' +
      '<div class="noscroll" style="margin-top:11px; padding:0 20px; display:flex; gap:7px; overflow-x:auto;">' +
        pill('发行概览', S.peerView === 'overview', 'pv:overview') +
        pill('信托渠道', S.peerView === 'trust', 'pv:trust') +
        // Top N 取实际卡片数,电脑端 peer_issuance_panel.TOP_N 调整时手机端自动跟随
        pill('资产 Top ' + PEER.top.length, S.peerView === 'top', 'pv:top') +
      '</div></div><div style="padding:2px 20px 18px;">';

    if (S.peerView === 'overview') {
      h += '<div style="margin-top:4px; ' + H2 + '">发行规模</div><div style="margin-top:9px; ' + CARD + ' padding:13px 14px 4px;">';
      PEER.groups.forEach(function (g) {
        var c = CG[g.label] || '#2f6fb0';
        h += barRow('<span style="display:inline-flex; align-items:center; gap:6px;"><span style="width:8px; height:8px; border-radius:2px; background:' + c + ';"></span>' + esc(g.label) + '</span>',
          g.amt, g.w.toFixed(2) + '%', '去年同期 ' + g.ly, dText(g.d, g.p), dColor(g.d), c);
      });
      h += '</div><div style="margin-top:7px; ' + SUB + ' line-height:1.65;">按基础资产归并至资产集团；未命中归并规则的列为「其他」</div>';
    }

    function trustScope() {
      var list = PEER.trust || [];
      var merged = list.length && /^其他/.test(list[list.length - 1].name || '');
      return merged ? ('前 ' + (list.length - 1) + ' 家 + 其他') : ('前 ' + list.length + ' 家');
    }

    if (S.peerView === 'trust') {
      h += '<div style="margin-top:4px; display:flex; align-items:baseline; justify-content:space-between;">' +
        // 渠道数取实际数据(电脑端 TRUST_TOP_N),末位是否为合并项也据实判断,不写死
        '<div style="' + H2 + '">信托渠道分布</div><div style="' + SUB + '">' + trustScope() + '</div></div>' +
        '<div style="margin-top:9px; display:flex; flex-direction:column; gap:9px;">';
      PEER.trust.forEach(function (t) {
        h += '<div style="' + CARD + ' padding:12px 14px;">' +
          '<div style="display:flex; align-items:baseline; justify-content:space-between; gap:8px;">' +
            '<span style="font-size:14px; font-weight:600; color:#0d1b2e;">' + esc(t.name) + '</span>' +
            '<span style="font-size:13px; font-weight:700; color:#0d1b2e; font-variant-numeric:tabular-nums; white-space:nowrap;">' + t.total + '</span></div>' +
          '<div style="margin-top:8px; display:flex; height:8px; border-radius:4px; overflow:hidden; background:#eef1f6;">';
        t.segs.forEach(function (s) { h += '<div style="height:100%; width:' + s[2] + '%; background:' + (CG[s[0]] || '#98a1ad') + ';"></div>'; });
        h += '</div><div style="margin-top:9px; display:flex; flex-wrap:wrap; gap:6px;">';
        t.segs.forEach(function (s) {
          h += '<div style="display:flex; align-items:center; gap:5px; background:#f4f7fb; border-radius:6px; padding:4px 8px;">' +
            '<span style="width:7px; height:7px; border-radius:2px; background:' + (CG[s[0]] || '#98a1ad') + '; flex:0 0 auto;"></span>' +
            '<span style="font-size:11px; color:#33405a; white-space:nowrap; font-variant-numeric:tabular-nums;">' + esc(s[0]) + ' ' + s[1] + ' 亿（' + s[2] + '%）</span></div>';
        });
        h += '</div></div>';
      });
      h += '</div><div style="margin-top:7px; ' + SUB + ' line-height:1.65;">仅统计原始权益人名称含「信托」的渠道；条内分段为各资产集团在该渠道内的占比</div>';
    }

    if (S.peerView === 'top') {
      h += '<div style="margin-top:4px; display:flex; align-items:baseline; justify-content:space-between;">' +
        '<div style="' + H2 + '">基础资产发行 Top ' + PEER.top.length + '</div><div style="' + SUB + '">点击展开渠道</div></div>' +
        '<div style="margin-top:9px; display:flex; flex-direction:column; gap:8px;">';
      PEER.top.forEach(function (c, i) {
        var open = !!S.peerOpen[i];
        h += '<div data-act="pt:' + i + '" style="' + CARD + ' padding:12px 14px;">' +
          '<div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">' +
            '<div style="min-width:0; flex:1;">' +
              '<div style="font-size:14px; font-weight:600; color:#0d1b2e; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(c.name) + '</div>' +
              '<div style="margin-top:4px; ' + SUB + '">' + c.cat + '</div></div>' +
            '<div style="flex:0 0 auto; text-align:right;">' +
              '<div style="font-size:16px; font-weight:700; color:#0d1b2e; font-variant-numeric:tabular-nums; line-height:1;">' + c.amt + '</div>' +
              '<div style="margin-top:4px; ' + SUB + ' font-variant-numeric:tabular-nums;">' + c.terms + '</div></div>' +
            fold(open) + '</div>';
        if (open) {
          h += '<div style="margin-top:11px; padding-top:10px; border-top:1px solid #f2f5f9;">';
          c.rows.forEach(function (r) {
            h += '<div style="margin-bottom:11px;">' +
              '<div style="display:flex; align-items:baseline; justify-content:space-between; gap:8px;">' +
                '<span style="font-size:12.5px; color:#0d1b2e; font-weight:500;">' + esc(r[0]) + '</span>' +
                '<span style="font-size:12.5px; font-weight:600; color:#0d1b2e; font-variant-numeric:tabular-nums; white-space:nowrap;">' + r[1] + '</span></div>' +
              '<div style="margin-top:5px; height:5px; border-radius:3px; background:#eef1f6; overflow:hidden;">' +
                '<div style="height:100%; width:' + r[2] + '%; background:#2f6fb0; border-radius:3px;"></div></div>' +
              '<div style="margin-top:4px; font-size:11px; color:' + dColor(r[4]) + '; font-variant-numeric:tabular-nums;">' + r[3] + '</div></div>';
          });
          h += '</div>';
        }
        h += '</div>';
      });
      h += '</div>';
    }

    h += caliberBox('pcaliber', S.peerCaliber, [
      '剔除京东系 = 原始权益人或基础资产含「京东」（并集口径，覆盖走信托通道发行的京东资产）；统计范围为全市场互联网金融 ABS/ABN 发行。',
      '同比 = 2025 年簿记时间 ≤ 2026 最新簿记日前一年的同期窗口；信托渠道仅统计名称含「信托」的原始权益人，按基础资产归并至六类资产集团，未命中规则的资产归入「其他」。',
      '2026 累计发行 3,016 亿 / 364 期，已剔除京东系 66 期 / 675 亿；同比窗口 2025-01-01 ~ 2025-08-14。'
    ]);
    return h + '</div></div>';
  }

  /* ---------- 占位 ---------- */
  function viewSoon() {
    return '<div style="padding:0 20px;">' +
      '<div style="padding:4px 0 0; font-size:23px; font-weight:700; color:#0d1b2e; letter-spacing:.5px;">机构画像</div>' +
      '<div style="margin-top:120px; text-align:center;">' +
        '<div style="width:56px; height:56px; margin:0 auto; border-radius:28px; background:#e7ebf2; display:flex; align-items:center; justify-content:center;">' +
          '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8a96ab" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5.4l3.4 2"></path></svg></div>' +
        '<div style="margin-top:16px; font-size:14.5px; font-weight:600; color:#4a5a75;">这个面板还没加工</div>' +
        '<div style="margin-top:8px; font-size:12.5px; color:#9aa5b5; line-height:1.7;">机构统计 / 授信总额度 · 待加工<br>请在电脑端查看完整面板</div>' +
        '<div data-act="sub:quick" style="margin:18px auto 0; max-width:180px; min-height:42px; display:flex; align-items:center; justify-content:center; background:#fff; border:1px solid #e4e8ee; border-radius:12px; font-size:13px; font-weight:500; color:#1a3a5c;">返回机构速查</div>' +
      '</div></div>';
  }

  /* ---------- 顶部 Tab + 弹层 ---------- */
  function tabBar() {
    var items = [
      ['progress', '机构画像', '<circle cx="11" cy="7" r="3.4"></circle><path d="M4.5 18.5c0-3.6 2.9-5.8 6.5-5.8s6.5 2.2 6.5 5.8"></path>'],
      ['asset', '资产大盘', '<path d="M3.5 18.5h15"></path><rect x="4.5" y="10" width="3.6" height="6"></rect><rect x="9.7" y="6" width="3.6" height="10"></rect><rect x="14.9" y="12.5" width="3.6" height="3.5"></rect>'],
      ['peer', '同业发行', '<path d="M3.5 14.5 8 9.5l3.6 3.2L18.5 6"></path><path d="M14.4 6h4.1v4"></path>']
    ];
    // 顶部标签栏:安全区留白包在栏内,图标与文字横向并排,选中态用底部 2px 下划线
    var h = '<div style="flex:0 0 auto; background:#fff; border-bottom:1px solid #e2e6ee; box-shadow:0 1px 3px rgba(13,27,46,.05);">' +
      '<div style="height:env(safe-area-inset-top, 0px);"></div>' +
      '<div style="display:flex; padding:0 10px;">';
    items.forEach(function (it) {
      var on = S.tab === it[0], c = on ? '#0d1b2e' : '#98a3b5';
      h += '<div data-act="tab:' + it[0] + '" style="flex:1; min-height:46px; display:flex; align-items:center; justify-content:center; gap:5px; color:' + c + '; border-bottom:2px solid ' + (on ? '#0d1b2e' : 'transparent') + ';">' +
        '<svg width="17" height="17" viewBox="0 0 22 22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 auto;">' + it[2] + '</svg>' +
        '<span style="font-size:13px; font-weight:' + (on ? '700' : '500') + '; letter-spacing:.2px; white-space:nowrap;">' + it[1] + '</span></div>';
    });
    return h + '</div></div>';
  }

  function sheet() {
    if (!S.sheet) return '';
    var kind = S.sheet, all = data();
    var cur = kind === 'owner' ? S.owner : S.cat;
    var base = all.filter(function (r) { return kind === 'owner' ? (!S.cat || r.c === S.cat) : (!S.owner || r.o === S.owner); });
    var vals = [];
    all.forEach(function (r) { var v = kind === 'owner' ? r.o : r.c; if (v && vals.indexOf(v) < 0) vals.push(v); });
    vals.sort();
    var opts = [{ label: '全部', value: '', count: base.length }].concat(vals.map(function (v) {
      return { label: v, value: v, count: base.filter(function (r) { return (kind === 'owner' ? r.o : r.c) === v; }).length };
    }));
    var h = '<div style="position:absolute; inset:0; z-index:120; display:flex; flex-direction:column; justify-content:flex-end;">' +
      '<div data-act="sheet:close" style="position:absolute; inset:0; background:rgba(9,17,30,.42); animation:mFadeIn .18s ease both;"></div>' +
      '<div style="position:relative; background:#fff; border-radius:20px 20px 0 0; padding:10px 0 calc(20px + env(safe-area-inset-bottom, 0px)); animation:mSheetUp .26s cubic-bezier(.22,.9,.3,1) both; max-height:70%; display:flex; flex-direction:column;">' +
      '<div style="width:38px; height:4px; border-radius:2px; background:#dbe1ea; margin:0 auto 6px;"></div>' +
      '<div style="padding:6px 20px 10px; display:flex; align-items:center; justify-content:space-between;">' +
        '<div style="font-size:15px; font-weight:700; color:#0d1b2e;">' + (kind === 'owner' ? '按负责人筛选' : '按机构类型筛选') + '</div>' +
        '<div data-act="sheet:close" style="font-size:13px; color:#1a3a5c; font-weight:500; min-height:32px; display:flex; align-items:center; padding-left:12px;">完成</div></div>' +
      '<div class="noscroll" style="overflow-y:auto; padding:0 20px;">';
    opts.forEach(function (o) {
      var on = o.value === cur;
      h += '<div data-act="pick:' + kind + ':' + esc(o.value) + '" style="min-height:46px; display:flex; align-items:center; justify-content:space-between; gap:10px; border-bottom:1px solid #f2f5f9;">' +
        '<span style="font-size:14px; color:' + (on ? '#1a3a5c' : '#33405a') + '; font-weight:' + (on ? '700' : '400') + ';">' + esc(o.label) + '</span>' +
        '<span style="font-size:11.5px; color:#6b7a95; font-variant-numeric:tabular-nums;">' + o.count + ' 家</span></div>';
    });
    return h + '</div></div></div>';
  }

  /* ---------- render / events ---------- */
  var root, scroller;

  function body() {
    if (S.tab === 'asset') return viewAsset();
    if (S.tab === 'peer') return viewPeer();
    if (S.sel) return viewDetail();
    if (S.sub !== 'quick') return viewSoon();
    return viewQuickList();
  }

  function render(keepScroll) {
    var top = keepScroll && scroller ? scroller.scrollTop : 0;
    root.innerHTML =
      '<div style="position:relative; width:100%; height:100%; background:#f2f4f8; overflow:hidden; display:flex; flex-direction:column;">' +
        tabBar() +
        '<div class="noscroll" id="m-scroll" style="flex:1; overflow-y:auto; overscroll-behavior:contain; position:relative; -webkit-overflow-scrolling:touch;">' + body() +
          '<div style="height:calc(14px + env(safe-area-inset-bottom, 0px));"></div></div>' +
        sheet() +
      '</div>';
    scroller = document.getElementById('m-scroll');
    if (keepScroll && scroller) scroller.scrollTop = top;
    var inp = document.getElementById('m-q');
    if (inp) {
      var composing = false;
      inp.addEventListener('compositionstart', function () { composing = true; });
      inp.addEventListener('compositionend', function () { composing = false; S.q = inp.value; S.limit = 24; renderList(); });
      inp.addEventListener('input', function (e) {
        if (composing || (e && e.isComposing)) return;
        S.q = inp.value; S.limit = 24; renderList();
      });
      if (S.focusQ) { S.focusQ = false; inp.focus(); }
    }
  }

  // 只重绘结果区，输入框节点保持不变（不打断中文输入法、不丢光标）
  function renderList() {
    var host = document.getElementById('m-list');
    if (!host) { render(true); return; }
    host.innerHTML = quickListBody();
  }

  function act(a) {
    var p = a.split(':');
    switch (p[0]) {
      case 'tab': S.tab = p[1]; S.sel = null; S.sub = 'quick'; render(); break;
      case 'sub': S.sub = p[1]; S.sel = null; render(); break;
      case 'open': S.sel = a.slice(5); S.openPr = {}; S.prAll = false; render(); break;
      case 'back': S.sel = null; render(); break;
      case 'more': S.limit += 30; render(true); break;
      case 'q': S.q = ''; S.limit = 24; S.focusQ = true; render(); break;
      case 'sheet': S.sheet = p[1] === 'close' ? null : p[1]; render(true); break;
      case 'pick': {
        var v = p.slice(2).join(':');
        if (p[1] === 'owner') S.owner = v; else S.cat = v;
        S.sheet = null; S.limit = 24; render(); break;
      }
      case 'pr': S.openPr[p[1]] = !S.openPr[p[1]]; render(true); break;
      case 'prAll': S.prAll = !S.prAll; render(true); break;
      case 'side': S.assetSide = p[1]; render(true); break;
      case 'caliber': S.caliber = !S.caliber; render(true); break;
      case 'pv': S.peerView = p[1]; S.peerOpen = {}; render(true); break;
      case 'pt': S.peerOpen[p[1]] = !S.peerOpen[p[1]]; render(true); break;
      case 'pcaliber': S.peerCaliber = !S.peerCaliber; render(true); break;
    }
  }

  window.ABS_MOBILE_MOUNT = function (el) {
    root = el;
    root.addEventListener('click', function (e) {
      var n = e.target;
      while (n && n !== root) {
        if (n.getAttribute && n.getAttribute('data-act')) { act(n.getAttribute('data-act')); return; }
        n = n.parentNode;
      }
    });
    render();
    if (!data().length) {
      var t = setInterval(function () { if (data().length) { clearInterval(t); render(); } }, 150);
      setTimeout(function () { clearInterval(t); }, 8000);
    }
  };
})();

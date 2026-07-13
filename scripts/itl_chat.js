/* ═══ 投资台账 · 智能问答（本地语义解析，离线运行，命名空间 ITLChat）═══
   把自然语言解析成结构化筛选规格 spec，本地精确计算，联动 window.ITL 面板。
   不联网、不外发数据。词表来自内嵌的 window.ITL_DATA。 */
(function () {
  var FIELD_LABEL = { asset: '资产类型', proj: '项目', mgr: '计划管理人', underwriter: '联席承销商', custodian: '托管行', inst: '认购机构', rating: '评级', layer: '分层', year: '年份' };
  var CHIP_FIELDS = ['asset', 'layer', 'rating'];
  var KW_FIELDS = ['mgr', 'underwriter', 'custodian', 'inst'];
  var ENTITY_FIELDS = ['inst', 'mgr', 'underwriter', 'custodian', 'asset', 'rating', 'layer'];
  var PANEL_DIMS = ['inst', 'mgr', 'underwriter', 'custodian', 'asset', 'rating', 'layer'];

  var METRIC_LABEL = { share: '认购份额', count: '记录数', proj: '项目数', cost: '平均成本', spread: '平均利差' };
  var METRIC_UNIT = { share: '亿', count: '笔', proj: '个', cost: '', spread: '' };
  // 注：台账的规模J列是项目级数值被复制到每一行（数据加工副产物），任何加总都会虚增；
  // 所有「规模/投资规模/管理规模」类问题一律按认购份额V列合计回答（share）。

  var CN_NUM = { '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12 };

  // 字段线索词：短/歧义词条（如评级「无」「A」）只有在句中出现对应线索时才允许匹配，避免误命中「无法」「无所谓」里的「无」
  var FIELD_CUE = { rating: /评级|级别|评为/, layer: /分层|层级/, asset: /资产|类型|品种/, inst: /机构|投资人/, mgr: /管理人/, underwriter: /承销/, custodian: /托管/ };

  var DATA = [], VOCAB = [], VOCAB_BY_FIELD = {}, COUNTS = {}, DATA_YEAR = 2026;
  var lastSpec = null;

  // ── init vocab ──
  // 数据源优先级：ITL_ALL_DATA（多年份合并语料，跨 Tab 问答用）
  //             → window.ITL.getData()（旧版单年份独立预览，向后兼容）
  //             → window.ITL_DATA（更早版本兜底）
  function initVocab() {
    DATA = window.ITL_ALL_DATA || ((window.ITL && window.ITL.getData) ? window.ITL.getData() : (window.ITL_DATA || []));
    ENTITY_FIELDS.forEach(function (f) { COUNTS[f] = new Map(); VOCAB_BY_FIELD[f] = new Map(); });
    DATA.forEach(function (r) {
      ENTITY_FIELDS.forEach(function (f) { var v = r[f]; if (v != null && v !== '') COUNTS[f].set(v, (COUNTS[f].get(v) || 0) + 1); });
    });
    // 业务当前年固定 2026（与 abs_common.py 的 2025→2026 纠错假设一致），"今年/去年"等相对时间词据此解析；
    // 不再用众数年份猜测——多年份合并后众数未必是 2026，猜测会导致"今年"语义漂移。
    DATA_YEAR = 2026;
    // candidate strings: full values + 括号去尾 base
    var seen = {};
    ENTITY_FIELDS.forEach(function (f) {
      COUNTS[f].forEach(function (c, val) {
        addCand(val, f, [val]);
        var base = val.replace(/[（(][^）)]*[)）]\s*$/, '').trim();
        if (base && base !== val && base.length >= 2) {
          var members = []; COUNTS[f].forEach(function (_c, v2) { if (v2 === base || v2.indexOf(base) === 0) members.push(v2); });
          addCand(base, f, members.length ? members : [val]);
        }
      });
    });
    VOCAB.sort(function (a, b) { return b.str.length - a.str.length; });
    function addCand(str, field, values) {
      var key = str + '@' + field; if (seen[key]) return; seen[key] = 1;
      VOCAB.push({ str: str, field: field, values: values });
    }
  }

  function countFor(field, values) { var n = 0; values.forEach(function (v) { n += (COUNTS[field].get(v) || 0); }); return n; }

  // ── year parsing（独立于 parseTime 的月份区间逻辑；台账目前覆盖 2024-2026）──
  // 支持单年("2024年")、范围("2024-2026年"/"2024到2026年"/"2024至2026年"/"2024~2026年")、
  // 列举("2024年和2026年"/"2024年、2025年")，统一返回年份字符串数组（升序去重）。
  function parseYears(q) {
    var range = q.match(/20(2[4-6])\s*(?:-|~|－|到|至)\s*20(2[4-6])\s*年/);
    if (range) {
      var y1 = 2000 + (+range[1]), y2 = 2000 + (+range[2]);
      if (y1 > y2) { var t = y1; y1 = y2; y2 = t; }
      var out = [];
      for (var y = y1; y <= y2; y++) out.push(String(y));
      return out;
    }
    var re = /20(2[4-6])\s*年/g, m, years = [];
    while ((m = re.exec(q))) { var yy = '20' + m[1]; if (years.indexOf(yy) < 0) years.push(yy); }
    years.sort();
    return years;
  }

  // ── time parsing ──
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function lastDay(y, m) { return new Date(y, m, 0).getDate(); }
  function monthRange(y, m1, m2) { return { from: y + '-' + pad(m1) + '-01', to: y + '-' + pad(m2) + '-' + pad(lastDay(y, m2)) }; }
  function parseMonthToken(q) {
    var m = q.match(/(\d{1,2})\s*月/); if (m) return +m[1];
    var cm = q.match(/([一二两三四五六七八九十]+)\s*月/); if (cm && CN_NUM[cm[1]]) return CN_NUM[cm[1]];
    return null;
  }
  function parseTime(q) {
    var y = DATA_YEAR;
    if (/去年/.test(q)) y = DATA_YEAR - 1;
    var rng = q.match(/(\d{1,2})\s*月.*?(?:到|至|-|~|—)\s*(\d{1,2})\s*月/);
    if (rng) {
      var m1 = +rng[1], m2 = +rng[2];
      if (m1 > m2) { var tmp = m1; m1 = m2; m2 = tmp; }   // 反序区间自动交换
      var r = monthRange(y, m1, m2); r.label = m1 + '–' + m2 + '月'; return r;
    }
    var qtr = q.match(/(?:第)?\s*([一二三四1-4])\s*季度/) || (/(Q[1-4])/i.test(q) ? [null, q.match(/Q([1-4])/i)[1]] : null);
    if (qtr) { var qn = CN_NUM[qtr[1]] || +qtr[1]; var r2 = monthRange(y, qn * 3 - 2, qn * 3); r2.label = qn + '季度'; return r2; }
    if (/上半年/.test(q)) { var a = monthRange(y, 1, 6); a.label = '上半年'; return a; }
    if (/下半年/.test(q)) { var b = monthRange(y, 7, 12); b.label = '下半年'; return b; }
    var rec = q.match(/(?:最近|近)\s*(\d+)\s*个?月/);
    if (rec) {
      var maxd = DATA.reduce(function (mx, r) { return (r.date && r.date > mx) ? r.date : mx; }, '');
      if (maxd) { var d = new Date(maxd); var from = new Date(d.getFullYear(), d.getMonth() - (+rec[1]) + 1, 1); return { from: from.getFullYear() + '-' + pad(from.getMonth() + 1) + '-01', to: maxd, label: '近' + rec[1] + '个月' }; }
    }
    var mo = parseMonthToken(q);
    if (mo) { var r3 = monthRange(y, mo, mo); r3.label = (y !== DATA_YEAR ? '去年' : '') + mo + '月'; return r3; }
    if (/今年|本年|全年/.test(q)) { return { from: y + '-01-01', to: y + '-12-31', label: '今年' }; }
    return null;
  }

  // ── metric / intent ──
  // 台账不存在的指标：直接告知而不是默默退化成份额（对财务工具，错的确定数字比报错更危险）
  var UNSUPPORTED_METRIC = /倍数|收益率|久期|余额|净值|回报/;

  function parseMetric(q) {
    if (/利差/.test(q)) return 'spread';
    if (/成本|利率|定价|价格/.test(q)) return 'cost';
    if (/规模|存量/.test(q)) return 'share';   // 规模类提问统一按认购份额V口径回答（见顶部注释）
    if (/笔数|多少笔|几笔|记录数|多少条|几条/.test(q)) return 'count';
    if (/项目数|几个项目|多少个项目|多少只|几只|多少个产品/.test(q)) return 'proj';
    if (/份额|投资|认购|申购|买了|买入|持有|投了|投多少|参与/.test(q)) return 'share';
    return null;
  }
  var NOUN_FIELD = [['资产', 'asset'], ['产品类型', 'asset'], ['认购机构', 'inst'], ['投资机构', 'inst'], ['投资人', 'inst'], ['机构', 'inst'], ['计划管理人', 'mgr'], ['管理人', 'mgr'], ['承销', 'underwriter'], ['托管', 'custodian'], ['评级', 'rating'], ['分层', 'layer'], ['层级', 'layer'], ['项目', 'proj']];
  function parseGroupBy(q) {
    if (!/(按|各|分别|什么|哪些|哪几|哪个|每个|分布|排名|构成|都投|投了什么|投向)/.test(q)) return null;
    for (var i = 0; i < NOUN_FIELD.length; i++) { if (q.indexOf(NOUN_FIELD[i][0]) >= 0) return NOUN_FIELD[i][1]; }
    return null;
  }
  var ROLE_FIELD = [[/管理|管理人/, 'mgr'], [/承销/, 'underwriter'], [/托管/, 'custodian'], [/投资|认购|申购|买入|买了|持有|投了|投向/, 'inst']];
  function roleHint(q) { for (var i = 0; i < ROLE_FIELD.length; i++) if (ROLE_FIELD[i][0].test(q)) return ROLE_FIELD[i][1]; return null; }

  // ── entity matching ──
  function matchEntities(q, metric, role) {
    // 拉丁字母统一转大写后再匹配（词表里评级等为大写：aaa → AAA）；长度不变，位置互斥判断不受影响
    q = q.replace(/[a-z]+/g, function (s) { return s.toUpperCase(); });
    // 业务同义词归一：口语叫法 → 台账实际值（在任何匹配前替换）
    q = q.replace(/夹层/g, '中间级').replace(/劣后/g, '次级');
    var consumed = [], byField = {};
    for (var i = 0; i < VOCAB.length; i++) {
      var cand = VOCAB[i], idx = q.indexOf(cand.str);
      if (idx < 0) continue;
      var s = idx, e = idx + cand.str.length, overlap = false;
      for (var j = 0; j < consumed.length; j++) { if (s < consumed[j][1] && e > consumed[j][0]) { overlap = true; break; } }
      if (overlap) continue;
      // which fields does this exact string appear in?
      var fields = VOCAB.filter(function (c) { return c.str === cand.str; });
      var chosen = pickField(fields, metric, role);
      // 防误命中：单字词条、或评级里≤2字的短码（无/A/AA/A+…），需句中出现对应字段线索才采纳
      var needsCue = cand.str.length <= 1 || (chosen.field === 'rating' && cand.str.length <= 2);
      if (needsCue) { var cue = FIELD_CUE[chosen.field]; if (!cue || !cue.test(q)) continue; }
      consumed.push([s, e]);
      if (!byField[chosen.field]) byField[chosen.field] = {};
      chosen.values.forEach(function (v) { byField[chosen.field][v] = 1; });
    }
    var out = {};
    // ── 子串兜底匹配(仅 asset/layer 这类少值结构化字段)──
    // 用户常用口语缩写:「白条」→ 赊销白条/白条取现/信托白条…(OR);「夹层」→ 含"夹层"的分层值。
    // 仅在该字段没有精确命中时启用;取查询里最长的未消费子串(≥2字),命中的全部值纳入 OR。
    ['asset', 'layer'].forEach(function (f) {
      if (byField[f]) return;
      var best = null;
      COUNTS[f].forEach(function (_c, v) {
        for (var L = Math.min(v.length, q.length); L >= 2; L--) {
          if (best && L < best.len) break;
          var found = false;
          for (var i2 = 0; i2 + L <= v.length; i2++) {
            var sub = v.substr(i2, L); var idx = q.indexOf(sub);
            if (idx < 0) continue;
            var e2 = idx + L, ov = false;
            for (var j2 = 0; j2 < consumed.length; j2++) { if (idx < consumed[j2][1] && e2 > consumed[j2][0]) { ov = true; break; } }
            if (ov) continue;
            if (!best || L > best.len) best = { len: L, span: sub, s: idx, e: e2 };
            found = true; break;
          }
          if (found) break;
        }
      });
      if (best) {
        var vals = [];
        COUNTS[f].forEach(function (_c, v) { if (v.indexOf(best.span) >= 0) vals.push(v); });
        if (vals.length) {
          consumed.push([best.s, best.e]);
          byField[f] = {}; vals.forEach(function (v) { byField[f][v] = 1; });
        }
      }
    });
    Object.keys(byField).forEach(function (f) { out[f] = Object.keys(byField[f]); });
    return out;
  }
  function pickField(fields, metric, role) {
    if (fields.length === 1) return fields[0];
    var byRole = role && fields.filter(function (c) { return c.field === role; });
    if (byRole && byRole.length) return byRole[0];
    if (metric === 'share') { var s = fields.filter(function (c) { return c.field === 'inst'; }); if (s.length) return s[0]; }
    // max record count
    var best = fields[0], bc = -1;
    fields.forEach(function (c) { var n = countFor(c.field, c.values); if (n > bc) { bc = n; best = c; } });
    return best;
  }

  // ── build spec ──
  function parse(q) {
    var role = roleHint(q);
    var metricExplicit = parseMetric(q);
    var metric = metricExplicit || 'share';
    var filters = matchEntities(q, metric, role);
    var yearsExplicit = parseYears(q);
    if (yearsExplicit.length) filters.year = yearsExplicit;
    var time = parseTime(q);
    var groupBy = parseGroupBy(q);
    // 句中提到 2 个及以上年份（"2024-2026年"/"2024年和2026年"等）→ 默认按年份分组对比，
    // 不要求必须出现"分别"二字；若已显式识别出其它分组维度(如"按资产类型")则以那个为准。
    if (!groupBy && filters.year && filters.year.length >= 2) groupBy = 'year';
    var trend = /增速|趋势|变化|走势|逐月|月度|每月|环比|同比|增长|逐月/.test(q);
    var topM = q.match(/前\s*(\d+)|top\s*(\d+)/i);
    var topN = topM ? (+(topM[1] || topM[2])) : (/最多|排名|排行/.test(q) ? 10 : null);
    var threshM = q.match(/(?:超过|大于|高于|>=?)\s*(\d+(?:\.\d+)?)\s*亿/);

    var hasFilter = Object.keys(filters).length > 0;
    // 只有出现「显式追问线索」才继承上一次筛选：那…呢 / 再看 / 换成 / 接着 / 呢结尾 等。
    // 不靠「有指标/时间」推断继承——否则「今年一共认购了多少」这类独立总量问句会误继承上一句实体。
    var followupCue = /(那|再[看算查]|换成|改成|接着|同样|刚才|上面)/.test(q) || /呢[？?]*$/.test(q);
    var lastHas = lastSpec && Object.keys(lastSpec.filters).length > 0;
    var inherited = false;
    if (!hasFilter && lastHas && followupCue) {
      filters = JSON.parse(JSON.stringify(lastSpec.filters));
      if (!time) time = lastSpec.time || null;
      if (!metricExplicit) metric = lastSpec.metric;
      inherited = true;
    }
    // 完全无法识别（无实体/指标/时间/意图，且未继承）→ 交给上层给出「没听懂」提示，不硬算数字
    var recognized = hasFilter || inherited || !!groupBy || !!topN || !!metricExplicit || !!time || trend;

    var spec = {
      raw: q, filters: filters, metric: metric, recognized: recognized, inherited: inherited,
      unsupported: (UNSUPPORTED_METRIC.test(q) ? q.match(UNSUPPORTED_METRIC)[0] : null),
      dateFrom: time ? time.from : '', dateTo: time ? time.to : '',
      time: time, timeLabel: time ? time.label : '',
      groupBy: groupBy, trend: trend, topN: topN,
      shareMin: threshM ? +threshM[1] : null
    };
    return spec;
  }

  // ── compute ──
  function filterRecs(spec) {
    var f = spec.filters;
    return DATA.filter(function (r) {
      for (var k in f) { if (f[k] && f[k].length && f[k].indexOf(r[k]) < 0) return false; }
      if (spec.dateFrom && (!r.date || r.date < spec.dateFrom)) return false;
      if (spec.dateTo && (!r.date || r.date > spec.dateTo)) return false;
      if (spec.shareMin != null && (r.share == null || r.share < spec.shareMin)) return false;
      return true;
    });
  }
  function agg(recs, metric) {
    if (metric === 'count') return recs.length;
    if (metric === 'proj') { var s = new Set(); recs.forEach(function (r) { if (r.proj) s.add(r.proj); }); return s.size; }
    if (metric === 'share') return recs.reduce(function (a, r) { return a + (r.share || 0); }, 0);
    if (metric === 'cost' || metric === 'spread') { var arr = recs.filter(function (r) { return r[metric] != null; }); return arr.length ? arr.reduce(function (a, r) { return a + r[metric]; }, 0) / arr.length : null; }
    return 0;
  }
  function fmt(v, metric) {
    if (v == null) return '—';
    if (metric === 'cost' || metric === 'spread') return (v * 100).toFixed(2) + '%';
    if (metric === 'count' || metric === 'proj') return v.toLocaleString('en-US');
    return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function groupAgg(recs, dim, metric) {
    var m = {};
    recs.forEach(function (r) { var k = r[dim] || '（未标注）'; (m[k] = m[k] || []).push(r); });
    var arr = Object.keys(m).map(function (k) { return { key: k, val: agg(m[k], metric), n: m[k].length }; });
    arr.sort(function (a, b) { return (b.val || 0) - (a.val || 0); });
    return arr;
  }
  function monthlySeries(recs, metric) {
    var m = {};
    recs.forEach(function (r) { if (!r.date) return; var k = r.date.slice(0, 7); (m[k] = m[k] || []).push(r); });
    return Object.keys(m).sort().map(function (k) { return { month: k, val: agg(m[k], metric), n: m[k].length }; });
  }

  // ── render answer ──
  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function condChips(spec) {
    var chips = [];
    if (spec.filters.year && spec.filters.year.length) {
      chips.push('<span class="c"><span class="k">年份</span>' + spec.filters.year.join('/') + '年</span>');
    }
    ENTITY_FIELDS.forEach(function (f) {
      if (spec.filters[f] && spec.filters[f].length) {
        var vals = spec.filters[f]; var show = vals.slice(0, 3).join(' / ') + (vals.length > 3 ? ' 等' + vals.length + '项' : '');
        chips.push('<span class="c"><span class="k">' + FIELD_LABEL[f] + '</span>' + esc(show) + '</span>');
      }
    });
    if (spec.timeLabel) chips.push('<span class="c"><span class="k">时间</span>' + esc(spec.timeLabel) + '</span>');
    if (spec.inherited) chips.push('<span class="c" style="background:#fdf6e3;border-color:#ecdfc0;color:#8a6d1d"><span class="k" style="color:#b39a55">⤵</span>承接上一问条件</span>');
    if (spec.shareMin != null) chips.push('<span class="c"><span class="k">份额≥</span>' + spec.shareMin + '亿</span>');
    chips.push('<span class="c"><span class="k">指标</span>' + METRIC_LABEL[spec.metric] + '</span>');
    if (spec.groupBy) chips.push('<span class="c"><span class="k">分组</span>' + FIELD_LABEL[spec.groupBy] + '</span>');
    return '<div class="itlc-cond">' + chips.join('') + '</div>';
  }
  function subjectLabel(spec) {
    var parts = [];
    if (spec.filters.year && spec.filters.year.length) parts.push(spec.filters.year.join('/') + '年');
    ENTITY_FIELDS.forEach(function (f) { if (spec.filters[f] && spec.filters[f].length) parts.push(spec.filters[f].slice(0, 2).join('/')); });
    var subj = parts.join('·');
    return (subj ? subj : '全部年份·全部记录') + (spec.timeLabel ? ' ' + spec.timeLabel : '');
  }

  function answer(spec) {
    var recs = filterRecs(spec);
    var html = '';
    if (!recs.length) {
      return '<div>没有匹配到记录。可换个说法，或检查一下条件：</div>' + condChips(spec);
    }
    var unit = METRIC_UNIT[spec.metric];

    if (spec.trend) {
      var ser = monthlySeries(recs, spec.metric);
      html += '<div>' + esc(subjectLabel(spec)) + ' 逐月' + METRIC_LABEL[spec.metric] + '走势（环比）：</div>';
      html += condChips(spec);
      var maxv = Math.max.apply(null, ser.map(function (s) { return s.val || 0; }).concat([0.0001]));
      html += '<table class="itlc-tbl"><thead><tr><th>月份</th><th class="r">' + METRIC_LABEL[spec.metric] + (unit ? '(' + unit + ')' : '') + '</th><th></th><th class="r">环比</th></tr></thead><tbody>';
      ser.forEach(function (s, i) {
        var mom = '—', cls = 'flat';
        if (i > 0 && ser[i - 1].val) { var g = (s.val - ser[i - 1].val) / ser[i - 1].val; mom = (g >= 0 ? '+' : '') + (g * 100).toFixed(1) + '%'; cls = g > 0.001 ? 'up' : (g < -0.001 ? 'down' : 'flat'); }
        html += '<tr><td class="name">' + s.month + '</td><td class="r v">' + fmt(s.val, spec.metric) + '</td>'
          + '<td class="itlc-bar-cell"><div class="itlc-mini-bar"><i style="width:' + ((s.val || 0) / maxv * 100).toFixed(0) + '%"></i></div></td>'
          + '<td class="r ' + cls + '">' + mom + '</td></tr>';
      });
      html += '</tbody></table>';
      html += linkNote(spec);
      return html;
    }

    var total = agg(recs, spec.metric);
    html += '<div class="itlc-big">' + fmt(total, spec.metric) + (unit ? '<span class="u">' + unit + '</span>' : '') + '</div>';
    var lead = esc(subjectLabel(spec)) + ' ' + METRIC_LABEL[spec.metric] + (spec.metric === 'cost' || spec.metric === 'spread' ? '' : '合计');
    var extra = '（' + recs.length + ' 笔';
    if (spec.metric !== 'proj') { var ps = new Set(); recs.forEach(function (r) { if (r.proj) ps.add(r.proj); }); extra += ' · ' + ps.size + ' 个项目'; }
    extra += '）';
    html = '<div style="margin-bottom:2px">' + lead + '</div>' + html + '<div style="font-size:11px;color:#96a1b0;margin-top:2px">' + extra + '</div>';
    html += condChips(spec);

    if (spec.groupBy === 'year') {
      // 跨年份对比：按年份升序展示（不按数值排序），附同比增长，呼应"分别/对比"的提问意图
      var gm2 = spec.metric;
      var ga2 = groupAgg(recs, 'year', gm2).sort(function (a, b) { return a.key.localeCompare(b.key); });
      var maxv3 = Math.max.apply(null, ga2.map(function (g) { return g.val || 0; }).concat([0.0001]));
      html += '<table class="itlc-tbl"><thead><tr><th>年份</th><th class="r">' + METRIC_LABEL[gm2] + (METRIC_UNIT[gm2] ? '(' + METRIC_UNIT[gm2] + ')' : '') + '</th><th></th><th class="r">同比</th></tr></thead><tbody>';
      ga2.forEach(function (g, i) {
        var yoy = '—', cls = 'flat';
        if (i > 0 && ga2[i - 1].val) { var gr = (g.val - ga2[i - 1].val) / ga2[i - 1].val; yoy = (gr >= 0 ? '+' : '') + (gr * 100).toFixed(1) + '%'; cls = gr > 0.001 ? 'up' : (gr < -0.001 ? 'down' : 'flat'); }
        html += '<tr><td class="name">' + esc(g.key) + '年</td><td class="r v">' + fmt(g.val, gm2) + '</td>'
          + '<td class="itlc-bar-cell"><div class="itlc-mini-bar"><i style="width:' + ((g.val || 0) / maxv3 * 100).toFixed(0) + '%"></i></div></td>'
          + '<td class="r ' + cls + '">' + yoy + '</td></tr>';
      });
      html += '</tbody></table>';
    } else if (spec.groupBy) {
      var dim = spec.groupBy;
      var gm = spec.metric;   // 分组聚合直接用所问指标（项目数/笔数/成本…都按组内算，不再偷换成份额）
      var ga = groupAgg(recs, dim, gm);
      var N = spec.topN || 12;
      var top = ga.slice(0, N);
      var maxv2 = Math.max.apply(null, top.map(function (g) { return g.val || 0; }).concat([0.0001]));
      html += '<table class="itlc-tbl"><thead><tr><th>' + FIELD_LABEL[dim] + '</th><th class="r">' + METRIC_LABEL[gm] + (METRIC_UNIT[gm] ? '(' + METRIC_UNIT[gm] + ')' : '') + '</th><th></th></tr></thead><tbody>';
      top.forEach(function (g) {
        html += '<tr><td class="name">' + esc(g.key) + '</td><td class="r v">' + fmt(g.val, gm) + '</td>'
          + '<td class="itlc-bar-cell"><div class="itlc-mini-bar"><i style="width:' + ((g.val || 0) / maxv2 * 100).toFixed(0) + '%"></i></div></td></tr>';
      });
      html += '</tbody></table>';
      if (ga.length > N) html += '<div style="font-size:11px;color:#96a1b0;margin-top:5px">共 ' + ga.length + ' 项，表内显示前 ' + N + '，完整结果见下方面板</div>';
    }
    html += linkNote(spec);
    return html;
  }
  function linkNote(spec) {
    return '<div class="itlc-note">✓ 已按此条件联动下方面板　<span class="lk" data-itlc="clear">清空面板</span></div>';
  }

  // ── apply to panel ──
  // 多年份模式下面板按年份拆成独立子 Tab（window.ITL_REG = {2026:inst,2025:inst,2024:inst}）。
  // 问答语料本身跨年份合并、不受当前 Tab 限制；但"联动面板"这个动作必须落到具体某一年的实例上：
  //   - 问句里显式指定了唯一年份 → 联动并切换到那一年的子 Tab
  //   - 未指定年份（跨年汇总问题）→ 联动到当前正打开的那个年份子 Tab，不强行切换
  function currentActiveYear() {
    var btn = document.querySelector('.sub-tab-button.active[data-sub^="query_"]');
    if (btn) return btn.dataset.sub.replace('query_', '');
    return '2026';
  }
  function applyToPanel(spec) {
    var panelSpec = { filters: {}, dateFrom: spec.dateFrom, dateTo: spec.dateTo, shareMin: spec.shareMin };
    ENTITY_FIELDS.forEach(function (f) { if (spec.filters[f] && spec.filters[f].length && (CHIP_FIELDS.indexOf(f) >= 0 || KW_FIELDS.indexOf(f) >= 0)) panelSpec.filters[f] = spec.filters[f]; });
    if (spec.trend) panelSpec.view = 'detail';
    else if (spec.groupBy && PANEL_DIMS.indexOf(spec.groupBy) >= 0) panelSpec.groupBy = spec.groupBy;
    else panelSpec.view = 'detail';

    if (window.ITL_REG) {
      // 多年份模式
      var targetYear = (spec.filters.year && spec.filters.year.length === 1) ? spec.filters.year[0] : currentActiveYear();
      var inst = window.ITL_REG[targetYear];
      if (!inst) return;
      inst.applySpec(panelSpec);
      if (window.selectModule) { try { window.selectModule('ledger'); } catch (e) { } }
      if (window.selectSub) { try { window.selectSub('query_' + targetYear); } catch (e) { } }
    } else if (window.ITL && window.ITL.applySpec) {
      // 单年份独立预览模式（向后兼容）
      window.ITL.applySpec(panelSpec);
      if (window.selectModule) { try { window.selectModule('ledger'); } catch (e) { } }
    }
  }

  // ── UI ──
  var elBody, elTa, elPanel, elSend;
  var SUGGEST = [
    '中信证券今年管理规模多少？',
    '交银理财2月份投资多少，都投了什么资产？',
    '平安理财的投资增速变化情况如何？',
    '按认购机构看今年份额排名前10',
    '交银理财2024-2026年分别投资规模多少？'
  ];

  function addMsg(role, html) {
    var d = document.createElement('div'); d.className = 'itlc-msg ' + role;
    d.innerHTML = '<div class="itlc-bubble">' + html + '</div>';
    elBody.appendChild(d); elBody.scrollTop = elBody.scrollHeight;
  }
  function suggList() {
    return '<div class="itlc-sugg">' + SUGGEST.map(function (q) { return '<button class="q" data-itlc-q="' + esc(q) + '">' + esc(q) + '</button>'; }).join('') + '</div>';
  }
  function suggestBlock() {
    return '<div>你好，我是投资台账问答助手。可以用大白话问我，例如：</div>' + suggList();
  }

  function handle(q) {
    q = (q || '').trim(); if (!q) return;
    addMsg('user', esc(q));
    var spec;
    try { spec = parse(q); } catch (e) { addMsg('bot', '抱歉，这句我没解析出来，换个说法试试？'); return; }
    if (!spec.recognized) {
      addMsg('bot', '这句我没太听懂——没识别到机构/资产/时间等条件。换个说法，或点下面的例子：' + suggList());
      return;   // 不覆盖上一次上下文、不改面板，避免给出看似确定的错误数字
    }
    if (spec.unsupported) {
      addMsg('bot', '台账里没有「' + esc(spec.unsupported) + '」这个指标，我不能硬算。目前支持：认购份额、规模、平均成本、平均利差、笔数、项目数。');
      return;
    }
    lastSpec = spec;
    var html;
    try { html = answer(spec); applyToPanel(spec); } catch (e) { html = '解析成功但计算出错了：' + esc(e.message); }
    addMsg('bot', html);
  }

  function init() {
    if (window.__itlcReady) return; window.__itlcReady = true;
    initVocab();
    var ball = document.createElement('button');
    ball.className = 'itlc-ball';
    ball.innerHTML = '<span class="itlc-dot"></span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>';
    document.body.appendChild(ball);

    elPanel = document.createElement('div');
    elPanel.className = 'itlc-panel';
    elPanel.innerHTML =
      '<div class="itlc-head"><div><div class="t">投资台账 · 智能问答</div><div class="s">本地解析 · 数据不出内网</div></div><button class="itlc-x">×</button></div>'
      + '<div class="itlc-body"></div>'
      + '<div class="itlc-foot"><textarea class="itlc-ta" rows="1" placeholder="用大白话问，例如：交银理财今年投了多少？"></textarea>'
      + '<button class="itlc-send"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg></button></div>'
      + '<div class="itlc-hint">支持：机构/管理人/承销商/托管行/资产/评级/分层/年份(2024-2026，支持范围与对比) · 份额·规模·成本·利差 · 月份/季度 · 排名·分组·增速 · 跨年份问答不受当前 Tab 限制</div>';
    document.body.appendChild(elPanel);

    elBody = elPanel.querySelector('.itlc-body');
    elTa = elPanel.querySelector('.itlc-ta');
    elSend = elPanel.querySelector('.itlc-send');
    addMsg('bot', suggestBlock());

    ball.addEventListener('click', function () { elPanel.classList.toggle('open'); if (elPanel.classList.contains('open')) elTa.focus(); });
    elPanel.querySelector('.itlc-x').addEventListener('click', function () { elPanel.classList.remove('open'); });
    elSend.addEventListener('click', function () { handle(elTa.value); elTa.value = ''; elTa.style.height = 'auto'; });
    elTa.addEventListener('keydown', function (e) { if (e.isComposing || e.keyCode === 229) return; if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handle(elTa.value); elTa.value = ''; elTa.style.height = 'auto'; } });
    elTa.addEventListener('input', function () { this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 90) + 'px'; });
    elBody.addEventListener('click', function (e) {
      var qb = e.target.closest('[data-itlc-q]'); if (qb) { handle(qb.getAttribute('data-itlc-q')); return; }
      var lk = e.target.closest('[data-itlc]');
      if (lk && lk.getAttribute('data-itlc') === 'clear') {
        if (window.ITL_REG) { var inst = window.ITL_REG[currentActiveYear()]; if (inst) inst.applySpec({ filters: {} }); }
        else if (window.ITL && window.ITL.applySpec) { window.ITL.applySpec({ filters: {} }); }
        addMsg('bot', '已清空面板筛选。');
      }
    });
  }

  window.ITLChat = { init: init };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

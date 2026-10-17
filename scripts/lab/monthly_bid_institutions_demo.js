(() => {
  'use strict';
  const root = document.getElementById('latest-bookkeeping');
  if (!root) return;
  const data = JSON.parse(document.getElementById('lb-data').textContent);
  const monthly = JSON.parse(document.getElementById('lb-monthly-data').textContent);
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fmt = value => typeof value === 'number' && Number.isFinite(value)
    ? value.toLocaleString('zh-CN', {maximumFractionDigits:value > 0 && value < 0.0001 ? 12 : 4}) : '未披露';
  const amount = value => fmt(value) === '未披露' ? '未披露' : fmt(value) + '亿元';
  const percent = value => {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    return value > 0 && value < 0.001 ? '<0.1%' : (value * 100).toFixed(1) + '%';
  };
  const groups = monthly.groups || ['理财子', '银行', '公募基金', '券商', '其他'];
  // 历史项目仍可出现在下方卡片；全年缺省数据遵循既有资产板块范围。
  const threeGroupAssets = new Set(['赊销白条', '金条白取混发', '信托金条', '白条取现',
    '信托企业主贷', '小贷企业主贷', '保理', '金采']);
  const emptyAsset = name => ({
    institutions:[], counts:Array(12).fill(0), visibleCounts:Array(12).fill(0),
    projectCounts:Array(12).fill(0), projectCount:0, totalAllocatedSize:0,
    bidCount:0, fallbackCount:0, bubbleMaxSize:1,
    visibleGroups:threeGroupAssets.has(name) ? groups.slice(0,3) : groups
  });
  const tooltip = document.createElement('div');
  tooltip.id = 'lb-monthly-tooltip';
  tooltip.className = 'lb-monthly-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.hidden = true;
  root.appendChild(tooltip);
  const scroll = $('lb-monthly-scroll');
  scroll.setAttribute('aria-label', '月度投标矩阵，可滚动查看；Tab进入气泡，方向键查看其他月份和机构');
  const expand = $('lb-monthly-expand');
  expand.setAttribute('aria-controls', scroll.id);
  expand.textContent = expand.getAttribute('aria-expanded') === 'true' ? '收起月表' : '扩大月表';
  const note = root.querySelector('.lb-monthly-note');
  if (note) note.innerHTML = '<span class="lb-monthly-legend-solid"></span> 月度规模以申购为主；1—3月未披露申购的项目以实际配售补充。气泡按当前资产独立缩放，悬停或聚焦查看金额与口径，方向键切换气泡。参与率按全年项目数计算；中标规模占比按全年实际配售计算，分母含未展示板块，剔除明确自持 / 不出表，仅限交易所 / 银行间。小于0.1%的正比例显示＜0.1%，0.0%为真实零，—为未知。下方最近项目卡按最近3期展示。';

  let index = 0, shownBubble = null;
  const bubbles = () => [...$('lb-monthly-rows').querySelectorAll('.lb-monthly-bubble')];
  function hideTooltip() {
    if (shownBubble) shownBubble.removeAttribute('aria-describedby');
    shownBubble = null;
    tooltip.hidden = true;
  }
  function placeTooltip(bubble) {
    const rect = bubble.getBoundingClientRect();
    const box = tooltip.getBoundingClientRect();
    const width = document.documentElement.clientWidth;
    const height = document.documentElement.clientHeight;
    tooltip.style.left = Math.max(8, Math.min(rect.left, width - box.width - 8)) + 'px';
    tooltip.style.top = Math.max(8, rect.bottom + box.height + 8 <= height
      ? rect.bottom + 8 : Math.min(rect.top - box.height - 8, height - box.height - 8)) + 'px';
  }
  function showTooltip(bubble) {
    hideTooltip();
    shownBubble = bubble;
    tooltip.textContent = bubble.title;
    tooltip.hidden = false;
    tooltip.scrollTop = 0;
    bubble.setAttribute('aria-describedby', tooltip.id);
    placeTooltip(bubble);
  }
  function setRoving(bubble) {
    bubbles().forEach(item => { item.tabIndex = item === bubble ? 0 : -1; });
  }
  function monthDetail(inst, records, month, size) {
    const bidRecords = records.filter(record => record.track === 'bids');
    const allocationRecords = records.filter(record => record.track === 'allocations');
    const track = bidRecords.length && allocationRecords.length ? 'mixed'
      : bidRecords.length ? 'bids' : 'allocations';
    const sum = items => items.reduce((total, record) => total + record.size, 0);
    const summary = track === 'mixed'
      ? `展示规模合计 ${fmt(size)}亿元（申购 ${fmt(sum(bidRecords))}亿元；实际配售补充 ${fmt(sum(allocationRecords))}亿元）`
      : `${track === 'bids' ? '申购' : '实际配售补充'}合计 ${fmt(size)}亿元`;
    const title = `${inst.name} · 2026年${month+1}月 · ${summary} · ${records.length}笔\n` + records.map(record =>
      `${record.date} ${record.project}｜${record.rawInstitution}｜${record.track === 'bids' ? '申购' : '实际配售补充'} ${fmt(record.size)}亿元｜总表${record.track === 'bids' ? 'W' : 'U'}${record.row}:${record.track === 'bids' ? 'Y' : 'V'}${record.row}`
    ).join('\n');
    return {track, title};
  }
  function render() {
    hideTooltip();
    const name = data.assets[index].name;
    const asset = {...emptyAsset(name), ...monthly.assets[name]};
    const visibleGroups = asset.visibleGroups;
    const visible = asset.institutions.filter(inst => visibleGroups.includes(inst.group));
    const visibleCounts = asset.visibleCounts;
    const query = $('lb-monthly-search').value.trim().toLowerCase();
    const rows = visible.filter(inst => (inst.name + ' ' + inst.months.flat().map(record => record.rawInstitution).join(' ')).toLowerCase().includes(query));
    const noYearData = asset.projectCount === 0 && asset.institutions.length === 0;
    $('lb-monthly-head').innerHTML = '<tr><th scope="col" class="lb-monthly-name">投标机构 / 板块</th>' + Array.from({length:12}, (_,month) =>
      `<th scope="col" class="${asset.counts[month] ? '' : 'lb-monthly-unreported'}">${month+1}月<span>${asset.counts[month] ? visibleCounts[month]+'家' : noYearData ? '无数据' : '未披露'}</span></th>`
    ).join('') + `<th scope="col" title="该类资产2026年共${asset.projectCount}个项目">参与率<span>${asset.projectCount}个项目</span></th><th scope="col" class="lb-monthly-share" title="${esc('该资产2026年全部机构实际配售合计' + amount(asset.totalAllocatedSize) + (asset.totalAllocatedSize == null ? '；完整金额未披露，暂无法计算占比' + (typeof asset.totalKnownAllocatedSize === 'number' ? '；已知部分' + amount(asset.totalKnownAllocatedSize) : '') : ''))}">中标规模占比<span>全年实际配售</span></th></tr>`;
    let firstBubble = true;
    const renderedGroups = visibleGroups.map((group,groupIndex) => {
      const institutions = rows.filter(inst => inst.group === group);
      const allCount = asset.institutions.filter(inst => inst.group === group).length;
      const header = `<tr class="lb-monthly-group" id="lb-monthly-group-${groupIndex}"><th colspan="15" scope="rowgroup">${esc(group)}<span>${institutions.length} 家${query ? ' / 全部 '+allCount+' 家' : ''}</span></th></tr>`;
      return header + (institutions.length ? institutions.map(inst => {
        const rowIndex = rows.indexOf(inst);
        const cells = Array.from({length:12}, (_,month) => {
          const records = inst.months[month] || [];
          let bubble = '';
          if (records.length) {
            const size = inst.monthlySizes[month];
            const detail = monthDetail(inst, records, month, size);
            const diameter = Math.max(3, 26*Math.sqrt(size/asset.bubbleMaxSize)).toFixed(2);
            bubble = `<span class="lb-monthly-bubble" role="button" tabindex="${firstBubble ? 0 : -1}" style="width:${diameter}px;height:${diameter}px" data-size="${size}" data-track="${detail.track}" data-row="${rowIndex}" data-month="${month}" title="${esc(detail.title)}" aria-label="${esc(detail.title)}"></span>`;
            firstBubble = false;
          }
          return `<td class="${asset.counts[month] ? '' : 'lb-monthly-unreported'}">${bubble}</td>`;
        }).join('');
        const shareTitle = inst.allocationShare == null
          ? `全年实际配售占比未知；完整金额未披露。机构全年实际配售${amount(inst.allocatedSize)}；资产全部机构实际配售${amount(asset.totalAllocatedSize)}`
            + (inst.allocatedSize == null && typeof inst.knownAllocatedSize === 'number' ? `；机构已知部分${amount(inst.knownAllocatedSize)}` : '')
            + (asset.totalAllocatedSize == null && typeof asset.totalKnownAllocatedSize === 'number' ? `；资产已知部分${amount(asset.totalKnownAllocatedSize)}` : '')
          : `机构全年实际配售${fmt(inst.allocatedSize)}亿元 ÷ 该资产全部机构实际配售${fmt(asset.totalAllocatedSize)}亿元（含未展示板块）`;
        return '<tr class="lb-monthly-institution"><th scope="row" class="lb-monthly-name" title="' + esc([...new Set(inst.months.flat().map(record => record.rawInstitution))].join(' / ')) + '">' + esc(inst.name) + '</th>' + cells
          + `<td class="lb-monthly-total" title="参与${inst.participationCount}个项目 ÷ 该类资产2026年共${asset.projectCount}个项目；覆盖${inst.monthCount}个月">${esc(percent(inst.participationRate))}</td><td class="lb-monthly-total lb-monthly-share" title="${esc(shareTitle)}">${esc(percent(inst.allocationShare))}</td></tr>`;
      }).join('') : '<tr><td colspan="15" class="lb-monthly-empty">' + (noYearData ? '2026年无数据' : query ? '无匹配机构' : '该板块暂无已披露投标') + '</td></tr>');
    });
    $('lb-monthly-rows').innerHTML = (noYearData ? `<tr><td colspan="15" class="lb-monthly-empty" role="status">${esc(name)} · 2026年无数据；下方仍可查看最近项目。</td></tr>` : '') + renderedGroups.join('');
  }
  root.addEventListener('click', event => {
    const bubble = event.target.closest('.lb-monthly-bubble');
    if (bubble) { setRoving(bubble); bubble.focus(); showTooltip(bubble); return; }
    const button = event.target.closest('button');
    if (button && button.dataset.asset !== undefined) {
      index = Number(button.dataset.asset);
      $('lb-monthly-search').value = '';
      render();
      scroll.scrollTop = 0;
    }
  });
  root.addEventListener('focusin', event => {
    const bubble = event.target.closest('.lb-monthly-bubble');
    if (bubble) { setRoving(bubble); showTooltip(bubble); }
  });
  root.addEventListener('focusout', event => {
    if (event.target.closest('.lb-monthly-bubble')) hideTooltip();
  });
  root.addEventListener('pointerover', event => {
    const bubble = event.target.closest('.lb-monthly-bubble');
    if (bubble) showTooltip(bubble);
  });
  root.addEventListener('pointerout', event => {
    if (event.target.closest('.lb-monthly-bubble')) {
      const focused = document.activeElement.closest('.lb-monthly-bubble');
      if (focused) showTooltip(focused); else hideTooltip();
    }
  });
  root.addEventListener('keydown', event => {
    const bubble = event.target.closest('.lb-monthly-bubble');
    if (!bubble) return;
    if (event.key === 'Escape') { event.preventDefault(); hideTooltip(); return; }
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); showTooltip(bubble); return; }
    if (event.key === 'PageDown' || event.key === 'PageUp') {
      event.preventDefault();
      tooltip.scrollTop += (event.key === 'PageDown' ? 1 : -1) * tooltip.clientHeight;
      return;
    }
    if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key)) return;
    event.preventDefault();
    const all = bubbles();
    const row = Number(bubble.dataset.row), month = Number(bubble.dataset.month);
    let next;
    if (event.key === 'Home' || event.key === 'End') next = all[event.key === 'Home' ? 0 : all.length-1];
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      const direction = event.key === 'ArrowRight' ? 1 : -1;
      next = all.filter(item => Number(item.dataset.row) === row && (Number(item.dataset.month)-month)*direction > 0)
        .sort((a,b) => direction*(Number(a.dataset.month)-Number(b.dataset.month)))[0];
    } else {
      const direction = event.key === 'ArrowDown' ? 1 : -1;
      next = all.filter(item => (Number(item.dataset.row)-row)*direction > 0).sort((a,b) =>
        direction*(Number(a.dataset.row)-Number(b.dataset.row)) || Math.abs(Number(a.dataset.month)-month)-Math.abs(Number(b.dataset.month)-month))[0];
    }
    if (next) {
      setRoving(next);
      next.focus({preventScroll:true});
      next.scrollIntoView({block:'nearest', inline:'nearest'});
      showTooltip(next);
    }
  });
  scroll.addEventListener('scroll', () => {
    const focused = document.activeElement.closest('.lb-monthly-bubble');
    if (shownBubble && (focused === shownBubble || shownBubble.matches(':hover'))) placeTooltip(shownBubble); else hideTooltip();
  });
  window.addEventListener('resize', hideTooltip);
  window.addEventListener('scroll', event => {
    if (event.target === document || event.target === window) {
      if (shownBubble && (document.activeElement === shownBubble || shownBubble.matches(':hover'))) placeTooltip(shownBubble);
      else hideTooltip();
    }
  }, true);
  $('lb-monthly-search').addEventListener('input', () => { render(); scroll.scrollTop = 0; });
  expand.addEventListener('click', () => {
    const expanded = expand.getAttribute('aria-expanded') !== 'true';
    expand.setAttribute('aria-expanded', String(expanded));
    expand.textContent = expanded ? '收起月表' : '扩大月表';
    scroll.classList.toggle('expanded', expanded);
    hideTooltip();
  });
  render();
})();

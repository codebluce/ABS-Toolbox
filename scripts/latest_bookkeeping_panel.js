(() => {
  'use strict';
  const root = document.getElementById('latest-bookkeeping');
  if (!root) return;
  const data = JSON.parse(document.getElementById('lb-data').textContent);
  const $ = id => root.querySelector('#' + id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const fmt = value => typeof value === 'number' ? value.toLocaleString('zh-CN', {maximumFractionDigits:4}) : '未披露';
  const rate = value => typeof value === 'number' ? (value * 100).toFixed(2) + '%' : value || '未披露';
  const costs = tier => tier.costs.length ? tier.costs.map(rate).join(' / ') : '未披露';
  // 同档位在申购/配售两种视图中保持同色，文字仍作为主要标识。
  const layerTone = name => {
    const value = name.replace(/\s+/g, '').toUpperCase();
    if (/次级/.test(value)) return 'junior';
    if (/中间|夹层/.test(value)) return 'mezzanine';
    if (/^(优先|优先级)?A1/.test(value)) return 'senior-a1';
    if (/^(优先|优先级)?A2/.test(value)) return 'senior-a2';
    if (/^(优先|优先级)?A/.test(value)) return 'senior-a';
    if (/^(优先|优先级)?B/.test(value)) return 'senior-b';
    if (/^(优先|优先级)?C/.test(value)) return 'senior-c';
    if (/^(优先|优先级)?D/.test(value)) return 'senior-d';
    return 'neutral';
  };
  // 表格与 CSV 共用列定义，避免切换口径后表头、数据或导出错位。
  const columnsByView = {
    bids: [
      {label:'档位', key:'layer'},
      {label:'机构名称', key:'institution'},
      {label:'申购利率', key:'rate', numeric:true, format:rate},
      {label:'申购规模（亿元）', key:'bidSize', numeric:true, format:fmt}
    ],
    allocations: [
      {label:'档位', key:'layer'},
      {label:'机构名称', key:'institution'},
      {label:'成本利率', key:'cost', numeric:true},
      {label:'配售规模（亿元）', key:'share', numeric:true, format:fmt}
    ]
  };
  const cellValue = (row, column) => column.format ? column.format(row[column.key]) : row[column.key];
  let assetIndex = 0, projectIndex = 0, view = 'bids', layer = '';
  const asset = () => data.assets[assetIndex];
  const project = () => asset().projects[projectIndex];
  const allRows = () => project().tiers.flatMap(tier => tier[view].map(row => ({...row, layer:tier.name, cost:rate(row.cost)})));
  const filteredRows = () => {
    const query = $('lb-search').value.trim().toLowerCase();
    return allRows().filter(row => (!layer || row.layer === layer) && row.institution.toLowerCase().includes(query));
  };
  $('lb-source').textContent = `数据来源：${data.source}　｜　台账最新簿记：${data.asOf}　｜　仅交易所 / 银行间 · 各资产查询最近3期`;
  $('lb-asset-count').textContent = `${data.assets.length} 类资产 · 点击切换`;
  $('lb-assets').innerHTML = data.assets.map((item, index) => `<button type="button" class="lb-asset" data-asset="${index}" aria-pressed="false"><strong>${esc(item.name)}</strong><span>${esc(item.date)} · ${item.projects.length} 期 / ${item.projects.length} 个项目</span></button>`).join('');
  function renderRows() {
    root.querySelectorAll('[data-view]').forEach(button => {
      const active = button.dataset.view === view;
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
    });
    root.querySelectorAll('[data-tier]').forEach(button => {
      const active = button.dataset.tier === layer;
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
    });
    $('lb-layer').value = layer;
    const rows = filteredRows();
    $('lb-row-count').textContent = `${rows.length} / ${allRows().length} 条记录`;
    const columns = columnsByView[view];
    $('lb-columns').innerHTML = columns.map(column => `<th${column.numeric ? ' class="lb-num"' : ''}>${esc(column.label)}</th>`).join('');
    $('lb-rows').innerHTML = rows.map(row => '<tr>' + columns.map(column => {
      const value = cellValue(row, column);
      const content = column.key === 'layer' ? `<span class="lb-layer-tag lb-layer-${layerTone(value)}">${esc(value)}</span>`
        : value === '未披露' ? `<span class="lb-unavailable">未披露</span>` : esc(value);
      return `<td${column.numeric ? ' class="lb-num"' : ''}>${content}</td>`;
    }).join('') + '</tr>').join('');
    $('lb-empty').hidden = rows.length > 0;
    $('lb-empty').textContent = allRows().length ? '没有符合筛选条件的机构，试试其他档位或关键词。' : view === 'bids' ? '所选项目尚未披露申购明细；未回退到历史项目。' : '所选项目尚未披露最终配售明细。';
    const key = view === 'allocations' ? 'share' : 'bidSize';
    const known = rows.filter(row => typeof row[key] === 'number');
    $('lb-totals').textContent = rows.length ? `当前筛选 · ${view === 'allocations' ? '已披露配售规模' : '已披露申购规模'}合计 ${fmt(known.reduce((sum,row)=>sum+row[key],0))} 亿元${known.length < rows.length ? ` · ${rows.length-known.length} 笔规模未披露（不计入合计）` : ''} · ${view === 'allocations' ? '机构' : '报价'}记录 ${rows.length} 笔` : '';
    $('lb-export').disabled = rows.length === 0;
  }
  function renderProject() {
    const p = project();
    $('lb-project-name').textContent = p.name;
    $('lb-project-date').textContent = p.date;
    $('lb-project-meta').textContent = `${asset().name}　｜　管理人：${p.manager || '未披露'}　｜　${p.venue || '场所未披露'}　｜　项目期限：${p.tenor && p.tenor !== '-' ? p.tenor : '未披露'}　｜　发行规模 ${fmt(p.size)} 亿元`;
    $('lb-layer').innerHTML = '<option value="">全部档位</option>' + p.tiers.map(tier => `<option value="${esc(tier.name)}">${esc(tier.name)}</option>`).join('');
    $('lb-tiers').innerHTML = p.tiers.map(tier => `<button type="button" class="lb-tier" data-tier="${esc(tier.name)}" aria-pressed="false"><div class="lb-tier-head">${esc(tier.name)}</div><div class="lb-tier-rate">${esc(costs(tier))}</div><div class="lb-tier-caption">${tier.costs.length > 1 ? '多条成本口径，保留源表值' : '档位成本利率'}</div><div class="lb-tier-note">${tier.bids.length} 笔报价 · ${tier.allocations.length} 笔配售</div></button>`).join('');
    renderRows();
  }
  function renderAsset() {
    root.querySelectorAll('[data-asset]').forEach(button => {
      const active = Number(button.dataset.asset) === assetIndex;
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
    });
    $('lb-project').innerHTML = asset().projects.map((p,index) => `<option value="${index}">${esc(p.name)} · ${esc(p.date)}</option>`).join('');
    $('lb-tie-note').textContent = `最近 ${asset().projects.length} 期 · ${asset().projects.length} 个项目${asset().projects.length < 3 ? '（不足3期，展示全部可用期次）' : ''}`;
    renderProject();
  }
  root.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.dataset.asset !== undefined) {
      assetIndex = Number(button.dataset.asset); projectIndex = 0; layer = ''; $('lb-search').value = ''; renderAsset();
    } else if (button.dataset.tier !== undefined) {
      layer = layer === button.dataset.tier ? '' : button.dataset.tier; renderRows();
    } else if (button.dataset.view) { view = button.dataset.view; renderRows(); }
  });
  $('lb-project').addEventListener('change', () => {projectIndex = Number($('lb-project').value); layer = ''; $('lb-search').value = ''; renderProject();});
  $('lb-layer').addEventListener('change', () => {layer = $('lb-layer').value; renderRows();});
  $('lb-search').addEventListener('input', renderRows);
  $('lb-export').addEventListener('click', () => {
    const field = value => '"' + String(value ?? '').replace(/^[=+\-@\t\r\n]/, "'$&").replace(/"/g,'""') + '"';
    const columns = columnsByView[view];
    const header = columns.map(column => column.label);
    const rows = filteredRows().map(row => columns.map(column => cellValue(row, column)));
    const blob = new Blob(['\ufeff' + [header,...rows].map(row=>row.map(field).join(',')).join('\r\n')], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `${project().name}_${view === 'allocations' ? '最终配售' : '申购明细'}_簿记明细.csv`; link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  renderAsset();
})();

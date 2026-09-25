  (() => {
    'use strict';
    const root = document.getElementById('alloc-quick');
    const get = id => root.querySelector('#' + id);
    const snapshot = JSON.parse(get('alloc-snapshot').textContent);
    const records = snapshot.records;
    const aliases = snapshot.investor_aliases;
    const canonical = name => aliases[name] || name;
    const originalsByName = new Map();
    records.forEach(r => {
      const name = canonical(r.investor);
      if (!originalsByName.has(name)) originalsByName.set(name, new Set());
      originalsByName.get(name).add(r.investor);
    });
    const names = [...originalsByName.keys()].sort((a,b) => a.localeCompare(b,'zh-CN'));
    const input = get('inst-search');
    const dropdown = get('inst-options');
    const month = get('month-select');
    const clear = get('clear-search');
    let selected = names.includes('中信证券') ? '中信证券' : null;
    let active = -1;
    let matches = [];
    let composing = false;

    const fmt = value => Number(value).toLocaleString('zh-CN',{maximumFractionDigits:2});
    function closeDropdown() {
      dropdown.classList.remove('show');
      input.setAttribute('aria-expanded','false');
      active = -1;
    }
    function choose(name) {
      selected = name;
      input.value = name;
      closeDropdown();
      render();
    }
    function showDropdown() {
      const query = input.value.trim().toLocaleLowerCase('zh-CN');
      const exact = names.filter(name => name.toLocaleLowerCase('zh-CN') === query);
      matches = exact.length ? exact : names.filter(name =>
        name.toLocaleLowerCase('zh-CN').includes(query) ||
        [...originalsByName.get(name)].some(original => original.toLocaleLowerCase('zh-CN').includes(query))
      );
      dropdown.replaceChildren();
      const limit = 60;
      matches.slice(0,limit).forEach((name,index) => {
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'search-item';
        option.setAttribute('role','option');
        option.setAttribute('aria-selected',name === selected ? 'true' : 'false');
        const label = document.createElement('span');
        label.textContent = name;
        const badge = document.createElement('small');
        const count = records.filter(r => canonical(r.investor) === name && r.month === month.value).length;
        badge.textContent = count ? `${month.value} · ${count}笔` : `${month.value}暂无`;
        option.append(label,badge);
        option.addEventListener('click',() => choose(name));
        dropdown.append(option);
      });
      if (!matches.length) {
        const empty = document.createElement('div');
        empty.className = 'search-empty';
        empty.textContent = '未找到匹配机构';
        dropdown.append(empty);
      } else if (matches.length > limit) {
        const note = document.createElement('div');
        note.className = 'dropdown-note';
        note.textContent = `仅显示前 ${limit} 个结果，请继续输入关键词缩小范围`;
        dropdown.append(note);
      }
      dropdown.classList.add('show');
      input.setAttribute('aria-expanded','true');
      active = -1;
    }
    function moveActive(delta) {
      const items = dropdown.querySelectorAll('.search-item');
      if (!items.length) return;
      active = Math.max(0, Math.min(items.length-1, active + delta));
      items.forEach((item,index) => item.classList.toggle('active',index === active));
      items[active].scrollIntoView({block:'nearest'});
    }
    function td(row,value,className='') {
      const cell = document.createElement('td');
      cell.className = className;
      cell.textContent = value || '—';
      if (!value || value === '—') cell.classList.add('missing');
      row.append(cell);
      return cell;
    }
    function renderRows(rows) {
      const body = get('detail-rows');
      body.replaceChildren();
      if (!rows.length) {
        const tr = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 12;
        cell.className = 'table-empty';
        cell.textContent = '该机构在所选月份没有可计入的表内分量，请切换月份或机构名称。';
        tr.append(cell); body.append(tr);
        return;
      }
      rows.forEach(record => {
        const tr = document.createElement('tr');
        td(tr,record.asset);
        const project = td(tr,'');
        project.classList.remove('missing');
        const name = document.createElement('span');
        name.className = 'project-name';
        name.textContent = record.project;
        project.replaceChildren(name);
        td(tr,record.manager); td(tr,record.tenor);
        const levelCell = td(tr,''); levelCell.classList.remove('missing');
        const level = document.createElement('span');
        level.className = record.level === '夹层' ? 'level mezz' : 'level';
        level.textContent = record.level;
        levelCell.replaceChildren(level);
        td(tr,record.investor,'investor');
        td(tr,fmt(record.amount_wan),'num amount');
        td(tr,record.price,'num'); td(tr,record.premium,'num');
        td(tr,record.scale,'num'); td(tr,record.tranche); td(tr,record.origin);
        body.append(tr);
      });
    }
    function render() {
      clear.style.display = input.value ? 'block' : 'none';
      const result = get('result-panel');
      const empty = get('empty-state');
      if (!selected) {
        result.hidden = true;
        empty.hidden = false;
        get('empty-title').textContent = input.value.trim() ? '请选择机构' : '输入机构名称开始查询';
        get('empty-copy').textContent = input.value.trim() ? '从搜索结果下拉列表中选择机构' : '支持模糊搜索；从下拉列表中选择机构查看获配明细';
        return;
      }
      empty.hidden = true;
      result.hidden = false;
      const rows = records.filter(r => canonical(r.investor) === selected && r.month === month.value);
      const junior = rows.filter(r => r.level === '次级').reduce((s,r) => s + Number(r.amount_wan),0);
      const mezz = rows.filter(r => r.level === '夹层').reduce((s,r) => s + Number(r.amount_wan),0);
      const projects = new Set(rows.map(r => r.project)).size;
      get('result-title').textContent = `${selected} · 2026年${month.value}`;
      get('result-subtitle').textContent = rows.length ? `${projects} 个项目 · ${rows.length} 笔明细（次级 ${rows.filter(r => r.level === '次级').length} 笔 / 夹层 ${rows.filter(r => r.level === '夹层').length} 笔）` : '本月无可计入的表内分量';
      get('total-amount').textContent = fmt(junior + mezz);
      get('junior-amount').textContent = fmt(junior);
      get('mezz-amount').textContent = fmt(mezz);
      get('count-stat').textContent = `${projects} / ${rows.length}`;
      const alert = get('month-alert');
      alert.classList.toggle('show',month.value === '3月' || rows.some(r => r.original_amount));
      alert.textContent = month.value === '3月' ? '3月主项目次级列为「报量」而非已确认分量，本面板仅展示可确认的夹层分量及独立分层记录；次级报量不计入汇总。' : '独立 3:1 结构化次级原表以亿计，本面板按 1 亿 = 10,000 万换算；表内分量均以万元展示。';
      renderRows(rows);
    }
    input.value = selected || '';
    get('snapshot-label').textContent = `快照 ${snapshot.snapshot_date}`;
    get('footer-date').textContent = ` · 快照日期：${snapshot.snapshot_date}`;
    input.addEventListener('focus',showDropdown);
    input.addEventListener('compositionstart',() => composing = true);
    input.addEventListener('compositionend',() => { composing = false; selected = null; showDropdown(); render(); });
    input.addEventListener('input',() => { if (!composing) { selected = null; showDropdown(); render(); } });
    input.addEventListener('keydown',event => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); if (!dropdown.classList.contains('show')) showDropdown(); moveActive(event.key === 'ArrowDown' ? 1 : -1); }
      else if (event.key === 'Enter' && dropdown.classList.contains('show')) { event.preventDefault(); const items = dropdown.querySelectorAll('.search-item'); if (active >= 0 && items[active]) items[active].click(); }
      else if (event.key === 'Escape') closeDropdown();
    });
    clear.addEventListener('click',() => { input.value = ''; selected = null; render(); input.focus(); });
    month.addEventListener('change',() => { render(); if (dropdown.classList.contains('show')) showDropdown(); });
    document.addEventListener('click',event => { if (!root.contains(event.target) || !event.target.closest('.search-wrap')) closeDropdown(); });
    render();
  })();

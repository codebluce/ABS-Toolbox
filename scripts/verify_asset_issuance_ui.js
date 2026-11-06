// Run against the fully generated desktop and mobile documents, including actual navigation.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.ABS_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [desktop, mobile, output] = process.argv.slice(2);
if (!desktop || !mobile || !output) throw Error('desktop, mobile, output paths required');
fs.mkdirSync(output, {recursive: true});

async function checkBalance(wrapper) {
  assert.deepEqual(await wrapper.locator('[data-view]').allTextContents(), ['ABS发行规模','ABS存量余额']);
  await wrapper.locator('#balance-tab').click();
  const frame=wrapper.frameLocator('#abs-balance-frame');
  await frame.locator('#total').waitFor();
  await frame.locator('#chart').evaluate(svg=>new Promise((resolve,reject)=>{
    let tries=0;function check(){if(Math.abs(svg.viewBox.baseVal.width-svg.getBoundingClientRect().width)<1)return resolve();if(++tries>30)return reject(Error('余额图表尺寸没有更新'));setTimeout(check,50);}check();
  }));
  assert.equal(await frame.locator('#total').textContent(), '2,241');
  assert.equal(await frame.locator('#total-change').textContent(), '较2026-03 -9.5%');
  assert.deepEqual(await frame.locator('#assets .number').allTextContents(), ['811','1,108','190','132']);
  const dates=await frame.locator('#period option').allTextContents();
  assert.equal(dates.length,10);
  assert.ok(dates.every(date=>['03','06','09','12'].includes(date.slice(5,7))));
  assert.ok(!dates.includes('2024-08'));
  for(let i=0;i<10;i++) {
    await frame.locator('#period').selectOption(String(i));
    const labels=await frame.locator('#period option').allTextContents();
    const change=await frame.locator('#total-change').textContent();
    if(i===0)assert.equal(change,'');
    else assert.ok(change.startsWith('较'+labels[10-i]+' '));
    assert.equal(await frame.locator('body').evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  }
  await frame.locator('#assets [data-group="白条"]').click();
  assert.equal(await frame.locator('#rows .asset-row').count(),3);
  await frame.locator('#chart [data-index="9"]').focus();
  assert.equal(await frame.locator('#tip tbody tr').count(),5);
  await frame.locator('#reset').click();
  await frame.locator('#period').selectOption('1');
  await wrapper.locator('#issuance-tab').click();
  assert.equal(await wrapper.frameLocator('#abs-issuance-frame').locator('#issuance-year').inputValue(),'compare');
  await wrapper.locator('#balance-tab').click();
  assert.equal(await frame.locator('#period').inputValue(),'1');
  await frame.locator('#period').selectOption('9');
}

async function check(frame) {
  await frame.locator('#group-chart .group-item').first().waitFor();
  assert.deepEqual(await frame.locator('[data-year]').allTextContents(), ['2026 年', '2025 年', '两年对比']);
  const result = [];
  for (const year of ['2025', '2026']) {
    await frame.locator('#issuance-year').selectOption(year);
    const snapshot = await frame.locator('body').evaluate(() => {
      const data = JSON.parse(document.getElementById('issuance-data').textContent);
      return {data, total: document.getElementById('total').textContent,
        groups: [...document.querySelectorAll('.group-name')].map(e => e.textContent),
        assets: [...document.querySelectorAll('.asset-bar-name')].map(e => e.textContent),
        overflow: document.documentElement.scrollWidth > innerWidth};
    });
    assert.equal(snapshot.overflow, false);
    assert.equal(snapshot.groups.length, 8);
    assert.equal(snapshot.assets.length, year === '2025' ? 21 : 15);
    assert.equal(snapshot.total, year === '2025' ? '2,741' : '1,643');
    const amounts=await frame.locator('#total,.channel-number,.group-value,.asset-num').allTextContents();
    assert.ok(amounts.every(value=>!/[\d,]+\.\d{2}(?!\d)/.test(value)));
    assert.ok(snapshot.groups.includes(year === '2025' ? '融资租赁' : '汽车融资租赁'));
    assert.deepEqual([...snapshot.assets].sort(), snapshot.data[year].assets.map(a => a.name).sort());
    await frame.locator('#group-chart [data-group="京企贷"]').click();
    assert.ok((await frame.locator('#dialog-subtitle').textContent()).includes(year === '2025' ? '30' : '18'));
    await frame.locator('#close-dialog').click();
    await frame.locator('#search').fill('信托金条');
    assert.equal(await frame.locator('.asset-chart-row').count(), 1);
    await frame.locator('#search').fill('');
    await frame.locator('#chart-sort').selectOption('银行间');
    assert.equal(await frame.locator('.asset-bar-name').first().textContent(), '赊销白条');
    await frame.locator('#chart-sort').selectOption('total');
    result.push({year, total: snapshot.total, assets: snapshot.assets.length});
  }
  await frame.locator('#issuance-year').selectOption('compare');
  assert.equal(await frame.locator('.group-compare-row').count(), 8);
  assert.equal(await frame.locator('#compare-body tr').count(), 4);
  assert.equal(await frame.locator('.group-yoy').count(), 8);
  const bars = await frame.locator('.year-bar').evaluateAll(nodes => nodes.map(node => ({
    label: node.querySelector('b').textContent,
    value: node.querySelectorAll('b')[1].textContent
  })));
  assert.deepEqual(bars.map(bar => bar.label), ['2025 同期', '2026 累计']);
  assert.deepEqual(bars.map(bar => bar.value), ['2,539', '1,643']);
  const groupBars = await frame.locator('.group-compare-row').evaluateAll(rows => rows.map(row => ({
    name: row.querySelector('.group-compare-name').textContent,
    values: [...row.querySelectorAll('.group-year-value')].map(node => node.textContent)
  })));
  assert.deepEqual(groupBars.find(item => item.name === '金采').values, ['90', '113']);
  const growth = await frame.locator('body').evaluate(() => {
    const d=JSON.parse(document.getElementById('issuance-data').textContent);
    const cutoff='2025'+d['2026'].asOf.slice(4);
    const previous=d['2025'].records.filter(r=>r.date<=cutoff).reduce((s,r)=>s+r.scale,0);
    return {expected:((d['2026'].total-previous)/previous*100).toFixed(1)+'%',zero:yoy(10,0),bothZero:yoy(0,0),decline:yoy(0,10)};
  });
  assert.equal(await frame.locator('.yoy-row td:last-child').textContent(), growth.expected);
  assert.equal(growth.zero,'新增（同期为0）');
  assert.equal(growth.bothZero,'—');
  assert.equal(growth.decline,'-100.0%');
  const groups = await frame.locator('body').evaluate(() => {
    const d=JSON.parse(document.getElementById('issuance-data').textContent);
    const records=d['2025'].records.filter(r=>r.date<='2025'+d['2026'].asOf.slice(4));
    return d['2026'].groups.filter(g=>g.name!=='其他待归类').map(g=>{
      const name=g.name==='汽车融资租赁'?'融资租赁':g.name;
      const prev=records.filter(r=>r.group===name).reduce((s,r)=>s+r.scale,0);
      const rate=prev ? (g.total-prev)/prev*100 : null;
      return {name, previous:prev.toLocaleString('en-US',{maximumFractionDigits:0}), change:rate===null?(g.total?'新增（同期为0）':'—'):(rate>0?'+':'')+rate.toFixed(1)+'%'};
    });
  });
  const labels=await frame.locator('.group-yoy').allTextContents();
  groups.forEach((g,i)=>{assert.ok(labels[i].includes(g.previous));assert.ok(labels[i].includes(g.change));});

  await frame.locator('.group-year-bar[data-detail-year="2025"][data-group="融资租赁"]').click();
  assert.ok((await frame.locator('#dialog-title').textContent()).includes('2025'));
  assert.ok((await frame.locator('#dialog-subtitle').textContent()).includes('7'));
  await frame.locator('#close-dialog').click();
  return result;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(desktop)).href);
  await page.locator('.tab-button[data-module="asset_overview"]').click();
  assert.equal(await page.locator('.sub-tab-button[data-sub="asset_distribution"]').textContent(), '消金资产');
  assert.deepEqual(await page.locator('.sub-tabs-pane[data-module="asset_overview"] button').allTextContents(), ['消金ABS','消金资产','风险表现']);
  assert.equal(await page.locator('.panel.active').getAttribute('data-sub'),'issuance_statistics');
  await page.locator('.sub-tab-button[data-sub="issuance_statistics"]').click();
  const desktopWrapper = page.frameLocator('#issuance-statistics-frame');
  const desktopFrame = desktopWrapper.frameLocator('#abs-issuance-frame');
  const desktopResults = await check(desktopFrame);
  await checkBalance(desktopWrapper);
  await desktopWrapper.locator('#issuance-tab').click();
  await page.screenshot({path: path.join(output, 'desktop-comparison.png')});
  await desktopFrame.locator('#issuance-year').selectOption('2026');
  await page.screenshot({path: path.join(output, 'desktop.png')});
  const source = await page.locator('#issuance-statistics-frame').getAttribute('srcdoc');
  await page.locator('.tab-button[data-module="ledger"]').click();
  await page.evaluate(() => window.ITL_REG['2026'].applySpec({view: 'detail'}));
  assert.equal(await page.locator('#itl-root-2026 .itl-detail tbody tr').count(), 500);

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(pathToFileURL(path.resolve(mobile)).href);
  await page.locator('[data-act="tab:asset"]').click();
  assert.deepEqual(await page.locator('[data-act^="assetview:"]').allTextContents(), ['消金ABS','消金资产','风险表现']);
  assert.equal(await page.locator('#m-issuance-statistics-frame').count(),1);
  await page.locator('[data-act="assetview:issuance"]').click();
  const mobileWrapper = page.frameLocator('#m-issuance-statistics-frame');
  const mobileFrame = mobileWrapper.frameLocator('#abs-issuance-frame');
  assert.equal(await page.locator('#m-issuance-statistics-frame').getAttribute('srcdoc'), source);
  const mobileResults = await check(mobileFrame);
  await checkBalance(mobileWrapper);
  await mobileWrapper.locator('#issuance-tab').click();
  await page.screenshot({path: path.join(output, 'mobile-comparison.png')});
  await mobileFrame.locator('#issuance-year').selectOption('2026');
  await page.screenshot({path: path.join(output, 'mobile.png')});
  await page.locator('[data-act="assetview:distribution"]').click();
  assert.equal(await page.locator('#m-issuance-statistics-frame').count(), 0);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'ui-validation.json'), JSON.stringify({status: 'PASS', desktopResults, mobileResults,
    checks: ['desktop subtab', 'mobile subtab', 'same embedded document', 'all assets', 'confirmed grouping', 'project details', 'search', 'sorting', 'two-year comparison', 'no overflow', 'ledger regression'], errors}, null, 2));
  await browser.close();
  console.log('PASS: desktop and mobile issuance statistics');
})().catch(e => { console.error(e); process.exit(1); });

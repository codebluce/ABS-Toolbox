// Run against the fully generated desktop and mobile documents, including actual navigation.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.ABS_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [desktop, mobile, output] = process.argv.slice(2);
if (!desktop || !mobile || !output) throw Error('desktop, mobile, output paths required');
fs.mkdirSync(output, {recursive: true});

async function check(frame) {
  await frame.locator('#group-chart .group-item').first().waitFor();
  assert.deepEqual(await frame.locator('[data-year]').allTextContents(), ['2026 年', '2025 年', '两年对比']);
  const result = [];
  for (const year of ['2025', '2026']) {
    await frame.locator('[data-year="' + year + '"]').click();
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
    assert.equal(snapshot.total, year === '2025' ? '2,740.69' : '1,643.11');
    assert.ok(snapshot.groups.includes(year === '2025' ? '融资租赁' : '汽车融资租赁'));
    assert.deepEqual([...snapshot.assets].sort(), snapshot.data[year].assets.map(a => a.name).sort());
    await frame.locator('#group-chart [data-group="京企贷"]').click();
    assert.ok((await frame.locator('#dialog-subtitle').textContent()).includes(year === '2025' ? '30.00' : '18.00'));
    await frame.locator('#close-dialog').click();
    await frame.locator('#search').fill('信托金条');
    assert.equal(await frame.locator('.asset-chart-row').count(), 1);
    await frame.locator('#search').fill('');
    await frame.locator('#chart-sort').selectOption('银行间');
    assert.equal(await frame.locator('.asset-bar-name').first().textContent(), '赊销白条');
    await frame.locator('#chart-sort').selectOption('total');
    result.push({year, total: snapshot.total, assets: snapshot.assets.length});
  }
  await frame.locator('[data-year="compare"]').click();
  assert.equal(await frame.locator('.group-compare-row').count(), 8);
  assert.equal(await frame.locator('#compare-body tr').count(), 4);
  assert.equal(await frame.locator('.group-yoy').count(), 8);
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
      return {name, previous:prev.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}), change:rate===null?(g.total?'新增（同期为0）':'—'):(rate>0?'+':'')+rate.toFixed(1)+'%'};
    });
  });
  const labels=await frame.locator('.group-yoy').allTextContents();
  groups.forEach((g,i)=>{assert.ok(labels[i].includes(g.previous));assert.ok(labels[i].includes(g.change));});

  await frame.locator('.group-year-bar[data-detail-year="2025"][data-group="融资租赁"]').click();
  assert.ok((await frame.locator('#dialog-title').textContent()).includes('2025'));
  assert.ok((await frame.locator('#dialog-subtitle').textContent()).includes('7.10'));
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
  assert.equal(await page.locator('.sub-tab-button[data-sub="consumer_asset"]').textContent(), '消金资产');
  await page.locator('.sub-tab-button[data-sub="issuance_statistics"]').click();
  const desktopFrame = page.frameLocator('#issuance-statistics-frame');
  const desktopResults = await check(desktopFrame);
  await page.screenshot({path: path.join(output, 'desktop-comparison.png')});
  await desktopFrame.locator('[data-year="2026"]').click();
  await page.screenshot({path: path.join(output, 'desktop.png')});
  const source = await page.locator('#issuance-statistics-frame').getAttribute('srcdoc');
  await page.locator('.tab-button[data-module="ledger"]').click();
  await page.evaluate(() => window.ITL_REG['2026'].applySpec({view: 'detail'}));
  assert.equal(await page.locator('#itl-root-2026 .itl-detail tbody tr').count(), 500);

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(pathToFileURL(path.resolve(mobile)).href);
  await page.locator('[data-act="tab:asset"]').click();
  await page.locator('[data-act="assetview:issuance"]').click();
  const mobileFrame = page.frameLocator('#m-issuance-statistics-frame');
  assert.equal(await page.locator('#m-issuance-statistics-frame').getAttribute('srcdoc'), source);
  const mobileResults = await check(mobileFrame);
  await page.screenshot({path: path.join(output, 'mobile-comparison.png')});
  await mobileFrame.locator('[data-year="2026"]').click();
  await page.screenshot({path: path.join(output, 'mobile.png')});
  await page.locator('[data-act="assetview:consumer"]').click();
  assert.equal(await page.locator('#m-issuance-statistics-frame').count(), 0);
  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'ui-validation.json'), JSON.stringify({status: 'PASS', desktopResults, mobileResults,
    checks: ['desktop subtab', 'mobile subtab', 'same embedded document', 'all assets', 'confirmed grouping', 'project details', 'search', 'sorting', 'two-year comparison', 'no overflow', 'ledger regression'], errors}, null, 2));
  await browser.close();
  console.log('PASS: desktop and mobile issuance statistics');
})().catch(e => { console.error(e); process.exit(1); });

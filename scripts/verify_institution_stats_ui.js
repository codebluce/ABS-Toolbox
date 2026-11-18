// 机构画像 > 机构统计：管理人表投行认购按角色拆三列（电脑端 + 手机端）。
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.ABS_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [desktop, mobile, output] = process.argv.slice(2);
if (!desktop || !mobile || !output) throw Error('desktop, mobile, output paths required');
fs.mkdirSync(output, {recursive: true});

async function checkDesktop(page) {
  await page.locator('.tab-button[data-module="progress"]').click();
  await page.locator('button[data-sub="inst_stats"]').click();
  const manager = page.locator('.inst-stats-block--manager');
  await manager.waitFor();
  const headText = await manager.locator('thead').innerText();
  assert.ok(headText.includes('投行认购规模(亿)'), '缺少投行认购分组表头');
  assert.ok(headText.includes('管理人') && headText.includes('销售机构') && headText.includes('合计'));
  const rows = manager.locator('tbody tr');
  assert.equal(await rows.count(), 13);
  const parsed = await manager.locator('tbody tr').evaluateAll(trs => trs.map(tr => {
    const cells = [...tr.querySelectorAll('td')].map(td => td.textContent.trim());
    return {name: cells[0], mgr: Number(cells[4]), sales: Number(cells[5]), total: Number(cells[6]), cols: cells.length};
  }));
  parsed.forEach(r => {
    assert.equal(r.cols, 7, r.name + ' 列数不是 7');
    assert.ok(Math.abs(r.mgr + r.sales - r.total) < 0.005, r.name + ' 合计≠管理人+销售');
  });
  const byName = Object.fromEntries(parsed.map(r => [r.name, r]));
  assert.equal(byName['中信证券'].mgr, 1.27);
  assert.equal(byName['中信证券'].sales, 2.09);
  assert.equal(byName['中信证券'].total, 3.36);
  assert.equal(byName['国信证券'].sales, 2.65);

  // 销售表仍是 5 列，未被改动
  const salesBlocks = page.locator('.inst-stats-block--sales');
  assert.equal(await salesBlocks.count(), 2);
  for (const i of [0, 1]) {
    const cells = await salesBlocks.nth(i).locator('tbody tr').first().locator('td').count();
    assert.equal(cells, 5);
  }

  // 口径一致：交易所 + 银行间两张销售表的投行认购 = 管理人表「销售机构」列
  const marketIb = {};
  for (const i of [0, 1]) {
    const rows = await salesBlocks.nth(i).locator('tbody tr').evaluateAll(trs => trs.map(tr => {
      const cells = [...tr.querySelectorAll('td')].map(td => td.textContent.trim());
      return [cells[0], Number(cells[4])];
    }));
    rows.forEach(([name, value]) => { marketIb[name] = (marketIb[name] || 0) + value; });
  }
  parsed.forEach(r => {
    const actual = Math.round((marketIb[r.name] || 0) * 100) / 100;
    assert.ok(Math.abs(actual - r.sales) < 0.011,
      `${r.name} 销售表合计 ${actual} ≠ 管理人表销售机构列 ${r.sales}`);
  });
  assert.equal(Math.round((marketIb['中信证券'] || 0) * 100) / 100, 2.09);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, '电脑端横向溢出: ' + overflow);
  return {rows: parsed.length, sample: byName['中信证券'], overflow};
}

async function checkMobile(page) {
  await page.locator('[data-act="tab:progress"]').click();
  await page.locator('[data-act="sub:inst_stats"]').click();
  await page.waitForTimeout(300);
  const text = await page.locator('body').innerText();
  assert.ok(text.includes('投行认购 3.36 亿'), '手机端合计缺失');
  assert.ok(text.includes('管理人 1.27 亿 · 销售机构 2.09 亿'), '手机端角色拆分缺失');
  assert.ok(text.includes('管理人 0.03 亿 · 销售机构 2.65 亿'), '国信证券角色拆分缺失');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, '手机端横向溢出: ' + overflow);
  return {overflow};
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(desktop)).href);
  const desktopResult = await checkDesktop(page);
  await page.screenshot({path: path.join(output, 'desktop-inst-stats.png')});

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(pathToFileURL(path.resolve(mobile)).href);
  const mobileResult = await checkMobile(page);
  await page.screenshot({path: path.join(output, 'mobile-inst-stats.png')});

  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'inst-stats-ui-validation.json'), JSON.stringify({
    status: 'PASS', desktopResult, mobileResult,
    checks: ['管理人表 7 列', '投行认购分组表头', '合计=管理人+销售', '销售表仍 5 列', '手机端角色拆分', '无横向溢出'],
    errors}, null, 2));
  await browser.close();
  console.log('PASS: institution stats role split (desktop + mobile)');
})().catch(e => { console.error(e); process.exit(1); });

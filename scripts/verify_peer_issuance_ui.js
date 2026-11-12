// 同业发行面板：电脑端与手机端一致性校验（卡片顺序、期限拆分利率、最近一笔发行）。
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.ABS_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [desktop, mobile, output] = process.argv.slice(2);
if (!desktop || !mobile || !output) throw Error('desktop, mobile, output paths required');
fs.mkdirSync(output, {recursive: true});

const EXPECTED = ['网商贷', '蚂蚁花呗', '蚂蚁借呗', '蚂蚁经营贷', '抖音放心借·小微', '抖音放心借·消费',
  '抖音月付', '腾讯分付', '微众银行微粒贷', '微众银行微业贷', '美团月付', '美团生活费', '美团生意贷',
  '京东白条', '京东现金贷', '京东企业主贷', '京东动产质押', '京东京企贷'];

async function checkDesktop(page) {
  await page.locator('.tab-button[data-module="peer_issuance"]').click();
  const panel = page.locator('.panel[data-module="peer_issuance"]');
  await panel.locator('.peer-issuance-card').first().waitFor();
  const names = await panel.locator('.peer-issuance-card h3').allTextContents();
  assert.deepEqual(names, EXPECTED);
  assert.equal(await panel.locator('.peer-issuance-card').count(), EXPECTED.length);
  const text = await panel.innerText();
  assert.ok(!text.includes('度小满'), '度小满卡片应已删除');
  assert.ok(!text.includes('中融小贷'), '中融小贷应并入海豚小贷');
  assert.ok(text.includes('海豚小贷'), '海豚小贷应作为合并后的权益人展示');
  assert.ok(!text.includes('基础资产发行 Top'), '不应保留 Top N 标题');
  assert.ok(text.includes('主要资产发行明细'));
  assert.ok(text.includes('统计范围：京东金条、京东自主支付资产、京东金条白取混池'));
  const legends = await panel.locator('.peer-issuance-card .peer-rate-legend').count();
  assert.equal(legends, EXPECTED.length);
  const latestRows = await panel.locator('.peer-issuance-card .peer-latest-row').count();
  assert.equal(latestRows, EXPECTED.length * 2);
  const firstCard = panel.locator('.peer-issuance-card').first();
  const legendText = await firstCard.locator('.peer-rate-legend').innerText();
  assert.ok(legendText.includes('1年期（≤1.1年）'));
  assert.ok(legendText.includes('2年期（>1.1年）'));
  assert.match(legendText, /\d+\.\d{2}%/);
  const latestText = await firstCard.locator('.peer-latest-list').innerText();
  assert.match(latestText, /AAA年限 \d+\.\d{2}年 · 发行规模 [\d,]+ 亿/);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, '电脑端出现横向溢出: ' + overflow);
  return {names, legends, latestRows, overflow};
}

async function checkMobile(page) {
  await page.locator('[data-act="tab:peer"]').click();
  await page.locator('[data-act="pv:top"]').click();
  const cards = page.locator('[data-act^="pt:"]');
  await cards.first().waitFor();
  assert.equal(await cards.count(), EXPECTED.length);
  const first = await cards.first().innerText();
  assert.ok(first.includes('网商贷'));
  assert.ok(first.includes('1年期'));
  assert.ok(first.includes('2年期'));
  assert.ok(first.includes('AAA年限'));
  assert.ok(!first.includes('Top'));
  assert.ok(!(await page.locator('body').innerText()).includes('中融小贷'));
  const jd = await cards.nth(EXPECTED.indexOf('京东现金贷')).innerText();
  assert.ok(jd.includes('统计范围：京东金条、京东自主支付资产、京东金条白取混池'));
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, '手机端出现横向溢出: ' + overflow);
  return {cards: await cards.count(), overflow};
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(desktop)).href);
  const desktopResult = await checkDesktop(page);
  await page.locator('.panel[data-module="peer_issuance"] .peer-issuance-block-title').scrollIntoViewIfNeeded();
  await page.screenshot({path: path.join(output, 'desktop-peer-cards.png')});

  await page.setViewportSize({width: 390, height: 844});
  await page.goto(pathToFileURL(path.resolve(mobile)).href);
  const mobileResult = await checkMobile(page);
  await page.screenshot({path: path.join(output, 'mobile-peer-cards.png')});

  assert.deepEqual(errors, []);
  fs.writeFileSync(path.join(output, 'peer-ui-validation.json'), JSON.stringify({
    status: 'PASS', desktopResult, mobileResult,
    checks: ['18 张卡片顺序', '度小满已删除', '京东现金贷合并口径', '期限拆分利率图例', '最近一笔发行明细',
      '无 Top N 标题', '电脑端无横向溢出', '手机端无横向溢出'], errors}, null, 2));
  await browser.close();
  console.log('PASS: desktop and mobile peer issuance cards');
})().catch(e => { console.error(e); process.exit(1); });

// 运行真实面板 JS/CSS；合成业务边界与已有 HTML 快照均只写入临时目录。
// node scripts/lab/test_monthly_bid_ui.js [--artifact <本地HTML>] [--keep-artifacts]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.MONTHLY_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const root = path.resolve(__dirname, '../..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const script = read('scripts/lab/monthly_bid_institutions_demo.js');
const css = read('scripts/lab/monthly_bid_institutions_demo.css');
const groups = ['理财子', '银行', '公募基金', '券商', '其他'];
const attack = '</ScRiPt><img src=x onerror="window.__monthlyXss=1"><script>window.__monthlyXss=2</script>&<>\'"\\u003c\u2028\u2029';
const encode = value => JSON.stringify(value).replace(/</g, '\\u003c').replace(/&/g, '\\u0026');
const record = (size, track, row, rawInstitution = '组合机构', month = 3) => ({
  size, track, row, rawInstitution, date:`2026-0${month}-04`,
  project:track === 'bids' ? '申购项目' : '配售补充项目', venue:'银行间'
});
function institution(name, group, entries, allocationShare, allocatedSize, participationRate = 0.2) {
  const months = Array.from({length:12}, (_,month) => entries[month] || []);
  return {name, group, months, monthlySizes:months.map(records => records.reduce((sum,r) => sum+r.size,0)),
    // 故意保留 v8 的 mixed 错误标记；UI 必须独立从逐笔轨道识别 mixed。
    monthlyTracks:months.map(records => records.some(r => r.track === 'bids') ? 'bids' : records.length ? 'allocations' : ''),
    allocationShare, allocatedSize, participationRate, participationCount:1,
    monthCount:months.filter(records => records.length).length};
}
function synthetic() {
  const project = (name, date) => ({name, date, size:10, venue:'银行间', manager:'测试管理人', tenor:'1年',
    tiers:[{name:'优先A', costs:[0.02], bids:[{institution:'项目申购机构', rate:0.02, bidSize:2}],
      allocations:[{institution:'项目配售机构', cost:0.02, share:1}]}]});
  const assets = [
    {name:'赊销白条', projects:[project('当前项目一','2026-10-16'),project('当前项目二','2026-10-15')]},
    {name:'京企贷', projects:[project('仅2025资产最近项目','2025-12-04')]},
    {name:'金采', projects:[project('另一历史资产','2025-11-04')]},
    {name:'动产质押', projects:[project('未知配售金额项目','2026-10-16')]}
  ].map(asset => ({...asset, date:asset.projects[0].date, dates:asset.projects.map(p => p.date)}));
  const institutions = [
    institution('组合机构','理财子',{2:[record(2,'bids',2),record(3,'allocations',3)],3:[record(0.000001,'bids',4)]},4/140,4,0.4),
    institution('真实小额获配','理财子',{0:[record(0.05,'bids',5)]},0.05/140,0.05,0.0005),
    institution('确实未获配','理财子',{1:[record(0.2,'allocations',6)]},0,0,0),
    institution('未知配售','理财子',{4:[record(0.3,'bids',7)]},null,null,null),
    institution(attack,'银行',{0:[{...record(0.4,'bids',8,attack), project:attack, date:attack, row:attack},
      ...Array.from({length:40},(_,i) => ({...record(0.01,'bids',100+i,attack),project:attack}))]},0.001,0.14),
    institution('隐藏券商','券商',{0:[record(100,'bids',9,'隐藏券商')]},0.96,135.81)
  ];
  for (let i=0;i<60;i++) institutions.splice(4,0,institution(`键盘机构${String(i).padStart(2,'0')}`,'银行',
    {2:[record(0.1,'bids',10+i,`键盘机构${i}`)]},0,0));
  const counts = Array.from({length:12}, (_,month) => institutions.filter(inst => inst.months[month].length).length);
  const visibleCounts = Array.from({length:12}, (_,month) => institutions.filter(inst => groups.slice(0,3).includes(inst.group) && inst.months[month].length).length);
  const incomplete = {...institutions[3],knownAllocatedSize:0.02};
  return {
    data:{assets, source:'本地合成测试', asOf:'2026-10-16'},
    monthly:{year:2026, groups, auditQc:{status:'FAIL'},releaseBlocked:true,assets:{赊销白条:{institutions, counts, visibleCounts, visibleGroups:groups.slice(0,3),
      bubbleMaxSize:5, projectCount:5, projectCounts:Array(12).fill(0), totalAllocatedSize:140, bidCount:66, fallbackCount:2},
      动产质押:{institutions:[incomplete],counts:Array(12).fill(1),visibleCounts:Array(12).fill(1),visibleGroups:groups,
        bubbleMaxSize:0.3,projectCount:1,projectCounts:Array(12).fill(0),totalAllocatedSize:null,totalKnownAllocatedSize:8,
        bidCount:1,fallbackCount:0}}}
  };
}
function documentFor(data, monthly) {
  let body = read('scripts/latest_bookkeeping_panel_body.html');
  const row = body.match(/    <div class="lb-project-row">.*?<\/div>\n/)[0];
  body = body.replace(row, `    <section class="lb-monthly" aria-labelledby="lb-monthly-title">
      <div class="lb-monthly-heading"><h2 id="lb-monthly-title">2026年月度投标机构</h2>
        <div class="lb-monthly-actions"><input id="lb-monthly-search" type="search" aria-label="查找全年投标机构"><button id="lb-monthly-expand" type="button" aria-expanded="false">展开全表</button></div></div>
      <div id="lb-monthly-scroll" class="lb-monthly-scroll" tabindex="0"><table class="lb-monthly-table"><caption class="lb-sr-only">月度投标矩阵</caption><thead id="lb-monthly-head"></thead><tbody id="lb-monthly-rows"></tbody></table></div>
      <div class="lb-monthly-note">旧说明0%为未获配</div></section>
  `);
  body = body.replace('  <section class="lb-card lb-project-summary"', '<section class="lb-card lb-project-block"><div class="lb-project-block-heading"><h2>最近项目簿记</h2>'+row+'</div><section class="lb-card lb-project-summary"');
  body = body.replace('  <p class="lb-preview-note">', '</section><p class="lb-preview-note">');
  return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;}'+read('scripts/latest_bookkeeping_panel.css')+css+'</style></head><body><section id="latest-bookkeeping">'
    + '<div class="lb-monthly-qc-banner" data-qc-status="FAIL" role="alert">数据核验存在待确认金额冲突，暂不能上线</div>'+body+'</section>'
    + '<script>window.__monthlyXss=0;</script><script id="lb-data" type="application/json">'+encode(data)+'</script>'
    + '<script>'+read('scripts/latest_bookkeeping_panel.js')+'</script><script id="lb-monthly-data" type="application/json">'+encode(monthly)+'</script><script>'+script+'</script></body></html>';
}
function snapshotWithCurrentUI(html) {
  const marker = /<script id="lb-monthly-data" type="application\/json">[\s\S]*?<\/script><script>[\s\S]*?<\/script>/g;
  assert.equal([...html.matchAll(marker)].length,1,'快照必须恰有一个月度数据及脚本块');
  const baselinePath = path.join(root,'audit/monthly_bookkeeping_20261017/baseline/scripts/lab/monthly_bid_institutions_demo.css');
  const baselineCSS = fs.existsSync(baselinePath) ? fs.readFileSync(baselinePath,'utf8') : css;
  assert.ok(html.includes(baselineCSS),'v8 CSS 快照应与基线一致');
  return html.replace(baselineCSS, () => css).replace(marker, match => match.slice(0,match.indexOf('</script>')+9)+'<script>'+script+'</script>');
}
async function verifyColumns(page) {
  const layout = await page.evaluate(() => ({head:document.querySelector('#lb-monthly-head tr').children.length,
    institutions:[...document.querySelectorAll('.lb-monthly-institution')].map(row => row.children.length),
    spans:[...document.querySelectorAll('#lb-monthly-rows [colspan]')].map(cell => cell.colSpan)}));
  assert.equal(layout.head,15);
  assert.ok(layout.institutions.every(count => count === 15));
  assert.ok(layout.spans.every(count => count === 15));
}
async function verifySynthetic(page, dir) {
  const {data,monthly} = synthetic();
  const file = path.join(dir,'synthetic.html');
  fs.writeFileSync(file,documentFor(data,monthly));
  await page.goto(pathToFileURL(file).href);
  await verifyColumns(page);
  assert.equal(await page.locator('.lb-monthly-institution').count(),65);
  const mixed = page.locator('.lb-monthly-bubble[data-track="mixed"]');
  assert.equal(await mixed.count(),1);
  assert.equal(await mixed.getAttribute('data-size'),'5');
  const mixedTitle = await mixed.getAttribute('title');
  for (const text of ['展示规模合计 5亿元','申购 2亿元','实际配售补充 3亿元','总表W2:Y2','总表U3:V3']) assert.ok(mixedTitle.includes(text));
  assert.ok(!mixedTitle.includes('申购合计 5亿元'));
  const dimensions = await page.locator('.lb-monthly-bubble').evaluateAll(elements => elements.map(element => {
    const style = getComputedStyle(element);
    return {size:Number(element.dataset.size), width:parseFloat(element.style.width), height:parseFloat(element.style.height),renderedWidth:parseFloat(style.width),
      color:style.backgroundColor, radius:style.borderRadius, image:style.backgroundImage};
  }));
  for (const bubble of dimensions) {
    assert.equal(bubble.width,Number(Math.max(3,26*Math.sqrt(bubble.size/5)).toFixed(2)));
    assert.equal(bubble.height,bubble.width);
    assert.ok(Math.abs(bubble.renderedWidth-bubble.width)<0.025,'浏览器实际尺寸只允许亚像素舍入差');
    assert.equal(bubble.color,'rgb(37, 99, 168)');
    assert.equal(bubble.radius,'50%');
    assert.equal(bubble.image,'none');
  }
  assert.ok(dimensions.some(bubble => bubble.width === 3),'极小正金额保留3px下限');
  const instRow = name => page.locator('.lb-monthly-institution').filter({has:page.locator('th', {hasText:name})});
  assert.equal(await instRow('真实小额获配').locator('td').nth(12).textContent(),'<0.1%');
  assert.equal(await instRow('真实小额获配').locator('td').nth(13).textContent(),'<0.1%');
  assert.ok((await instRow('真实小额获配').locator('td').nth(13).getAttribute('title')).includes('140亿元'));
  assert.equal(await instRow('确实未获配').locator('td').nth(13).textContent(),'0.0%');
  assert.equal(await instRow('未知配售').locator('td').nth(12).textContent(),'—');
  assert.equal(await instRow('未知配售').locator('td').nth(13).textContent(),'—');
  assert.ok((await instRow('未知配售').locator('td').nth(13).getAttribute('title')).includes('未知'));
  assert.ok(!(await instRow('未知配售').locator('td').nth(13).getAttribute('title')).includes('机构全年实际配售0亿元'));
  assert.equal(await page.locator('.lb-monthly-qc-banner').textContent(),'数据核验存在待确认金额冲突，暂不能上线');
  assert.equal(await page.locator('.lb-monthly-qc-banner').getAttribute('data-qc-status'),'FAIL');
  assert.equal(await page.locator('.lb-monthly-qc-banner').getAttribute('role'),'alert');
  assert.equal(await page.locator('.lb-monthly-qc-banner').evaluate(el => getComputedStyle(el).borderLeftWidth),'4px');
  assert.equal(await page.locator('img').count(),0);
  assert.equal(await page.evaluate(() => window.__monthlyXss),0);
  const attackRow = page.locator('.lb-monthly-institution').last();
  assert.equal(await attackRow.locator('th').textContent(),attack);
  const attackBubble = attackRow.locator('.lb-monthly-bubble');
  await attackBubble.focus();
  assert.ok((await page.locator('#lb-monthly-tooltip').textContent()).includes(attack));
  assert.equal(await page.locator('#lb-monthly-tooltip img').count(),0);
  await page.keyboard.press('PageDown');
  assert.ok(await page.locator('#lb-monthly-tooltip').evaluate(el => el.scrollTop>0),'长详情可通过键盘滚动');
  await page.keyboard.press('PageUp');
  assert.equal(await page.locator('#lb-monthly-tooltip').evaluate(el => el.scrollTop),0);
  assert.equal(await page.locator('.lb-monthly-bubble[tabindex="0"]').count(),1);

  // 从搜索框出发，只有容器与一个气泡入口，后续靠方向键导航。
  await page.locator('#lb-monthly-search').focus();
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id),'lb-monthly-expand');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id),'lb-monthly-scroll');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.classList.contains('lb-monthly-bubble')),true);
  await page.keyboard.press('Home');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.track),'mixed');
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),true);
  assert.equal(await mixed.getAttribute('aria-describedby'),'lb-monthly-tooltip');
  await page.keyboard.press('ArrowRight');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.month),'3');
  await page.keyboard.press('ArrowLeft');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.track),'mixed');
  await page.keyboard.press('ArrowDown');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.row),'1');
  await page.keyboard.press('ArrowUp');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.month),'2');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),false);
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),true);
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement.id),'lb-project');
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),false);
  await mixed.hover();
  assert.equal(await page.locator('#lb-monthly-tooltip').textContent(),mixedTitle);
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),true);

  // 最近项目、明细口径切换不应重建全年月表。
  await page.locator('#lb-project').hover();
  const matrix = await page.locator('#lb-monthly-rows').innerHTML();
  await page.selectOption('#lb-project','1');
  await page.locator('[data-view="allocations"]').click();
  assert.equal(await page.locator('#lb-project-name').textContent(),'当前项目二');
  assert.equal(await page.locator('#lb-monthly-rows').innerHTML(),matrix);
  await page.locator('[data-asset="1"]').click();
  assert.equal(await page.locator('#lb-project-name').textContent(),'仅2025资产最近项目');
  assert.equal(await page.locator('.lb-monthly-bubble').count(),0);
  assert.equal(await page.locator('.lb-monthly-group').count(),5);
  assert.equal(await page.locator('#lb-monthly-head tr th').nth(13).textContent(),'参与率0个项目');
  assert.ok((await page.locator('#lb-monthly-head tr th').nth(14).getAttribute('title')).includes('0亿元'));
  assert.ok((await page.locator('#lb-monthly-rows').textContent()).includes('2026年无数据'));
  assert.ok(!(await page.locator('#lb-monthly-rows').textContent()).includes('组合机构'));
  assert.equal(await page.locator('#lb-monthly-head tr th span').allTextContents().then(texts => texts.slice(0,12).every(text => text === '无数据')),true);
  await verifyColumns(page);
  await page.locator('[data-asset="2"]').click();
  assert.equal(await page.locator('.lb-monthly-group').count(),3);
  await verifyColumns(page);
  await page.locator('[data-asset="3"]').click();
  assert.equal(await page.locator('.lb-monthly-institution td').nth(13).textContent(),'—');
  const unknownTitle = await page.locator('.lb-monthly-institution td').nth(13).getAttribute('title');
  for (const text of ['未披露','机构已知部分0.02亿元','资产已知部分8亿元']) assert.ok(unknownTitle.includes(text));
  assert.ok(!(await page.locator('#lb-monthly-head th').nth(14).getAttribute('title')).includes('合计0亿元'));
  assert.ok((await page.locator('#lb-monthly-head th').nth(14).getAttribute('title')).includes('已知部分8亿元'));
  await verifyColumns(page);
  await page.locator('[data-asset="0"]').click();
  assert.equal(await page.locator('.lb-monthly-bubble[data-track="mixed"]').count(),1);
  await page.locator('#lb-monthly-search').fill('不存在');
  assert.equal(await page.locator('.lb-monthly-bubble').count(),0);
  assert.equal(await page.locator('#lb-monthly-tooltip').isVisible(),false);
  await page.locator('#lb-monthly-search').fill('');
  assert.equal(await page.locator('.lb-monthly-bubble[tabindex="0"]').count(),1);

  await page.locator('#lb-monthly-expand').click();
  assert.equal(await page.locator('#lb-monthly-expand').getAttribute('aria-expanded'),'true');
  assert.equal(await page.locator('#lb-monthly-expand').textContent(),'收起月表');
  assert.equal(await page.locator('#lb-monthly-expand').getAttribute('aria-controls'),'lb-monthly-scroll');
  await page.locator('#lb-monthly-scroll').evaluate(el => { el.scrollTop = 700; });
  const sticky = await page.evaluate(() => {
    const container = document.getElementById('lb-monthly-scroll');
    const head = document.getElementById('lb-monthly-head');
    return {height:container.clientHeight, viewport:innerHeight, max:getComputedStyle(container).maxHeight,
      head:head.getBoundingClientRect().top, top:container.getBoundingClientRect().top,
      scrolled:container.scrollTop, remaining:container.scrollHeight>container.clientHeight};
  });
  assert.ok(sticky.height<=sticky.viewport*0.7+1 && sticky.height>310);
  assert.ok(sticky.remaining && sticky.scrolled>0 && sticky.max !== 'none');
  assert.ok(Math.abs(sticky.head-sticky.top)<3,'展开后的表头随容器内滚动保持固定');
  await page.locator('#lb-monthly-expand').click();
  assert.equal(await page.locator('#lb-monthly-expand').textContent(),'扩大月表');
  assert.equal(await page.locator('#lb-monthly-expand').getAttribute('aria-expanded'),'false');
  for (const width of [1440,1024,390]) {
    await page.setViewportSize({width,height:1000});
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),'页面不能横向溢出');
    await verifyColumns(page);
  }
  await page.screenshot({path:path.join(dir,'synthetic-narrow.png')});
  // 初始资产也可全年缺省，必须直接显示空态，而非等点击才修复。
  const initialFile = path.join(dir,'initial-empty.html');
  fs.writeFileSync(initialFile,documentFor({...data,assets:[data.assets[1]]},{...monthly,assets:{}}));
  await page.goto(pathToFileURL(initialFile).href);
  assert.equal(await page.locator('.lb-monthly-group').count(),5);
  assert.equal(await page.locator('.lb-monthly-bubble').count(),0);
  assert.ok((await page.locator('#lb-monthly-rows').textContent()).includes('2026年无数据'));
  await verifyColumns(page);
  return {visibleInstitutions:65,mixedBubbles:1,emptyGroups:[5,3],minDiameter:3,columns:15};
}
async function verifyReal(page, file) {
  await page.setViewportSize({width:1440,height:1000});
  await page.goto(pathToFileURL(file).href);
  await page.evaluate(() => {
    if (typeof selectModule === 'function' && typeof selectSub === 'function') {
      selectModule('pricing'); selectSub('bookkeeping');
    }
  });
  const {data,monthly} = await page.evaluate(() => ({data:JSON.parse(document.getElementById('lb-data').textContent),
    monthly:JSON.parse(document.getElementById('lb-monthly-data').textContent)}));
  const percent = value => value == null ? '—' : value>0 && value<0.001 ? '<0.1%' : (value*100).toFixed(1)+'%';
  let bubbleCount = 0, projectCount = 0;
  for (let a=0;a<data.assets.length;a++) {
    await page.locator('[data-asset="'+a+'"]').click();
    const asset = monthly.assets[data.assets[a].name];
    const visible = asset.institutions.filter(inst => asset.visibleGroups.includes(inst.group));
    const rendered = await page.locator('.lb-monthly-institution').evaluateAll(rows => rows.map(row => ({
      name:row.children[0].textContent, participation:row.children[13].textContent, share:row.children[14].textContent
    })));
    assert.deepEqual(rendered,visible.map(inst => ({name:inst.name, participation:percent(inst.participationRate),share:percent(inst.allocationShare)})));
    await verifyColumns(page);
    const bubbles = await page.locator('.lb-monthly-bubble').evaluateAll(elements => elements.map(el => ({
      size:Number(el.dataset.size), track:el.dataset.track, title:el.title,
      width:parseFloat(el.style.width), height:parseFloat(el.style.height), color:getComputedStyle(el).backgroundColor
    })));
    let b=0;
    for (const inst of visible) for (let month=0;month<12;month++) {
      const records = inst.months[month];
      if (!records.length) continue;
      const bubble = bubbles[b++];
      const size = records.reduce((sum,record) => sum+record.size,0);
      const hasBids = records.some(record => record.track === 'bids');
      const hasAllocations = records.some(record => record.track === 'allocations');
      assert.ok(Math.abs(bubble.size-size)<1e-9);
      assert.equal(bubble.width,Number(Math.max(3,26*Math.sqrt(size/asset.bubbleMaxSize)).toFixed(2)));
      assert.equal(bubble.height,bubble.width);
      assert.equal(bubble.color,'rgb(37, 99, 168)');
      assert.equal(bubble.track,hasBids && hasAllocations ? 'mixed' : hasBids ? 'bids' : 'allocations');
      for (const record of records) assert.ok(bubble.title.includes(`总表${record.track === 'bids' ? 'W' : 'U'}${record.row}:${record.track === 'bids' ? 'Y' : 'V'}${record.row}`));
    }
    assert.equal(b,bubbles.length);
    bubbleCount += b;
    assert.equal(await page.locator('.lb-monthly-bubble[tabindex="0"]').count(),b ? 1 : 0);
    const matrix = await page.locator('#lb-monthly-rows').innerHTML();
    for (let p=0;p<data.assets[a].projects.length;p++) {
      await page.selectOption('#lb-project',String(p));
      assert.equal(await page.locator('#lb-project-name').textContent(),data.assets[a].projects[p].name);
      for (const view of ['bids','allocations']) {
        await page.locator('[data-view="'+view+'"]').click();
        assert.equal(await page.locator('#lb-rows tr').count(),data.assets[a].projects[p].tiers.reduce((total,tier) => total+tier[view].length,0));
        assert.equal(await page.locator('#lb-monthly-rows').innerHTML(),matrix);
      }
      projectCount++;
    }
  }
  return {assets:data.assets.length,projects:projectCount,bubbles:bubbleCount};
}
async function main() {
  const args = process.argv.slice(2);
  const keep = args.includes('--keep-artifacts');
  const supplied = args.includes('--artifact') ? args[args.indexOf('--artifact')+1] : null;
  const defaultSnapshot = path.join(root,'deliverables/dashboards/01_latest/ABS综合看板_20261016.html');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'monthly-bid-ui-'));
  const browser = await chromium.launch({headless:true,executablePath:process.env.MONTHLY_UI_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [], requests = [];
    page.on('pageerror',error => errors.push(error.message));
    await page.route(/^https?:\/\//,route => {requests.push(route.request().url());return route.abort();});
    const syntheticResult = await verifySynthetic(page,dir);
    let realResult = null;
    if (supplied) realResult = await verifyReal(page,path.resolve(supplied));
    else if (fs.existsSync(defaultSnapshot)) {
      realResult = await verifyReal(page,defaultSnapshot);
    }
    assert.deepEqual(errors,[]);
    assert.deepEqual(requests,[]);
    const result = {status:'PASS',checkedAt:new Date().toISOString(),synthetic:syntheticResult,real:realResult,
      pageErrors:errors,networkRequests:requests,...(keep ? {artifacts:dir} : {})};
    if (keep) fs.writeFileSync(path.join(dir,'result.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
    if (!keep) fs.rmSync(dir,{recursive:true,force:true});
  }
}
main().catch(error => {console.error(error);process.exitCode=1;});

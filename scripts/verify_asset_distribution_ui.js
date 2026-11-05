const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.ABS_UI_PLAYWRIGHT||'/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const [desktop,mobile,output]=process.argv.slice(2);
if(!desktop||!mobile||!output)throw Error('desktop mobile output required');
fs.mkdirSync(output,{recursive:true});
async function verify(frame){
 await frame.locator('#total').waitFor();
 assert.equal(await frame.locator('#total').textContent(),'5,685');
 assert.equal(await frame.locator('.total span').first().textContent(),'消金资产余额合计');
 assert.equal(await frame.locator('#fund-panels .head .muted').count(),0);
 assert.deepEqual(await frame.locator('.asset-value').allTextContents(),['1,470','3,700','515']);
 assert.equal(await frame.locator('.history,#history-chart,.warning').count(),0);
 assert.ok((await frame.locator('body').textContent()).includes('四舍五入后可能与合计有最多2亿元差'));
 assert.equal(await frame.locator('#fund-panels .row').count(),13);
 for(let i=0;i<12;i++){
  await frame.locator('#period').selectOption(String(i));
  assert.ok(!(await frame.locator('body').innerText()).includes('差额'));
  const order=await frame.locator('#fund-panels .panel').evaluateAll(panels=>panels.map(p=>[...p.querySelectorAll('.num')].map(e=>e.textContent==='—'?null:Number(e.textContent.replace(/,/g,'')))));
  order.forEach(values=>{assert.deepEqual(values,[...values].sort((a,b)=>a===null?(b===null?0:1):b===null?-1:b-a));});
  const styles=await frame.locator('body').evaluate(()=>{
   const aligned=[...document.querySelectorAll('.asset-value-line')].every(e=>{const a=e.querySelector('.asset-value').getBoundingClientRect(),p=e.querySelector('.asset-share').getBoundingClientRect();return a.top<p.bottom&&p.top<a.bottom;});
   return {bg:getComputedStyle(document.querySelector('.total')).backgroundColor,total:getComputedStyle(document.querySelector('#total')).color,black:[...document.querySelectorAll('.asset-value,.asset-share,.num,.pct')].every(e=>getComputedStyle(e).color==='rgb(0, 0, 0)'),aligned,overflow:document.documentElement.scrollWidth>innerWidth};
  });
  assert.equal(styles.bg,'rgb(21, 43, 67)');assert.equal(styles.total,'rgb(255, 255, 255)');assert.ok(styles.black&&styles.aligned&&!styles.overflow);
  const rowFont=await frame.locator('.row').first().evaluate(e=>parseFloat(getComputedStyle(e).fontSize));
  assert.ok(Math.abs(rowFont-(await frame.locator('body').evaluate(()=>innerWidth<=650)?13:14.3))<.05);
 }
 await frame.locator('#period').selectOption('11');
 assert.deepEqual(await frame.locator('#fund-panels .num').allTextContents(),['746','340','268','64','52','1,910','1,540','150','100','307','121','47','40']);
}
(async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1440,height:1050}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(pathToFileURL(path.resolve(desktop)).href);
 await p.locator('.tab-button[data-module="asset_overview"]').click();
 assert.deepEqual(await p.locator('.sub-tabs-pane[data-module="asset_overview"] button').allTextContents(),['发行统计','消金资产','风险表现']);
 assert.equal(await p.locator('.sub-tab-button[data-sub="consumer_asset"]').count(),0);
 await p.locator('.sub-tab-button[data-sub="asset_distribution"]').click();
 await verify(p.frameLocator('#asset-distribution-frame'));
 const document=await p.locator('#asset-distribution-frame').getAttribute('srcdoc');
 await p.screenshot({path:path.join(output,'desktop.png')});
 await p.setViewportSize({width:390,height:844});await p.goto(pathToFileURL(path.resolve(mobile)).href);
 await p.locator('[data-act="tab:asset"]').click();assert.deepEqual(await p.locator('[data-act^="assetview:"]').allTextContents(),['发行统计','消金资产','风险表现']);
 assert.equal(await p.locator('[data-act="assetview:consumer"]').count(),0);
 await p.locator('[data-act="assetview:distribution"]').click();assert.equal(await p.locator('#m-asset-distribution-frame').getAttribute('srcdoc'),document);
 await verify(p.frameLocator('#m-asset-distribution-frame'));await p.screenshot({path:path.join(output,'mobile.png')});
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(output,'distribution-ui.json'),JSON.stringify({status:'PASS',latestTotal:5685,checks:['old panel removed','desktop and mobile tabs','same document','12 time selections','13 fund rows','no history or difference','integer amounts inline with percent','navy total with white number','black numeric values','no overflow'],errors},null,2));
 await b.close();console.log('PASS: asset distribution desktop/mobile replacement');
})().catch(e=>{console.error(e);process.exit(1)});

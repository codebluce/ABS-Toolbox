// Production JS in Chromium, manual synthetic expectations; --artifact verifies a new integrated snapshot.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PRICING_UI_PLAYWRIGHT || '/Users/wupeizhi.nolan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = path.resolve(__dirname, '..');
const production = JSON.parse(execFileSync(path.join(root, '.venv/bin/python'), ['-c',
  'import sys,json;sys.path.insert(0,"scripts");import gen_pricing_insight as p;print(json.dumps({"js":p._PRICING_INSIGHT_JS,"html":p._PRICING_INSIGHT_HTML,"css":p.PRICING_INSIGHT_CSS}))'], {cwd:root,encoding:'utf8'}));
const resource = fs.readFileSync(path.join(root,'scripts/lab/pricing_insight_js.txt'),'utf8');
const makeRow = (changes={}) => {
  const r={product:'1年期赊销白条',asset:'赊销白条',date:'2026-10-16',project:'测试项目',venue:'银行间',layer:'优先A1',month:'2026-10',tenor:'1年期',cost:1.8,spread:.2,inst:'测试机构',share:1,layer_size:8,project_size:10,...changes};
  r.identity_key=JSON.stringify([r.asset,r.date,r.project,r.venue,r.layer]);
  return r;
};
const data=[makeRow(),makeRow({cost:1.9,share:2}),makeRow({layer:'优先A2',layer_size:2}),
 makeRow({date:'2026-10-15',layer_size:4}),makeRow({venue:'上交所',layer_size:5}),
 makeRow({asset:'京企贷',layer_size:10}),makeRow({project:'缺R',layer_size:null}),
 makeRow({date:'2026-09-16',month:'2026-09',layer_size:2}),makeRow({inst:'其他机构',share:4})];
function documentFor(rows, script=production.js) {
 return '<!doctype html><meta charset="utf-8"><style>'+production.css+'</style>'+production.html+
 '<script>const ALL_PRODUCTS=["1年期赊销白条"];const ALL_DATA='+JSON.stringify(rows)+';const PROJECT_SIZES={"测试项目":999};'+script+'</script>';
}
async function manual(page, dir, script, label) {
 const file=path.join(dir,label+'.html'); fs.writeFileSync(file,documentFor(data,script));
 await page.goto(pathToFileURL(file).href);
 const result=await page.evaluate(() => {
   const s=computeWindowStats(['测试机构'],'2026-10-15','2026-10-16')['测试机构'];
   return {count:s.count,share:s.share,costs:s.costs,spreadSum:s.spreadSum,spreadCount:s.spreadCount,ratios:s.ratios,
     a1:layerRatio(ALL_DATA[0]),a2:layerRatio(ALL_DATA[2]),missing:formatLayerRatio(layerRatio(ALL_DATA[6]))};
 });
 assert.equal(result.a1,12.5);assert.equal(result.a2,50);assert.equal(result.missing,'--');
 assert.equal(result.count,7);assert.equal(result.share,8);assert.equal(result.spreadCount,7);
 assert.deepEqual(result.costs,[1.8,1.9,1.8,1.8,1.8,1.8,1.8]);assert.ok(Math.abs(result.spreadSum-1.4)<1e-12);
 assert.deepEqual(result.ratios,[37.5,50,25,20,10]);
 const month=await page.evaluate(() => computeWindowStats(['测试机构'],'2026-09-16','2026-10-16')['测试机构'].ratios);
 assert.deepEqual(month,[37.5,50,25,20,10,50]);
 await page.selectOption('#productSelect','1年期赊销白条');await page.fill('#costInput','2.50');
 await page.evaluate(() => doSearch());
 assert.equal(await page.locator('#resultBody .ratio-cell').nth(0).textContent(),'12.5%');
 assert.ok((await page.locator('#insightBody').textContent()).includes('28.5%'));
 assert.equal(await page.locator('#resultBody .ratio-cell').filter({hasText:'--'}).count(),1);
 for (const value of [-1,0,true,Infinity,'8']) {
   const ratio=await page.evaluate(value => layerRatio({share:1,layer_size:value}),value);assert.equal(ratio,null);
 }
 // Production aggregation must fail conflicts instead of selecting a last quote.
 const conflict=await page.evaluate(() => {
   ALL_DATA.push({...ALL_DATA[0],layer_size:2});
   try {computeWindowStats(['测试机构'],'2026-10-15','2026-10-16');return false;}
   catch(error){return error.message.includes('[R FAIL] conflicting R');}
   finally {ALL_DATA.pop();}
 });assert.equal(conflict,true);
 return {label,count:result.count,ratios:result.ratios,mean:28.5};
}
function panelOnly(html) {
 const start=html.indexOf('<div class="panel" data-module="pricing" data-sub="compare">');
 if (start<0) return html;
 const scriptEnd=html.indexOf('</script>',start)+9;
 assert.ok(scriptEnd>start);
 return '<!doctype html><meta charset="utf-8"><style>'+production.css+'</style>'+html.slice(start,scriptEnd);
}
async function checkReal(page,file,dir,replaceSource=false) {
 let html=panelOnly(fs.readFileSync(file,'utf8'));
 if (replaceSource) {
   const sourceStart=html.indexOf('// ====== HELPERS ======');
   const sourceEnd=html.indexOf('</script>',sourceStart);
   assert.ok(sourceStart>=0 && sourceEnd>sourceStart);
   html=html.slice(0,sourceStart)+production.js+html.slice(sourceEnd);
 }
 const target=path.join(dir,replaceSource?'existing-snapshot-source-check.html':'real-panel.html');
 fs.writeFileSync(target,html);await page.goto(pathToFileURL(target).href);
 const result=await page.evaluate(() => {
   const products=[...ALL_PRODUCTS];populateProducts(products);let checked=0,missing=0;
   for(const product of products){document.getElementById('productSelect').value=product;document.getElementById('costInput').value='2.50';doSearch();
     const rows=ALL_DATA.filter(r=>r.product===product&&r.cost<=2.5).sort((a,b)=>a.date!==b.date?(a.date<b.date?1:-1):a.cost-b.cost);
     const shown=rows.length ? [...document.querySelectorAll('#resultBody .ratio-cell')].map(e=>e.textContent) : [];
     if (!rows.length && document.getElementById('resultArea').style.display !== 'none') throw Error('Empty detail should be hidden');
     const expected=rows.map(r=>r.layer_size==null?'--':(r.share/r.layer_size*100).toFixed(1)+'%');
     if(JSON.stringify(shown)!==JSON.stringify(expected))throw Error('Real detail mismatch '+product);
     checked+=shown.length;missing+=expected.filter(x=>x==='--').length;
   }
   return {products:products.length,checked,missing,hasLayerSize:ALL_DATA.some(r=>Object.hasOwn(r,'layer_size'))};
 });
 if(!replaceSource)assert.equal(result.hasLayerSize,true,'新产物必须含layer_size');
 return result;
}
(async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'pricing-layer-test-'));
 const browser=await chromium.launch({headless:true,executablePath:process.env.PRICING_UI_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 try {
  const page=await browser.newPage();const errors=[],requests=[];
  page.on('pageerror',e=>errors.push(e.message));await page.route(/^https?:\/\//,r=>{requests.push(r.request().url());return r.abort();});
  const synthetic=await manual(page,dir,production.js,'runtime');synthetic.resource=await manual(page,dir,resource,'historical-resource');
  const snapshot=await checkReal(page,path.join(root,'deliverables/dashboards/01_latest/ABS综合看板_20261016.html'),dir,true);
  const args=process.argv.slice(2);let real=null;
  if(args.includes('--artifact'))real=await checkReal(page,path.resolve(args[args.indexOf('--artifact')+1]),dir);
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  console.log(JSON.stringify({status:'PASS',synthetic,existingSnapshotSourceCheck:snapshot,real,pageErrors:errors,networkRequests:requests}));
 } finally {await browser.close();fs.rmSync(dir,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});

// 无浏览器依赖：执行真实面板脚本，验证两种表头、单元格顺序及 CSV。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = new Map();
const node = id => {
  if (!nodes.has(id)) nodes.set(id, {textContent:'', innerHTML:'', value:'', listeners:{},
    addEventListener(type, callback) {this.listeners[type] = callback;}});
  return nodes.get(id);
};
const root = {listeners:{}, querySelector(selector) {return node(selector.slice(1));},
  querySelectorAll() {return [];}, addEventListener(type, callback) {this.listeners[type] = callback;}};
const snapshot = {source:'定稿.xlsx', asOf:'2026-09-21', assets:[{name:'白条',dates:['2026-09-21'],projects:[{
  name:'测试项目',date:'2026-09-21',manager:'管理人',venue:'上交所',size:10,tenor:'21+3',
  tiers:[{name:'优先A',costs:[0.0177],
    bids:[{institution:'报价机构',rate:0.0176,bidSize:2,share:null}],
    allocations:[{institution:'配售机构',share:1.3,rate:null,bidSize:null,cost:0.0177}]}]
}]}]};
node('lb-data').textContent = JSON.stringify(snapshot);
let exported, filename;
const context = {document:{getElementById(id) {return id==='latest-bookkeeping' ? root : node(id);},
  createElement() {return {set download(value) {filename=value;},click(){}};}},
  Blob, URL:{createObjectURL(blob) {exported=blob;return 'blob:test';},revokeObjectURL(){}},
  setTimeout(callback) {callback();}};
vm.runInNewContext(fs.readFileSync(__dirname+'/latest_bookkeeping_panel.js','utf8'),context);
const headers = () => [...node('lb-columns').innerHTML.matchAll(/<th[^>]*>(.*?)<\/th>/g)].map(match=>match[1]);
const cells = () => [...node('lb-rows').innerHTML.matchAll(/<td[^>]*>(.*?)<\/td>/g)].map(match=>match[1].replace(/<[^>]+>/g,''));
async function main() {
  assert.ok(node('lb-project-meta').textContent.includes('项目期限：21+3'));
  assert.ok(node('lb-project').innerHTML.includes('测试项目 · 2026-09-21'));
  assert.ok(node('lb-tie-note').textContent.includes('不足3期'));
  assert.deepEqual(headers(),['档位','机构名称','申购利率','申购规模（亿元）']);
  assert.deepEqual(cells(),['优先A','报价机构','1.76%','2']);
  assert.ok(node('lb-rows').innerHTML.includes('lb-layer-senior-a'));
  for (const [layerName,tone] of [['优先A1','senior-a1'],['优先A2','senior-a2'],['优先B','senior-b'],['中间级','mezzanine'],['次级','junior'],['未分层','neutral']]) {
    assert.equal(vm.runInNewContext(`(${fs.readFileSync(__dirname+'/latest_bookkeeping_panel.js','utf8').match(/const layerTone = (name => \{[\s\S]*?\n  \});/)[1]})('${layerName}')`),tone);
  }
  node('lb-export').listeners.click();
  const bidCsv=await exported.text();
  assert.equal(bidCsv.split('\r\n')[0],'"档位","机构名称","申购利率","申购规模（亿元）"');
  assert.ok(filename.includes('申购明细'));
  root.listeners.click({target:{closest(){return {dataset:{view:'allocations'}};}}});
  assert.deepEqual(headers(),['档位','机构名称','成本利率','配售规模（亿元）']);
  assert.deepEqual(cells(),['优先A','配售机构','1.77%','1.3']);
  node('lb-export').listeners.click();
  const allocationCsv=await exported.text();
  assert.equal(allocationCsv.split('\r\n')[0],'"档位","机构名称","成本利率","配售规模（亿元）"');
  assert.ok(filename.includes('最终配售'));
  node('lb-search').value='不存在';node('lb-search').listeners.input();
  assert.equal(node('lb-rows').innerHTML,'');assert.equal(node('lb-empty').hidden,false);
  assert.equal(node('lb-export').disabled,true);
  console.log('PASS: 申购明细 / 最终配售表头、行数据、CSV及空筛选状态');
}
main().catch(error=>{console.error(error);process.exitCode=1;});

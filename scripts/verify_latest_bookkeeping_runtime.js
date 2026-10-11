// 对真实数据执行实际组件脚本：所有项目/视图/档位/搜索/CSV均验证；不替代视觉检查。
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const mobile = input.mobile === true;
const data = mobile ? input.data : input;
const nodes = new Map();
function el(id) {
  if (!nodes.has(id)) nodes.set(id, {innerHTML:'',textContent:'',value:'',listeners:{},
    addEventListener(type, handler) {this.listeners[type] = handler;}});
  return nodes.get(id);
}
const root={listeners:{},querySelector(selector){return el(selector.slice(1));},querySelectorAll(){return [];},
  addEventListener(type, handler){this.listeners[type]=handler;}};
el('lb-data').textContent=JSON.stringify(data);
let exported,filename;
const context={document:{getElementById(id){return id==='latest-bookkeeping'?root:el(id);},
  createElement(){return {set download(value){filename=value;},click(){}};}},Blob,
  URL:{createObjectURL(blob){exported=blob;return 'blob:check';},revokeObjectURL(){}},setTimeout(fn){fn();}};
const componentScript = mobile ? input.script : fs.readFileSync(__dirname+'/latest_bookkeeping_panel.js','utf8');
vm.runInNewContext(componentScript,context);
const click=dataset=>root.listeners.click({target:{closest(){return {dataset};}}});
const decode=value=>value.replace(/<[^>]*>/g,'').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const shown=()=>[...el('lb-rows').innerHTML.matchAll(/<tr>(.*?)<\/tr>/g)].map(match=>[...match[1].matchAll(/<td[^>]*>(.*?)<\/td>/g)].map(cell=>decode(cell[1])));
const fmt=value=>typeof value==='number'?value.toLocaleString('zh-CN',{maximumFractionDigits:4}):'未披露';
const rate=value=>typeof value==='number'?(value*100).toFixed(2)+'%':value||'未披露';
const quote=value=>'"'+String(value??'').replace(/^[=+\-@\t\r\n]/,"'$&").replace(/"/g,'""')+'"';
async function main(){
  let projects=0,details=0,exports=0,filters=0;
  for (let a=0;a<data.assets.length;a++) {
    click({asset:String(a)});
    for (let p=0;p<data.assets[a].projects.length;p++) {
      el('lb-project').value=String(p);el('lb-project').listeners.change();projects++;
      const project=data.assets[a].projects[p];
      assert.equal(el('lb-project-name').textContent,project.name);
      assert.ok(el('lb-project-meta').textContent.includes(`项目期限：${project.tenor && project.tenor !== '-' ? project.tenor : '未披露'}`));
      for (const view of ['bids','allocations']) {
        click({view});
        const header=view==='bids'?['档位','机构名称','申购利率','申购规模（亿元）']:['档位','机构名称','成本利率','配售规模（亿元）'];
        const rows=project.tiers.flatMap(tier=>tier[view].map(row=>view==='bids'?[tier.name,row.institution,rate(row.rate),fmt(row.bidSize)]:[tier.name,row.institution,rate(row.cost),fmt(row.share)]));
        assert.deepEqual([...el('lb-columns').innerHTML.matchAll(/<th[^>]*>(.*?)<\/th>/g)].map(x=>decode(x[1])),header);
        assert.deepEqual(shown(),rows,`${project.name}/${view}显示明细`);details+=rows.length;
        assert.equal(el('lb-empty').hidden,rows.length>0);
        if(rows.length && !mobile){
          el('lb-export').listeners.click();
          assert.equal(await exported.text(),[header,...rows].map(row=>row.map(quote).join(',')).join('\r\n'));
          assert.ok(filename.includes(project.name));exports++;
        }
        for (const tier of project.tiers) {
          el('lb-layer').value=tier.name;el('lb-layer').listeners.change();
          assert.deepEqual(shown(),rows.filter(row=>row[0]===tier.name));filters++;
        }
        el('lb-layer').value='';el('lb-layer').listeners.change();
        if(rows.length){
          el('lb-search').value=rows[0][1];el('lb-search').listeners.input();
          assert.deepEqual(shown(),rows.filter(row=>row[1].toLowerCase().includes(rows[0][1].toLowerCase())));filters++;
        }
        el('lb-search').value='__不存在的机构校验__';el('lb-search').listeners.input();
        assert.deepEqual(shown(),[]);if(!mobile) assert.equal(el('lb-export').disabled,true);filters++;
        el('lb-search').value='';el('lb-search').listeners.input();
      }
    }
  }
  if(mobile) {
    assert.ok(!componentScript.includes("$('lb-export')"));
    assert.ok(!componentScript.includes('URL.createObjectURL'));
    assert.ok(!componentScript.includes("$('lb-row-count')"));
    const formatter=componentScript.match(/const balancedAssetLabel = (name => \{[\s\S]*?\n  \});/)[1];
    for (const asset of data.assets) {
      const label=vm.runInNewContext('('+formatter+')('+JSON.stringify(asset.name)+')',{esc:s=>s});
      const lines=[...label.matchAll(/<span[^>]*>(.*?)<\/span>/g)].map(m=>m[1]);
      assert.equal(lines.join(''),asset.name);
      if(lines.length===2) {
        assert.ok(lines.every(line=>[...line].length>=2));
        assert.ok(Math.abs([...lines[0]].length-[...lines[1]].length)<=1);
      }
    }
  }
  console.log(JSON.stringify({status:'PASS',projects,details,exports,filters}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});

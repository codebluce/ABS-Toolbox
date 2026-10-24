"""按已确认资产方范围，将华泰公告汇总增量加入完整同业底稿。"""
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
from copy import copy
import argparse, hashlib, json, re
import openpyxl
from peer_issuance_panel import normalize_product_key, parse_dynamics
from supplement_peer_huatai import infer_booking

PARTIES={'京东','蚂蚁','网商银行','腾讯','微众银行','字节','美团','平安普惠','度小满','奇富科技','金城银行','新网银行','滴滴','携程','分期乐'}
NAME_ALIASES={
    '华泰资管诚昕3号4期资产支持专项计划':'华泰资管诚新3号4期资产支持专项计划',
    '华泰资管诚昕3号5期资产支持专项计划':'华泰资管诚新3号5期资产支持专项计划',
}
POSSIBLE_DUPLICATES={
    '深圳市财付通网络金融小额贷款有限公司2026年度和盛第2期定向资产支持票据':
    '深圳市财付通网络金融小额贷款有限公司2026年度和富第2期定向资产支持票据',
}

def decimal(v):
    if v is None or str(v).strip() in {'','-','—'}:return None
    text=str(v).strip()
    if re.fullmatch(r'\d+,\d{1,2}',text):text=text.replace(',','.')
    return Decimal(text)

def huatai_projects(path):
    wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
    projects=[]
    try:
        for sheet in ['交易所-2026年','交易商协会-2026年']:
            exchange=sheet.startswith('交易所-');current=None
            for rownum,row in enumerate(wb[sheet].iter_rows(min_row=2,max_col=13,values_only=True),2):
                if row[1]:
                    raw=row[0]
                    if isinstance(raw,datetime):est=raw.date()
                    elif isinstance(raw,date):est=raw
                    else:est=datetime.strptime(str(raw).strip().replace('/','-'),'%Y-%m-%d').date()
                    current={'product':str(row[1]).strip(),'established':est,'amount':decimal(row[3] if exchange else row[2]),'venue':str(row[2]) if exchange else '银行间','originator':str(row[4] if exchange else row[3]),'manager':str(row[5] if exchange else row[4]),'party':str(row[11] if exchange else row[10]),'asset':str((row[12] if exchange else row[11]) or ''),'sheet':sheet,'row':rownum,'tiers':[]}
                    projects.append(current)
                if current and (row[6] if exchange else row[5]):
                    current['tiers'].append({'layer':str(row[6] if exchange else row[5]),'rating':str(row[9] if exchange else row[8]).strip(),'amount':decimal(row[8] if exchange else row[7]),'term':decimal(row[7] if exchange else row[6]),'rate':decimal(row[10] if exchange else row[9]),'row':rownum})
    finally:wb.close()
    if len({normalize_product_key(x['product']) for x in projects})!=len(projects):raise ValueError('华泰2026项目名重复，拒绝自动加入')
    return projects

def asset_labels(h):
    p,a=h['party'],h['asset']
    if p=='京东':
        if a=='白条':return '京东白条','消金分期类'
        if a=='金条':return '京东金条','消金提现类'
        if a=='金条/白取':return '京东金条白取混池','消金提现类'
        if a=='动产质押':return '京东动产质押','小微toB'
        return '京东'+(a or '资产（待细分）'),'小微toB'
    mapping={
        ('微众银行','微粒贷'):('微众银行微粒贷','消金提现类'),
        ('微众银行','微业贷'):('微众银行微业贷','小微toB'),
        ('蚂蚁','花呗'):('蚂蚁花呗','消金分期类'),
        ('蚂蚁','借呗'):('蚂蚁借呗','消金提现类'),
        ('蚂蚁','小微贷'):('蚂蚁经营贷','小微toB'),
        ('腾讯','分付'):('腾讯分付','消金分期类'),
        ('字节','月付'):('抖音月付','消金分期类'),
        ('字节','放心借小微'):('抖音放心借·小微','小微toC'),
        ('字节','放心借消费'):('抖音放心借·消费','消金提现类'),
    }
    if (p,a) in mapping:return mapping[(p,a)]
    if p=='平安普惠':return '平安普惠经营贷','小微toB'
    if p=='度小满':return '度小满贷款资产（待细分）','小微toB'
    return p+(a or '资产（待细分）'),'未知资产类型'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--huatai',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cutoff',type=date.fromisoformat,required=True)
    args=ap.parse_args()
    original=parse_dynamics(args.source);old={normalize_product_key(r['product']):r for r in original}
    w=openpyxl.load_workbook(args.source);s=w.worksheets[0]
    row_index={normalize_product_key(str(s.cell(r,2).value)):r for r in range(2,s.max_row+1) if s.cell(r,2).value}
    additions=[];excluded=[];duplicates=[];changes=[];renames=[];cross=[]
    raw=w.create_sheet('华泰原值'+args.cutoff.strftime('%m%d'));raw.append(['项目','设立日','资产方','基础资产','项目规模','工作表','项目行','分层','评级','分层规模','期限年','利率百分数','原始分层行'])
    end=max(row_index.values())
    for h in huatai_projects(args.huatai):
        for t in h['tiers']:raw.append([h['product'],h['established'].isoformat(),h['party'],h['asset'],float(h['amount']),h['sheet'],h['row'],t['layer'],t['rating'],float(t['amount']) if t['amount'] is not None else None,float(t['term']) if t['term'] is not None else None,float(t['rate']) if t['rate'] is not None else None,t['row']])
        key=normalize_product_key(h['product'])
        if h['established']>args.cutoff:excluded.append({**h,'reason':'设立日超出文件截止窗口'});continue
        if h['party'] not in PARTIES:excluded.append({**h,'reason':'现有资产方范围外，不扩围'});continue
        aliases=[name for name,target in NAME_ALIASES.items() if target==h['product'] and normalize_product_key(name) in old]
        if key not in old and aliases:
            previous=old[normalize_product_key(aliases[0])]
            # 只有规模、首档利率及设立日都相同，才将文本差异认作同项目。
            aaa=[t for t in h['tiers'] if t['rating'].startswith('AAA')]
            rr=row_index[normalize_product_key(aliases[0])];old_est=s.cell(rr,10).value
            old_date=old_est.date() if isinstance(old_est,datetime) else old_est
            if previous['amount']!=h['amount'] or old_date!=h['established'] or (aaa and aaa[0]['rate'] is not None and previous['aaa']!=aaa[0]['rate']/100):
                duplicates.append({**h,'reason':'别名候选事实不全相符，暂不追加','candidate':aliases[0]});continue
            s.cell(rr,2,h['product']);renames.append({'before':aliases[0],'after':h['product'],'evidence':'设立日期、规模、首档AAA报价一致，华泰名称规范化','row':rr});row_index[key]=rr;old[key]=previous;continue
        possible=POSSIBLE_DUPLICATES.get(h['product'])
        if key not in old and possible and normalize_product_key(possible) in old:
            duplicates.append({**h,'reason':'和富/和盛名称冲突，同发行机构、规模及期次相似，未重复追加','candidate':possible});continue
        if key in old:
            previous=old[key];aaa=[t for t in h['tiers'] if t['rating'].startswith('AAA')]
            diffs={}
            if previous['amount']!=h['amount']:diffs['amount']={'panel':previous['amount'],'huatai':h['amount']}
            if aaa:
                if aaa[0]['rate'] is not None and previous['aaa'] is not None and abs(previous['aaa']-aaa[0]['rate']/100)>Decimal('.000001'):diffs['aaa']={'panel':previous['aaa'],'huatai_percent':aaa[0]['rate']}
                if aaa[0]['term'] is not None and previous['term'] is not None and abs(previous['term']-aaa[0]['term'])>Decimal('.02'):diffs['term']={'panel':previous['term'],'huatai':aaa[0]['term']}
            if diffs:changes.append({'product':h['product'],'sheet':h['sheet'],'row':h['row'],'differences':diffs,'action':'原有值保留，待公告核实；华泰原值完整留档'})
            continue
        booking=infer_booking(h['established'])
        if booking.year!=2026:cross.append({**h,'booking_inferred':booking,'reason':'跨年，已有底稿另行留档，不重复2026计入'});continue
        aaa=[t for t in h['tiers'] if t['rating'].startswith('AAA')];aa=[t for t in h['tiers'] if t['rating'].startswith('AA+')]
        def join(ts,k,suffix=''):return '、'.join(str(t[k])+suffix for t in ts if t[k] is not None) or None
        def pct(ts):return '、'.join(f"{t['amount']/h['amount']*100:.4f}%" for t in ts if t['amount'] is not None) or None
        base,typ=asset_labels(h);start=booking-timedelta(days=booking.weekday());week=f'{start.year}.{start.month}.{start.day}-{(start+timedelta(days=6)).year}.{(start+timedelta(days=6)).month}.{(start+timedelta(days=6)).day}'
        vals=[week,h['product'],'ABS' if h['sheet'].startswith('交易所-') else 'ABN',h['venue'],h['originator'],base,typ,float(h['amount']),datetime.combine(booking,datetime.min.time()),datetime.combine(h['established'],datetime.min.time()),join(aaa,'rate','%'),join(aaa,'term'),pct(aaa),join(aa,'rate','%'),join(aa,'term'),pct(aa),None,h['manager'],args.huatai.name,'推算：设立日计第1交易日，向前第4交易日（非实际公告簿记日）',h['established'].isoformat(),h['sheet'],h['row'],'按既有资产方范围归属，资产未披露细项保留待细分标签']
        end+=1
        for col,v in enumerate(vals,1):cell=s.cell(end,col,v);cell._style=copy(s.cell(2,col)._style)
        for col in [9,10]:s.cell(end,col).number_format='yyyy/mm/dd'
        addition={**h,'booking_inferred':booking,'base_asset':base,'asset_type':typ};additions.append(addition);old[key]=addition
    notes=w['数据口径与来源']
    note=f'完整已录底稿已使用华泰截至{args.cutoff.isoformat()}明细补录现有资产方范围项目；新项目簿记日按设立日含当日第4交易日推算，非实际簿记公告。京东动产质押纳入京东系；范围外主体未加入。原有日期及未公告核实的数值保留，名称冲突单列复核。本统计表示已录入覆盖，不保证市场无缺漏；缺失AAA字段不补造。'
    for row in notes:
        if row[0].value=='面板说明':row[1].value=note
    notes.append(['本次华泰源',args.huatai.name]);notes.append(['本次源SHA256',hashlib.sha256(args.huatai.read_bytes()).hexdigest()]);notes.append(['本次基线',args.source.name])
    for sh in [s,raw]:sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
    args.output.parent.mkdir(parents=True,exist_ok=True);temp=args.output.with_suffix('.stage.xlsx');w.save(temp);temp.replace(args.output);w.close()
    current=parse_dynamics(args.output)
    added=sum((h['amount'] for h in additions),Decimal(0));previous_sum=sum((r['amount'] for r in original),Decimal(0));now=sum((r['amount'] for r in current),Decimal(0))
    assert len(current)==len(original)+len(additions) and len({normalize_product_key(r['product']) for r in current})==len(current) and now==previous_sum+added
    summary={'before_count':len(original),'before_amount':previous_sum,'after_count':len(current),'after_amount':now,'added_count':len(additions),'added_amount':added,'name_corrections':renames,'additions':additions,'excluded':excluded,'possible_duplicates':duplicates,'field_differences':changes,'cross_year':cross,'source_sha256':hashlib.sha256(args.huatai.read_bytes()).hexdigest(),'policy':note}
    def encode(v):
        if isinstance(v,(date,Decimal)):return str(v)
        raise TypeError(type(v))
    args.output.with_suffix('.update.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=encode)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['additions','excluded','field_differences','cross_year']},ensure_ascii=False,indent=2,default=encode))

if __name__=='__main__':main()

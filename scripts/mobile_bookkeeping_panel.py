"""手机版最新簿记：等宽均衡换行资产、冻结标题、紧凑无导出明细。

复用桌面同一业务快照和明细逻辑；独立验证实际移动端组件，不放宽桌面门禁。
"""
from pathlib import Path
import re

import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc

CSS = Path(__file__).with_suffix('.css').read_text(encoding='utf-8')


def render_html(data):
    body = panel.render_body(data)
    header = '''<header class="lb-mobile-freeze"><h1>最新项目簿记明细</h1>
<div id="lb-assets" class="lb-assets" role="group" aria-label="选择资产类型"></div>
<span id="lb-source" hidden></span><span id="lb-asset-count" hidden></span></header>'''
    body, count = re.subn(r'<header class="lb-banner">.*?</header>', lambda _: header, body, count=1, flags=re.S)
    assert count == 1
    # 类型控件已移至冻结区域，项目下拉仍位于滚动内容，避免头部过高。
    body, count = re.subn(r'    <div class="lb-section-heading"><h2>资产类型</h2>.*?<div id="lb-assets".*?</div>\n', '', body, count=1, flags=re.S)
    assert count == 1
    pattern = r"  \$\('lb-assets'\)\.innerHTML = .*?;\n"
    line = """  const balancedAssetLabel = name => {
    const characters = [...name];
    const lines = characters.length <= 3 ? [name] : [characters.slice(0,Math.ceil(characters.length/2)).join(''), characters.slice(Math.ceil(characters.length/2)).join('')];
    return lines.map(value => `<span class="lb-asset-line">${esc(value)}</span>`).join('');
  };
  $('lb-assets').innerHTML = data.assets.map((item,index) => `<button type="button" class="lb-asset" data-asset="${index}" aria-label="${esc(item.name)}" aria-pressed="false"><strong>${balancedAssetLabel(item.name)}</strong></button>`).join('');\n"""
    body, count = re.subn(pattern, lambda _: line, body, count=1)
    assert count == 1
    # 手机版移除导出与计数，不保留隐藏按钮或可执行导出逻辑。
    body = body.replace('<button id="lb-export" class="lb-export" type="button">导出当前明细 CSV</button>', '')
    body = body.replace('<label>档位 <select id="lb-layer">', '<select id="lb-layer" class="lb-filter-layer" aria-label="档位">')
    body = body.replace('<option value="">全部档位</option></select></label>', '<option value="">全部档位</option></select>')
    body = body.replace('<span id="lb-row-count" class="lb-muted" aria-live="polite"></span>', '')
    body = body.replace('placeholder="搜索机构名称…"', 'placeholder="搜索机构"')
    body, count = re.subn(r"  \$\('lb-export'\)\.addEventListener\('click', \(\) => \{.*?\n  \}\);", '', body, count=1, flags=re.S)
    assert count == 1
    body = '\n'.join(line for line in body.split('\n') if "$('lb-export')" not in line and "$('lb-row-count')" not in line)
    body, count = re.subn(r'<div class="lb-tier-caption">.*?</div><div class="lb-tier-note">.*?</div>', '', body, count=1)
    assert count == 1
    assert 'id="lb-export"' not in body and "$('lb-export')" not in body
    assert qc.extract_data(body) == data
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{margin:0;}' + panel.BOOKKEEPING_CSS + CSS + '</style></head><body>' + body + '</body></html>')


def verify_html(content, expected_data):
    if qc.extract_data(content) != expected_data:
        raise ValueError('手机版簿记明细与桌面快照不一致')
    if content != render_html(expected_data):
        raise ValueError('手机版簿记模板、实际脚本或样式陈旧/被篡改，请重新生成')
    return {'status':'PASS'}


def runtime_script(data):
    document=render_html(data)
    scripts=re.findall(r'<script>(.*?)</script>', document, re.S)
    if len(scripts) != 1:
        raise ValueError('手机版簿记执行脚本应唯一')
    return scripts[0]

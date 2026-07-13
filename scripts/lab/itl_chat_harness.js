/* ═══ 智能问答回归测试基座（Node 环境，stub DOM 驱动真实 itl_chat.js）═══
 *
 * 用途：不开浏览器即可对问答机器人做批量问题回归——加载真实三年台账数据 + 真实
 * itl_chat.js 源码，逐条发问并捕获回答文本，供迭代前后对比（问答版"自检"）。
 *
 * 用法：
 *   1. 先导出语料: python3 -c "...compute_data_multi_year... json.dump(all_records)"
 *   2. node scripts/lab/itl_chat_harness.js <records.json> [questions.txt]
 *      questions.txt 每行一个问题；缺省跑内置的标准问题库。
 *
 * 原理：最小化 stub window/document（只覆盖 itl_chat.js 实际用到的 DOM 面），
 * eval 真实源码 → IIFE 自动 init() → 捕获 textarea 的 keydown 监听器 → 逐题触发
 * → 从 elBody 子节点里取最后一个 bot 气泡的 HTML，剥掉标签得纯文本回答。
 */
'use strict';
const fs = require('fs');
const path = require('path');

const recordsPath = process.argv[2];
if (!recordsPath) { console.error('用法: node itl_chat_harness.js <records.json> [questions.txt]'); process.exit(1); }
const records = JSON.parse(fs.readFileSync(recordsPath, 'utf-8'));

// ── 最小 DOM stub ──────────────────────────────────────────────
class FakeEl {
  constructor(tag) {
    this.tagName = tag; this.className = ''; this.innerHTML = ''; this.value = '';
    this.style = {}; this.children = []; this.listeners = {}; this._qcache = {};
    this.classList = {
      _s: new Set(),
      toggle: () => {}, add: () => {}, remove: () => {}, contains: () => false,
    };
    this.dataset = {};
  }
  appendChild(c) { this.children.push(c); return c; }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  querySelector(sel) { if (!this._qcache[sel]) this._qcache[sel] = new FakeEl('div'); return this._qcache[sel]; }
  querySelectorAll() { return []; }
  get scrollHeight() { return 0; }
  set scrollTop(v) { /* noop */ }
}

const documentStub = {
  readyState: 'complete',
  body: new FakeEl('body'),
  createElement: (tag) => new FakeEl(tag),
  addEventListener: () => {},
  querySelector: () => null,       // currentActiveYear() → null → 默认 2026
  querySelectorAll: () => [],
};
const windowStub = { ITL_ALL_DATA: records };

// ── 加载真实源码 ────────────────────────────────────────────────
const src = fs.readFileSync(path.join(__dirname, '..', 'itl_chat.js'), 'utf-8');
(new Function('window', 'document', src))(windowStub, documentStub);

// panel 是 init() 里第二个 createElement 出来的、append 到 body 的元素
const panel = documentStub.body.children.find(el => el.className === 'itlc-panel');
if (!panel) { console.error('FATAL: init() 未跑通，itlc-panel 不存在'); process.exit(1); }
const elTa = panel.querySelector('.itlc-ta');
const elBody = panel.querySelector('.itlc-body');

function stripTags(html) {
  return html
    .replace(/<table[\s\S]*?<\/thead>/g, ' [表格] ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ').trim();
}

function ask(q) {
  elTa.value = q;
  const before = elBody.children.length;
  elTa.listeners['keydown']({ isComposing: false, keyCode: 13, key: 'Enter', shiftKey: false, preventDefault() {} });
  const bots = elBody.children.filter(c => c.className.indexOf('bot') >= 0);
  const last = bots[bots.length - 1];
  return last ? stripTags(last.innerHTML) : '(无回答)';
}

// ── 标准问题库（迭代时在此追加；也可用 questions.txt 覆盖）────────
const DEFAULT_QUESTIONS = [
  '交银理财2024-2026白条优先A档分别投资多少亿',
  '交银理财2024-2026年白条优先A档分别投资多少亿',
  '交银理财和中邮理财分别投了多少',
  '2025年3月交银理财投了多少',
  '成本最低的机构是哪家',
  '交银理财占今年总份额的比例是多少',
  '白条和金条一共投了多少',
  '平安理财近两年的投资趋势',
  '2024年vs2026年信托金条投资对比',
  '优先A档平均成本多少',
  '2024年赊销白条投了多少',
  '交银理财2024-2026年分别投资规模多少',
];

const questions = process.argv[3]
  ? fs.readFileSync(process.argv[3], 'utf-8').split('\n').map(s => s.trim()).filter(Boolean)
  : DEFAULT_QUESTIONS;

questions.forEach((q, i) => {
  let a;
  try { a = ask(q); } catch (e) { a = 'EXCEPTION: ' + e.message; }
  console.log('Q' + (i + 1) + ': ' + q);
  console.log('A' + (i + 1) + ': ' + a.slice(0, 300));
  console.log('---');
});

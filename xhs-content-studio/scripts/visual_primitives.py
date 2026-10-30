#!/usr/bin/env python3
"""Self-contained visual primitives for the adaptive XHS card studio."""
import html

STUDIO_CSS = """
:root { --glass-blur: 28px; --glass-alpha: 0.56; }
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Avenir Next", "Segoe UI", -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  background: var(--bg-base);
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  transition: background 0.4s ease;
}
body[data-world="obsidian"] { --bg-base: #060913; --card-rgb: 15,23,42; --bar-rgb: 10,14,24; --orb1: #ff2442; --orb2: #6366f1; --orb3: #06b6d4; --ink: #f8fafc; --ink-dim: rgba(226,232,240,0.72); --pill-bg: rgba(255,255,255,0.08); --pill-border: rgba(255,255,255,0.16); --card-border: rgba(255,255,255,0.20); --accent: #ff2442; }
body[data-world="crimson"] { --bg-base: #14080e; --card-rgb: 28,12,21; --bar-rgb: 20,8,14; --orb1: #ff2442; --orb2: #fb7185; --orb3: #f59e0b; --ink: #fff7f8; --ink-dim: rgba(255,228,232,0.75); --pill-bg: rgba(255,255,255,0.08); --pill-border: rgba(255,255,255,0.16); --card-border: rgba(255,255,255,0.18); --accent: #fb7185; }
body[data-world="emerald"] { --bg-base: #041114; --card-rgb: 6,24,30; --bar-rgb: 4,17,20; --orb1: #10b981; --orb2: #06b6d4; --orb3: #3b82f6; --ink: #ecfdf7; --ink-dim: rgba(209,250,229,0.72); --pill-bg: rgba(255,255,255,0.08); --pill-border: rgba(255,255,255,0.16); --card-border: rgba(255,255,255,0.16); --accent: #10b981; }
body[data-world="pearl"] { --bg-base: #eef2f9; --card-rgb: 255,255,255; --bar-rgb: 255,255,255; --orb1: #ff2442; --orb2: #6366f1; --orb3: #0ea5e9; --ink: #0f172a; --ink-dim: rgba(51,65,85,0.78); --pill-bg: rgba(15,23,42,0.05); --pill-border: rgba(15,23,42,0.12); --card-border: rgba(255,255,255,0.88); --accent: #e11d48; }
.mono { font-family: ui-monospace, "SF Mono", "Cascadia Code", "JetBrains Mono", Consolas, "Noto Sans SC", monospace; }
.studio-wrap { max-width: 1220px; margin: 0 auto; padding: 24px 20px 40px; }
.studio-bar {
  position: sticky; top: 12px; z-index: 50;
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px;
  padding: 16px 20px; border-radius: 20px;
  background: rgba(var(--bar-rgb), 0.78);
  backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--pill-border);
  box-shadow: 0 16px 40px -18px rgba(0,0,0,0.45);
}
.brand-eyebrow { font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent); font-weight: 700; }
.brand-title { font-size: 20px; font-weight: 800; margin-top: 2px; }
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; font-size: 12px; }
.controls .group { display: flex; align-items: center; gap: 6px; }
.ctl-btn {
  padding: 6px 12px; border-radius: 999px; cursor: pointer; font-size: 12px;
  background: var(--pill-bg); color: var(--ink); border: 1px solid var(--pill-border);
}
.ctl-btn.active { background: var(--accent); color: #fff; border-color: transparent; font-weight: 700; }
.ctl-btn.primary { background: var(--accent); color: #fff; border-color: transparent; font-weight: 700; }
input[type="range"] { accent-color: var(--accent); width: 110px; }
.hint { font-size: 11px; opacity: 0.6; width: 100%; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 24px; margin-top: 24px; }
.glass-card {
  position: relative; border-radius: 26px; overflow: hidden; aspect-ratio: 3 / 4;
  background: rgba(var(--card-rgb), var(--glass-alpha));
  backdrop-filter: blur(var(--glass-blur)) saturate(190%); -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(190%);
  border: 1px solid var(--card-border);
  box-shadow: inset 0 1px 2px rgba(255,255,255,0.28), 0 24px 48px -12px rgba(0,0,0,0.45);
}
.orb { position: absolute; border-radius: 50%; filter: blur(56px); opacity: 0.5; pointer-events: none; }
.orb-a { width: 190px; height: 190px; top: -60px; right: -60px; background: var(--orb1); }
.orb-b { width: 170px; height: 170px; bottom: -70px; left: -50px; background: var(--orb2); }
.orb-c { width: 120px; height: 120px; top: 42%; left: -60px; background: var(--orb3); }
.card-inner { position: relative; z-index: 1; height: 100%; display: flex; flex-direction: column; gap: 12px; padding: 24px; }
.card-top { display: flex; justify-content: space-between; align-items: center; font-size: 11px; }
.badge { padding: 4px 10px; border-radius: 999px; background: var(--accent); color: #fff; font-weight: 700; letter-spacing: 0.04em; }
.page-tag { opacity: 0.65; }
.card-title { font-size: 25px; line-height: 1.3; font-weight: 900; letter-spacing: -0.01em; margin: 0; }
.card-sub { font-size: 11px; letter-spacing: 0.06em; opacity: 0.75; margin: 0; }
.pill {
  background: var(--pill-bg); border: 1px solid var(--pill-border); border-radius: 14px;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  padding: 10px 12px; font-size: 13px; line-height: 1.55;
}
.pill .n { color: var(--accent); font-weight: 700; margin-right: 6px; }
.card-foot { margin-top: auto; padding-top: 12px; padding-right: 46px; border-top: 1px solid var(--pill-border); font-size: 12px; opacity: 0.8; }
.card-export {
  position: absolute; right: 14px; bottom: 14px; z-index: 2;
  width: 34px; height: 34px; border-radius: 50%; border: none; cursor: pointer;
  background: var(--accent); color: #fff; font-size: 15px; line-height: 1;
  box-shadow: 0 8px 20px -6px rgba(0,0,0,0.5);
}
[contenteditable] { outline: none; border-radius: 6px; }
[contenteditable]:focus { background: rgba(127,127,127,0.14); }
"""

STUDIO_JS = """
const rootEl = document.documentElement;
document.querySelectorAll('[data-set-world]').forEach(function (b) {
  b.addEventListener('click', function () {
    document.body.dataset.world = b.dataset.setWorld;
    document.querySelectorAll('[data-set-world]').forEach(function (x) { x.classList.toggle('active', x === b); });
  });
});
const blurR = document.getElementById('blur-range'), blurV = document.getElementById('blur-val');
blurR.addEventListener('input', function () { rootEl.style.setProperty('--glass-blur', blurR.value + 'px'); blurV.textContent = blurR.value + 'px'; });
const opR = document.getElementById('opacity-range'), opV = document.getElementById('opacity-val');
opR.addEventListener('input', function () { rootEl.style.setProperty('--glass-alpha', opR.value / 100); opV.textContent = opR.value + '%'; });
let lang = 'zh';
const langBtn = document.getElementById('lang-toggle');
langBtn.addEventListener('click', function () {
  lang = (lang === 'zh') ? 'en' : 'zh';
  document.querySelectorAll('[data-zh][data-en]').forEach(function (el) { el.textContent = el.dataset[lang]; });
  langBtn.textContent = (lang === 'zh') ? '中 / EN' : 'EN / 中';
});
function inlineStyles(src, dst) {
  const cs = getComputedStyle(src);
  let t = '';
  for (let i = 0; i < cs.length; i++) { const p = cs[i]; t += p + ':' + cs.getPropertyValue(p) + ';'; }
  dst.style.cssText = t;
  const s = src.children, d = dst.children;
  for (let i = 0; i < s.length; i++) { if (d[i]) inlineStyles(s[i], d[i]); }
}
async function exportCard(card, name) {
  const DW = 450, DH = 600, S = 2;
  const clone = card.cloneNode(true);
  inlineStyles(card, clone);
  clone.querySelectorAll('.card-export').forEach(function (n) { n.remove(); });
  clone.querySelectorAll('[contenteditable]').forEach(function (n) { n.removeAttribute('contenteditable'); });
  clone.style.width = DW + 'px'; clone.style.height = DH + 'px'; clone.style.margin = '0';
  clone.style.transform = 'scale(' + S + ')'; clone.style.transformOrigin = 'top left';
  clone.style.backdropFilter = 'none'; clone.style.webkitBackdropFilter = 'none';
  const wrap = document.createElement('div');
  wrap.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml');
  wrap.style.cssText = 'width:900px;height:1200px;overflow:hidden;position:relative;background:' + getComputedStyle(document.body).getPropertyValue('--bg-base') + ';';
  wrap.appendChild(clone);
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1200"><foreignObject width="100%" height="100%">' + new XMLSerializer().serializeToString(wrap) + '</svg>';
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }));
  const img = new Image();
  await new Promise(function (res, rej) { img.onload = res; img.onerror = rej; img.src = url; });
  const c = document.createElement('canvas'); c.width = 900; c.height = 1200;
  c.getContext('2d').drawImage(img, 0, 0);
  URL.revokeObjectURL(url);
  const a = document.createElement('a'); a.download = name; a.href = c.toDataURL('image/png'); a.click();
}
document.querySelectorAll('.glass-card').forEach(function (card, i) {
  const btn = card.querySelector('.card-export');
  if (btn) btn.addEventListener('click', function () { exportCard(card, 'XHS_Glass_P' + (i + 1) + '.png'); });
});
document.getElementById('export-all').addEventListener('click', async function () {
  const cards = document.querySelectorAll('.glass-card');
  for (let i = 0; i < cards.length; i++) {
    await exportCard(cards[i], 'XHS_Glass_P' + (i + 1) + '.png');
    await new Promise(function (r) { setTimeout(r, 350); });
  }
});
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _bi(zh: str, en: str) -> str:
    """Bilingual toggleable scaffold text (user content keeps its authored language)."""
    return f' data-zh="{_esc(zh)}" data-en="{_esc(en)}"'


def _card(page: int, badge_zh: str, badge_en: str, inner: str, foot_html: str, orbs: str = "ab") -> str:
    orb_html = "".join(f'<div class="orb orb-{o}"></div>' for o in orbs)
    return f"""      <article class="glass-card">
        {orb_html}
        <div class="card-inner">
          <div class="card-top mono"><span class="badge" contenteditable="true"{_bi(badge_zh, badge_en)}>{_esc(badge_zh)}</span><span class="page-tag">P{page} / 06</span></div>
{inner}
          <div class="card-foot" contenteditable="true">{foot_html}</div>
        </div>
        <button class="card-export" type="button" title="导出此卡为 900×1200 PNG">⬇</button>
      </article>"""

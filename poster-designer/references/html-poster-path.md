# HTML 出图路径（浏览器确定性排版）

宿主没有生图能力、但能渲染 HTML 并导出 PNG 时，用本路径制作中文精确、Logo 原样、表格与流程清晰的宣传单页或海报。它与 `scripts/compose_poster.py` 同级：都是确定性排版，只是渲染引擎从 Pillow 换成浏览器。

本路径生成的是扁平 PNG，不是可编辑设计源文件；机器检查通过也只记 `draft`，仍需实际看图。

## 1. 适用判断

写代码前先按 `references/direction-playbook.md` 选定方向（D1–D4），并记录方向卡。不要因为上一版用了某个骨架就继续沿用；同一客户第二次交付至少替换版式骨架、主色、标题字体中的两项。

| 条件 | 走本路径 | 不走本路径 |
|---|---|---|
| 宿主能力 | 有 DOM/CSS 渲染与截图或导出能力 | 只能生图，或只能输出文字 |
| 内容特征 | 长中文、精确数字、字段表、步骤流程、必须原样 Logo | 纯氛围主视觉、无精确文字 |
| 产出 | 数字分发 PNG、A4 单页、可打印草稿 | 需要图层可编辑的 PSD/AI |
| 状态 | `draft`，人工看图后可 `ready` | — |

宿主确认顺序：能写文件 → 能渲染固定尺寸容器 → 能把容器导出为 PNG → 能测量导出图宽高。四步缺一，按 `references/platform-adapter.md` 降级，不声称已出图。

## 2. 画布与安全区

固定像素画布，不用百分比自适应，避免导出尺寸漂移。

| 用途 | 画布 px | 导出倍率 | 成品像素 |
|---|---|---|---|
| A4 竖版 · 数字分发 | 794 × 1123 | 3× | 2382 × 3369（约 288 dpi） |
| A4 竖版 · 印刷 | 794 × 1123 | 4× | 3176 × 4492 |
| A4 竖版 · 300 dpi 标准 | 2480 × 3508 | 1× | 2480 × 3508 |
| A3 竖版 | 1123 × 1587 | 3× | 3369 × 4761 |
| 3:4 社交竖图 | 1080 × 1440 | 2× | 2160 × 2880 |
| 9:16 全屏 | 1080 × 1920 | 2× | 2160 × 3840 |
| 16:9 横幅 | 1920 × 1080 | 2× | 3840 × 2160 |
| 公众号头图 | 900 × 383 | 2× | 1800 × 766 |

- 3× 不等于 300 dpi。印刷必须按印厂要求的物理尺寸和 dpi 单独换算，缺规格时只交数字版或印刷草稿。
- A4 版心边距 44–52 px（约 12–14 mm）；页脚基线距底边 ≥ 32 px。
- 印刷出血另加 3 mm，按目标 dpi 换算；数字分发不需要出血，不能把出血当成边距。
- 页面不允许出现滚动条：`.poster` 的 `scrollHeight` 必须等于声明高度。

## 3. A4 信息单页结构

功能型单页信息密度高，按"结论在前、证据在后"排：

1. 页眉：Logo + 品牌名 + 单页编号（如 `产品单页 01`）。
2. 标题区：主标题（2 行内）+ 一句副标题 + 1 段导语。
3. 关键参数条：3–4 个有来源的数字或单位，用上下边框分组，不用等宽卡片三连。
4. 字段表：每行"编号 + 字段名 + 来源说明"，行间用 1px 分隔线；字段名与来源一一对应。
5. 流程条：3–5 步，单向连线，步骤顺序来自用户资料，不凭视觉猜。
6. 机制/边界框：说明匹配键、未命中处理、覆盖范围等容易被误解的规则。
7. 页脚：公司署名 + 单页编号。

版式骨架见 `references/design-knowledge.md` 的 E、F 两型；可直接复制 `assets/example-poster.html` 改写。

字数控制：A4 正文 12–14 px，辅助文字 ≥10 px，主标题 38–46 px；单段导语不超过 3 行。信息装不下时改版式或拆成用户要求的多张，不缩字号、不删事实。

## 4. 品牌色与 Logo

- Logo 只读，不重绘。按原始文件内嵌，不引用远程 URL。
- 显示尺寸不得超过源尺寸的 1.5 倍；超过时记录放大倍率并把清晰度记为 `unverified`。64×64 源图显示 40–48 px 是安全区间。
- 深色底上的白底 Logo 要加白底容器（内边距 4–6 px），不要直接反色。
- 无品牌色时从 Logo 取主色：解码后仅统计 `alpha > 180` 的像素，按 8 阶量化，取出现频次最高且饱和度 ≥0.25 的颜色；结果写入设计说明。取不到彩色时用中性深灰，不臆造品牌色。
- 配色不超过 1 个主色 + 1 个强调色；同系列多张共享主色规则，用深浅区分产品线。

## 5. HTML 契约

```html
<main class="poster" data-canvas="794x1123">
  ...
</main>
<button id="exportBtn" type="button">导出为 PNG</button>
```

- `.poster`：固定 `width` / `height`，显式 `background`，`overflow: hidden`；不依赖父级背景。
- 字体栈必须含中文可用字体，并给出回退：
  `'Noto Sans CJK SC','Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif`；
  正文需要宋体感时用 `'Noto Serif CJK SC','Songti SC','SimSun',serif`。
- 导出按钮 `position: fixed`，位于 `.poster` 之外，不覆盖版心；`@media print` 中隐藏。
- 图片一律 `data:` URI 内嵌；`file://` 页面导出时相对路径和远程图片可能取不到，导致空洞。
- 所有 `var(--x)` 必须在 `:root` 中定义默认值；装饰层用 `background-image` 线性渐变或 `::before`，不用大尺寸 base64 背景。
- 多张共用同一套边距、页脚和编号规则；只改内容区结构，保证成套识别。

## 6. 导出契约

使用 html-to-image（不要用 html2canvas：它在 canvas 中重新实现 CSS，背景、透明度、渐变和阴影会与页面不一致）。

```html
<script>
  (function () {
    function loadLib() {
      if (window.htmlToImage) return Promise.resolve();
      var urls = [
        'https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js',
        'https://unpkg.com/html-to-image@1.11.11/dist/html-to-image.js'
      ];
      return urls.reduce(function (p, url) {
        return p.catch(function () {
          return new Promise(function (resolve, reject) {
            var s = document.createElement('script');
            s.src = url;
            s.onload = function () { window.htmlToImage ? resolve() : reject(new Error('unavailable')); };
            s.onerror = function () { reject(new Error('unavailable')); };
            document.head.appendChild(s);
          });
        });
      }, Promise.reject());
    }
    document.getElementById('exportBtn').addEventListener('click', function () {
      var btn = this;
      btn.disabled = true;
      loadLib()
        .then(function () { return document.fonts && document.fonts.ready ? document.fonts.ready : null; })
        .then(function () { return new Promise(function (r) { setTimeout(r, 200); }); })
        .then(function () {
          return window.htmlToImage.toPng(document.querySelector('.poster'), {
            pixelRatio: 3,
            cacheBust: true,
            backgroundColor: '#ffffff'
          });
        })
        .then(function (url) {
          var a = document.createElement('a');
          a.download = 'poster-01-v001.png';
          a.href = url;
          a.click();
        })
        .catch(function (err) { alert('导出失败：' + err.message); })
        .then(function () { btn.disabled = false; });
    });
  })();
</script>
```

- 固定 `pixelRatio: 3`（印刷按 4），不随设备变化。
- 导出前等待 `document.fonts.ready`，再延迟 200 ms，避免字体替换导致的排版差异。
- 截取范围是 `.poster` 整块；导出文件名与任务编号一致。
- 导出后必须实测：文件存在、宽高 = 画布 × 倍率、格式为 PNG。

## 7. 导出兼容黑名单

| 禁止 | 导出问题 | 替代 |
|---|---|---|
| `background-clip: text` + `-webkit-text-fill-color: transparent` | 渐变文字背景丢失 | SVG `<text>` + `<linearGradient>`，或直接纯色 |
| 容器 `opacity` | 子元素透明度叠加异常 | `rgba()` 颜色 |
| `backdrop-filter` | 毛玻璃丢失 | 半透明 `rgba()` 背景 |
| `mix-blend-mode` | 混合模式丢失 | 具体颜色值 |
| 大半径 `filter: blur()` | 模糊范围不一致 | SVG `feGaussianBlur` 或预渲染背景 |
| `position: sticky` | 退化为静态 | `relative` / `fixed` |
| 多层含 `inset` 的 `box-shadow` | inset 阴影丢失 | 最多 2 层外阴影，inset 用 border 模拟 |
| 未定义的 `var(--x)` | 属性值为空 | `:root` 中给默认值 |
| 远程或相对路径 `<img>` | 导出时取不到图 | `data:` URI 内嵌 |

## 8. 自检与状态

```text
python <技能目录>/scripts/check_html_poster.py <任务目录>/poster.html \
  --expect-size A4 --export-scale 3 --report <任务目录>/layout-report.json
```

有 Playwright 时追加 `--render`，会打开页面测量元素越界、字体状态与导出按钮位置，并可 `--export <任务目录>/poster.png` 实测下载：

```text
python <技能目录>/scripts/check_html_poster.py <任务目录>/poster.html \
  --expect-size A4 --export-scale 3 --render --export <任务目录>/poster.png \
  --preview <任务目录>/preview-mobile.png --report <任务目录>/layout-report.json
```

版式重复检查（需要 Pillow 与上一版 PNG）：

```text
python <技能目录>/scripts/check_html_poster.py <任务目录>/poster.html \
  --expect-size A4 --png <任务目录>/poster.png \
  --compare <任务目录>/poster-上一版.png --report <任务目录>/layout-report.json
```

`similarity >= 0.86` 判 `reuse`（退出码 2，必须换方向）；`0.72–0.86` 判 `related`（同系列可接受，需确认意图）；`< 0.72` 判 `distinct`。不要用 `--allow-reuse` 掩盖重复版式。

判定：

- 静态项（画布、按钮、导出库、禁用 CSS、变量、占位符、中文字体栈）任一失败即阻断。
- `--render` 报元素越界、页面滚动或字体未就绪，即阻断。
- `--export` 未执行或导出尺寸不符，`html_export` 记 `unverified` / `fail`，只能交 `draft`。
- 脚本不判断中文错字、事实准确性和审美；这些仍需按 `references/quality-checklist.md` 看图核对。
- A4 单页默认记录为 `zoom` 阅读（可放大查看），不用手机 12 px 阈值直接判 fail；仍要生成 390 px 预览，确认在手机上不放大时至少能看清标题与关键数字。手机直读的传播图仍按 `mobile` 检查。

## 9. 交付记录

`delivery.json` 中该图使用：

```json
"production": {
  "method": "html_render",
  "recipe": "poster.html",
  "layout_report": "layout-report.json"
}
```

`direction` 建议填写（如 `D2-卷宗`）；`brand_id` 可选：有品牌配置时填写并核对，没有时不虚构。`layout-report.json` 由检查脚本生成，内含 HTML 哈希、导出图哈希与尺寸、`checks.layout` 和 `checks.html_export` 证据；改 HTML 或重新导出后必须重新生成报告，不能沿用旧证据。
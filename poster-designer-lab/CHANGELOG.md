# Changelog

## 1.3.0 - 设计方向与防重复

- 新增 `references/direction-playbook.md`：D1 现代工具 / D2 档案卷宗 / D3 技术白皮书 /
  D4 品牌海报四个方向、选择规则、方向卡、防重复红线与阈值；同一客户第二次交付至少替换
  版式骨架、主色、标题字体中的两项。
- `scripts/check_html_poster.py` 新增 `--compare <上一版.png>`：比较主色直方图、行密度、
  暗色行分布和边缘密度，输出 `similarity` 与 `distinct/related/reuse`；`reuse` 退出码 2，
  除非人工 `--allow-reuse`。新增 `--compare-report`，并把结论写入 `layout-report` 的
  `checks.direction`。
- `--render` 现在读取实际 computed font-family 与 `document.fonts.check()`，首选字体未加载时
  `render_font_actual` 判 fail，不再只匹配字体栈字符串；浏览器探测支持
  `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 与常见安装目录，去掉固定机器路径。
- 新增 `scripts/analyze_logo.py`：输出 Logo 尺寸、透明背景比例、主色、计划显示倍率与
  安全尺寸，深色底透明 Logo 给出白底容器建议，放大超过 1.5× 时退出码 1。
- `SKILL.md` Phase 2 增加方向选择与防重复要求；交付契约支持 `production.direction`；
  质检清单新增 `direction` 项；HTML 路径补充 `--compare` 用法。
- 新增 `evaluation/test_direction.py` 回归对比度与 Logo 分析；`acceptance.json` 增加
  T31–T34；版本 1.3.0 同步到 `compose_poster.py`、`analyze_logo.py` 与验收文件。

## 1.2.0 - HTML 出图路径与 A4 宣传单页

- 新增 `references/html-poster-path.md`：A4/A3/社交画布尺寸、安全边距、信息单页结构、
  Logo 取色与内嵌、HTML 契约、html-to-image 导出契约、导出兼容黑名单、自检与状态。
- 新增 `scripts/check_html_poster.py`：标准库静态检查画布、导出按钮、导出库、倍率、字体等待、
  禁用 CSS、CSS 变量、占位符、中文字体栈与图片内嵌；可选 `--render/--export` 用 Playwright
  实测元素越界、页面滚动、按钮遮挡、字体状态并点击导出，生成 `layout-report.json`。
- 新增 `assets/example-poster.html`：794×1123 A4 单页可运行骨架，含导出按钮与兼容写法，
  内容为虚构模板说明，可直接复制改写。
- `SKILL.md` 新增第 11 条原则「出图即验」，执行路径表与决策表加入 HTML 确定性排版，
  触发词补宣传单页/A4 单页/HTML 海报/导出 PNG；目标尺寸不再把 3:4 套在 A4 上。
- `references/design-knowledge.md` 新增 A4/A3 尺寸、E/F 两型信息单页版式、档案/政务与
  软件工具配色，以及第 7 节成套系列规则。
- `references/composition.md`、`platform-adapter.md`、`quality-checklist.md`、
  `prompt-crafting.md` 补 HTML 路径分流、能力核实、`html_export` 检查与设计说明写法。
- `references/delivery-contract.md` 支持 `production.method = html_render`：校验 HTML 哈希、
  导出图哈希/尺寸、`layout` 与 `html_export` 证据；未实测导出不得 `ready`。
- `scripts/validate_delivery.py` 增加 html_render 校验分支，旧 deterministic/generated/edited
  记录行为不变；`scripts/compose_poster.py` 版本号同步 1.2.0。
- `evaluation/acceptance.json` 增加 T27–T30（A4 单页、HTML 导出、禁用 CSS、记录校验）；
  新增 `evaluation/test_html_path.py` 回归静态检查、哈希失效与 ready 门槛（共 8 个用例）。

## 1.1.2 - 版本号接续已发布版本

- 版本号 1.0.4 → 1.1.2：已发布的 1.1.1 包在平台侧为当前最新版本，
  本次发布需大于该版本，故接续递增至 1.1.2。
- 交付内容与 1.0.4 一致（SKILL.md 结构重排、元数据规范、排版组件与交付预检无变更）；
  `scripts/compose_poster.py` 的 `SKILL_VERSION`、`evaluation/acceptance.json` 同步 1.1.2。

## 1.0.4 - SKILL.md 结构重排

- `SKILL.md` 章节结构重排：标题（`Poster Designer：AI 宣传海报设计师`）→ 一句话摘要 →
  核心原则 → 何时触发 → 工作流（Phase 1–5）→ 决策规则 → 安全约束 → 资源导航 → 依赖 → 关于。
- frontmatter 的 `description` / `description_zh` / `description_en` 改为多行块，补触发词行
  （做海报、宣传图、产品海报、活动海报、电商主图、海报改图、海报方案、生图提示词等）。
- 新增 `allowed-tools: Bash(python:*)`，与本地排版/校验脚本的调用方式一致。
- 原 8 节规则内容全部保留并归并：素材只读、必保留清单 ID、四类交付路径、3 次调用预算、
  逐张状态与检查项、发布门槛等，无规则删减。
- `compose_poster.py` 的 `SKILL_VERSION`、`evaluation/acceptance.json` 同步 1.0.4。

## 1.0.3 - 元数据与文档规范

- `SKILL.md` frontmatter 补齐 `description_zh`、`description_en`，字段顺序修正为
  `name → description → agent_created → version → display_name → display_name_en →
  description_zh → description_en → author → license → metadata`。
- `description` 末尾补「不用于…」边界句：VI 系统设计、视频制作、多页宣传册、印刷生产管理、
  营销内容自动发布不在本技能范围。
- `metadata` 修正为 `homepage` + `repository` + `contact` + `qq`（原 `email` 改为 `contact`）。
- 文末增加「关于」页脚（出品 / 官网 / 邮箱 / QQ / 许可 + Copyright）。
- `scripts/validate_delivery.py` 的版本门槛由「仅 1.0.2」改为「≥1.0.2」的版本元组比较，
  后续版本升级不再需要改校验逻辑；`scripts/compose_poster.py` 的 `SKILL_VERSION` 同步为 1.0.3。
- `evaluation/acceptance.json` 的 `skill_version` 同步为 1.0.3。
- 排版组件、交付流程、质量检查与验收用例均无行为变更。

## 1.0.2 - 排版组件与交付预检

- 新增可选本地排版组件 `scripts/compose_poster.py`：矩形、中文文本与原图的确定性排版，
  生成前完整预检（缺字、文本溢出、内容块重叠、必保留原文遗漏），输出独立 PNG、移动预览、
  布局报告与 draft 记录，不调用生图模型。
- 交付记录升级到 schema v2，新增 `readability`、`assets` 检查项；`scripts/validate_delivery.py`
  核对预检报告与最终文件哈希。
- 新增 `references/composition.md`（排版、品牌配置、素材与移动阅读预检）。
- 新增 `references/delivery-contract.md`、`references/quality-checklist.md` 的对应条款。

## 1.0.1 - 商业交付流程

- 建立任务简报、必保留清单（稳定 ID）与逐张状态（`plan_only` / `draft` / `ready` / `blocked`）。
- 增加 `evaluation/acceptance.json` 真实行为验收用例，未执行一律标 `not_run`。
- 明确素材只读、输出写入新任务目录、不覆盖源文件与旧版本。

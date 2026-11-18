# Changelog

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

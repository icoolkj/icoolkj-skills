# Changelog

## 1.0.3 - 规范对齐版

- `SKILL.md` frontmatter 补齐 `description_zh`、`description_en`，字段顺序与仓库其他技能统一
  （`name → description → agent_created → version → display_name → display_name_en →
  description_zh → description_en → author → license → metadata`）。
- `description` 末尾补「不用于…」边界句：VI 系统设计、视频制作、多页宣传册、印刷生产管理、
  营销内容自动发布不在本技能范围。
- `metadata` 与仓库统一：`homepage` + `repository` + `contact` + `qq`（原 `email` 改为 `contact`，
  仓库地址指向本仓库）。
- 文末增加统一「关于」页脚（出品 / 官网 / 邮箱 / QQ / 许可 + Copyright）。
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

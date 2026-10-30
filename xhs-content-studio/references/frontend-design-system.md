# Frontend & Gaussian Glassmorphism Design System · 前端视觉与高斯毛玻璃设计规范 (Bilingual Reference)

This reference synthesizes three industry-leading frontend design skills into a unified visual engine for `xhs-carousel-card-maker`:
本规范将三大前沿前端与 UI/UX 设计 Skill 融合为小红书图文卡片与交互工作台的核心视觉引擎：

1. **[anthropics/skills/frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design)** — *Intentional Aesthetic Direction, Typography & Visual Restraint (蓄意美学方向、字体性格与克制法则)*
2. **[nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)** — *Glassmorphism Style Priority, Curated Palettes & Font Pairings (高斯毛玻璃风格矩阵、精选调色板与字体配对)*
3. **[pbakaus/impeccable](https://github.com/pbakaus/impeccable)** — *Anti-Slop Quality Checks, Hierarchy/Clarity/Craft & Polish Commands (反 AI 塑料感检测、层级/清晰度/匠心与精修指令)*

---

## 1. Gaussian Glassmorphism Architecture · 高斯毛玻璃四层光学架构 (`ui-ux-pro-max` + `impeccable`)

True Glassmorphism (高斯毛玻璃) relies on **translucent multi-layer refraction over an ambient light field**, never a flat grey card on a plain white page. Every generated `output_cards_preview.html` must implement this 4-layer optical stack:

| Layer (光学层级) | Technical CSS Spec (CSS 核心参数) | Visual Role (视觉作用) |
| :--- | :--- | :--- |
| **L0: Ambient Mesh Light Field (背景弥散极光场)** | `radial-gradient(...)` orbs with `filter: blur(72px)` + subtle SVG fractal noise (`opacity: 0.035`) | Provides vivid chromatic light blobs behind cards so `backdrop-filter` has real colors to refract (提供丰富的色彩折射源，消除塑料感). |
| **L1: Primary Frosted Card (主卡片高斯毛玻璃层)** | `backdrop-filter: blur(28px) saturate(190%); -webkit-backdrop-filter: blur(28px) saturate(190%);` | Creates the signature frosted acrylic depth with adjustable blur (`8px`–`40px`) and translucency (营造标志性的亚克力磨砂通透感). |
| **L2: Specular Rim Highlight (1px 镜面高光描边层)** | `border: 1px solid rgba(255,255,255,0.22); box-shadow: inset 0 1px 1px rgba(255,255,255,0.35), 0 20px 50px -12px rgba(0,0,0,0.35);` | Simulates light catching the top-left bevel of physical frosted glass (模拟物理磨砂玻璃边缘的镜面折光). |
| **L3: Inner Micro-Glass Pills (内嵌微晶信息舱)** | `background: rgba(255,255,255,0.07)` (Dark) or `rgba(255,255,255,0.55)` (Light) + `backdrop-filter: blur(12px)` |Separates key takeaways and terminal code blocks without heavy opaque boxes (轻量承载干货要点与代码块). |

---

## 2. Four Curated Glassmorphism Worlds · 四大精选毛玻璃主题世界 (`ui-ux-pro-max` Palettes)

Each theme defines coordinated tokens for background canvas, ambient light orbs, glass surface fill, specular border, and accent badges:

1. **Obsidian Cyber Glass · 深空黑曜毛玻璃 (Default for Tech / API / Code)**
   - **Canvas Base**: `#060913` (Deep Midnight Slate)
   - **Ambient Orbs**: `#ff2442` (Crimson Coral), `#6366f1` (Electric Indigo), `#06b6d4` (Cyan Laser)
   - **Card Glass Surface**: `rgba(15, 23, 42, 0.56)` with `1px solid rgba(255, 255, 255, 0.15)`
   - **Text Contrast**: `#f8fafc` primary headline, `#cbd5e1` body, `#38bdf8` / `#fda4af` accents.
2. **Crimson Aurora Glass · 绯红琉璃毛玻璃 (Default for Xiaohongshu Viral / Growth)**
   - **Canvas Base**: `#14080e` (Warm Rose-Obsidian) or Frosted Daylight `#fdf8f9`
   - **Ambient Orbs**: `#ff2442` (XHS Red), `#fb7185` (Rose Glow), `#f59e0b` (Amber Gold)
   - **Card Glass Surface**: `rgba(28, 12, 21, 0.54)` with `1px solid rgba(255, 255, 255, 0.18)`
3. **Emerald Prism Glass · 极光翡翠毛玻璃 (Default for Architecture / Efficiency)**
   - **Canvas Base**: `#041114` (Abyssal Teal)
   - **Ambient Orbs**: `#10b981` (Emerald), `#06b6d4` (Cyan), `#3b82f6` (Royal Blue)
   - **Card Glass Surface**: `rgba(6, 24, 30, 0.56)` with `1px solid rgba(255, 255, 255, 0.16)`
4. **Pearl Daylight Glass · 冰川昼白毛玻璃 (Clean Editorial Frosted Light Mode)**
   - **Canvas Base**: `#eef2f9` (Soft Ice Daylight)
   - **Ambient Orbs**: `rgba(255, 36, 66, 0.28)`, `rgba(99, 102, 241, 0.26)`, `rgba(14, 165, 233, 0.25)`
   - **Card Glass Surface**: `rgba(255, 255, 255, 0.68)` with `1px solid rgba(255, 255, 255, 0.88)` and `inset 0 1px 2px rgba(255,255,255,0.95)`
   - **Text Contrast**: `#0f172a` primary headline, `#334155` body, `#e11d48` accent.

---

## 3. Bilingual Editorial Typography · 中英双语杂志级排版规范 (`anthropics/frontend-design` + `impeccable /typeset`)

- **Font Stack (`字体栈`)**:
  - **English Display & UI**: `'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif`
  - **Chinese Display & Body**: `'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', 'Microsoft YaHei', sans-serif`
  - **Technical Code & Numerals**: `'JetBrains Mono', 'Fira Code', monospace` with `font-variant-numeric: tabular-nums`
- **Bilingual Pairing Rules (`中英双语混排黄金法则`)**:
  - **Eyebrow Header (`卡片顶部双语眉题`)**: Pair a tracked-out English category token (`01 / PROTOCOL ANATOMY`) with a concise Chinese pill badge (`协议拆解`), separated by a subtle glass dot or slash.
  - **Card Main Title (`卡片主标题`)**: Bold Chinese headline (`20px–24px` in preview, `46px–54px` on 900×1200 canvas, `font-weight: 800`, `letter-spacing: -0.02em`) with inline code tokens (`/v1/chat/completions`) wrapped in translucent monospace pills.
  - **Subtitle Banner (`双语副标题横幅`)**: Combine the Chinese core takeaway with a compact English subtitle line (`font-size: 11px`, `opacity: 0.72`) so every card carries international studio-grade visual polish.

---

## 4. Anti-Slop Quality Checklist · 反 AI 塑料感自检清单 (`pbakaus/impeccable` 59-Check Distilled)

Before finalizing `output_cards_preview.html`, verify that none of these generic AI anti-patterns appear:
- [x] **No Unrefracted Flat Cards**: Every card uses `backdrop-filter: blur(...)` over positioned ambient gradient spheres.
- [x] **No Status-Chip Soup**: At most 2 distinct badge styles per card (1 top-left accent pill + 1 top-right muted index tag `P1 / 06`).
- [x] **No Muddy Black Shadows**: Use layered ambient shadows + `inset 0 1px 1px rgba(255,255,255,0.35)` top-edge specular reflection.
- [x] **Interactive User Control**: Always include live sliders for **Gaussian Blur (`高斯模糊半径`)** and **Glass Opacity (`玻璃不透明度`)**, **4 Theme Switchers**, **Bilingual Toggle (`中英双语开关`)**, and **High-Res 900×1200 Gaussian Glass PNG Export**.

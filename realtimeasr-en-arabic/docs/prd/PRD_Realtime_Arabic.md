# PRD: 实时阿拉伯语识别体验 Demo 改造

## 1. 项目概述
基于现有 WebCall Arabic 基础项目，实现前后端分离的实时语音识别 Demo。
核心目标包括：
1. 录音文件的后端持久化及 SQLite 数据库存储记录。
2. 历史记录独立页面（Dashboard）供查阅、播放与下载。
3. Speechmatics 规范的高级可视化热词配置（支持 additional_vocab 及其 sounds_like 扩展）。
4. 前端高级审美重构（Anti-slop，禁用廉价设计，引入 Bento Grid 及极致细节动效）。

## 2. 架构说明
- **后端**：FastAPI + WebSockets + SQLite。新增 `storage/` 目录用于存储 `.wav` 音频文件。
- **前端**：原生 HTML/CSS/JS。划分为两个页面：
  - `index.html`: 实时转录大屏及热词控制面板。
  - `history.html`: 历史记录 Dashboard。

## 3. 功能需求详述

### 3.1 录音持久化与历史记录
- **录音落盘**：后端 WebSocket 在接收客户端传入的 `pcm_s16le` 音频帧时，实时写入 `storage/{session_id}.wav`，参数为 16kHz, 16bit, 单声道。
- **记录落库**：会话结束后，后端将 `{session_id, language, final_transcript, audio_path, timestamp}` 存入 SQLite 数据库。
- **历史记录 API**：
  - `GET /api/history`: 返回按照时间倒序的历史记录。
  - `GET /api/download/{session_id}`: 下载对应的录音文件。

### 3.2 可视化热词配置
- **交互规范**：前端提供高级“卡片表单”输入热词。
  - 输入框一：Word / Phrase (例如 Dyna)。
  - 输入框二：Sounds Like (选填，逗号分隔，例如 die nah)。
- **数据结构**：生成如下数组，并在 WebSocket握手 (`action: "start"`) 时通过 `hotwords` 字段传给后端。
  ```json
  [
    "simple_word",
    { "content": "Dyna", "sounds_like": ["die nah"] }
  ]
  ```
- **后端透传**：后端将其映射至 Speechmatics 的 `additional_vocab` 字段。

### 3.3 UI/UX 审美规范
- **色彩纪律**：严格遵守 `frontend-design` 及 `design-taste-frontend` 规范。主色调为高级灰白与特定主导色（与顶部 Navbar 背景条一致）。全面禁用系统 emoji，一律使用 Phosphor / Radix 风格的 SVG Icon，其 `stroke` 颜色跟随主题。
- **字体纪律**：封杀 Inter，英文字体采用高级无衬线体（Satoshi 或 Geist），阿拉伯语使用 Noto Sans Arabic。
- **空间与微动效**：采用非对称 Bento Grid。所有交互元素须有物理阻尼反馈 (`transform: scale(0.98)` 等)。字词上屏必须带有平滑的垂直位移或渐显动画，防止硬切。

## 4. 交付清单
1. SQLite 初始化文件与 FastAPI 挂载逻辑。
2. 音频 Wav 流式写入类。
3. `index.html`, `style.css`, `app.js` 全面重构。
4. `history.html` 及对应的 `history.js`。
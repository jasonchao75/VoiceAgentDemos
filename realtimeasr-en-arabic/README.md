# WebCall Arabic - 实时语音识别与录音落盘系统

这是一个前后端分离的实时语音识别展示项目（Demo），支持阿拉伯语、英语以及混合语言的识别。基于 Speechmatics WebSocket API 构建，并在本次升级中引入了原生的极简风格界面（Bento Grid）、SQLite 数据持久化以及音频文件实时落盘。

## 🌟 核心特性

- **极致前端审美 (Anti-Slop UI)**: 摒弃廉价的组件库和默认样式，采用定制的非对称 Bento Grid、Spring 物理动画和 SVG 线条图标。
- **实时语音转写**: 基于 Speechmatics Realtime WebSocket API。
- **数据与录音持久化**: 后端自动截获二进制音频流存为 `16kHz WAV` 格式，同时将会话详情保存入 SQLite 数据库。
- **历史记录看板**: 专属的 `/history.html` 数据大屏，可查阅过往测试记录并直接下载录音。
- **可视化热词配置**: 高级标签（Tag）式交互，支持实时添加带发音提示（Sounds like）的定制专有词汇。

---

## 🛠️ 技术栈

### 后端 (Backend)
- **语言框架**: Python 3.8+ / FastAPI
- **通信协议**: WebSocket
- **数据库**: SQLite (原生 `sqlite3`)
- **API对接**: Speechmatics Realtime API

### 前端 (Frontend)
- **核心**: 原生 HTML5 / CSS3 / JavaScript (无需 Node.js/npm)
- **音频采集**: Web Audio API / AudioWorklet
- **设计规范**: Satoshi & Noto Sans Arabic (字体), Phosphor Icons (矢量图标)

---

## 🚀 部署与运行 (包含自动部署)

本项目支持通过 GitHub Actions 进行轻量自动化部署到 DigitalOcean。详细的服务器配置前提、免密重启配置、以及触发方式等请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)。

### 1. 环境准备
- 确保已安装 Python 3.8 或更高版本。
- 获取 Speechmatics API Key。

### 2. 安装后端依赖
```bash
cd demos/realtimeasr-en-arabic
pip install -r backend/requirements.txt
```

### 3. 环境变量与 API Key 配置
对于本地开发，请在 `demos/realtimeasr-en-arabic` 或项目根目录创建一个 `.env` 文件：
```env
# Speechmatics
SPEECHMATICS_API_KEY=你的_API_KEY_填写在这里
SPEECHMATICS_URL=wss://eu2.rt.speechmatics.com/v2

# 服务器配置
HOST=0.0.0.0
PORT=8010
```
对于 GitHub Actions 的 CI/Smoke Test 流程，请前往 GitHub 仓库配置 Secrets：
进入 **Settings > Secrets and variables > Actions > New repository secret**，名称填写 `SPEECHMATICS_API_KEY`，值为真实的 API Key。

### 4. 本地运行

#### 后端启动
在项目根目录（或 `demos/realtimeasr-en-arabic` 目录）运行：
```bash
python -m backend.main
```
这将在 `http://0.0.0.0:8010` 启动 FastAPI 后端服务。

#### 前端体验
由于本项目为纯原生前端，您有以下两种方式预览：
1. **直接双击**：在文件浏览器中双击 `frontend/index.html`。
2. **轻量服务器**：在 `frontend` 目录下运行 `python -m http.server 8765`，然后在浏览器访问 `http://127.0.0.1:8765`。

---

## 📁 目录结构

```text
realtime-en-arabic/
├── backend/
│   ├── database.py             # SQLite 数据库与建表逻辑
│   ├── main.py                 # FastAPI 入口及 REST API
│   ├── websocket_handler.py    # WebSocket 桥接与录音文件落地
│   ├── speechmatics_client.py  # Speechmatics 客户端，支持热词追加
│   ├── config.py               # 配置加载
│   └── storage/                # 音频文件 (.wav) 自动保存目录
├── frontend/
│   ├── index.html              # 实时转录大屏页面
│   ├── history.html            # 历史记录看板页面
│   ├── css/
│   │   └── style.css           # 全局样式（Bento Grid, CSS Variables）
│   └── js/
│       ├── app.js              # 录音核心控制与 WebSocket 交互
│       ├── history.js          # 看板历史记录 API 拉取逻辑
│       └── audio-worklet-processor.js
├── docs/
│   └── prd/
│       └── PRD_Realtime_Arabic.md # 需求与架构文档
├── .env.example
└── README.md
```

---

## 💡 使用指南

1. **配置热词**：在左侧面板输入您的专有词汇，还可选择输入发音（Sounds like），点击 "+" 即可添加。
2. **开始录音**：点击左下角 **Start Session**，允许麦克风权限后即可说话。
3. **结束与保存**：点击 **Stop Session**，录音将被存入后端的 `storage/` 文件夹并入库，页面将弹出成功提示。
4. **历史回溯**：点击顶部导航栏的 **History Dashboard** 即可查看之前所有的转录会话和录音。

## ⚠️ 故障排查

1. **麦克风无权限**: 浏览器安全策略要求必须在 `localhost` 或 `HTTPS` 环境下才能调起麦克风。
2. **WebSocket 连接失败**: 请检查 `backend/main.py` 是否正常运行，并且控制台没有报错。
3. **转录结果不准**: 可以尝试在“Additional Vocabulary”配置中添加拼音/发音相近的热词以纠正模型识别。

---

## 🧪 CI/CD 与测试指南 (Smoke Test)

本仓库包含用于验证基础连通性的自动化 CI 和 Smoke Test 工作流，位于 `.github/workflows/` 下。

### 自动化 Smoke Test (手动触发)
自动化 Smoke Test 仅用于确认服务能够正常构建、启动并进行基础的健康检查，**不包含**真实音频的识别准确率（WER/CER）或延迟等高级性能评测。字准率、WER/CER、延迟评测等效果评测属于后续高级 CI 流程。

覆盖内容：
- 后端 Python 依赖安装与语法检查
- FastAPI 应用启动与 `/health` 端点检查
- `SPEECHMATICS_API_KEY` Secret 存在性验证（防泄漏）
- 前端静态文件可用性检查

**触发方式**：
在 GitHub Actions 页面选择 `Smoke Test` workflow，点击 `Run workflow` 手动触发。
*(注：触发时虽然有 `test_live_asr` 开关，但当前它仅是一个预留参数，不会实际调用真实的 Speechmatics API，不会产生计费。)*

### 人工验收清单 (Manual Smoke Test)
在部署或重大更新后，请按以下步骤进行人工验收：
1. 打开 Demo 页面（`index.html`）。
2. 允许浏览器的麦克风权限。
3. 点击左下角的 **Start Session**。
4. 对着麦克风说一句测试语音（如 "Hello, testing Speechmatics API" 或阿拉伯语测试句）。
5. 确认页面中实时出现 Partial (临时) / Final (最终) 的转录文本。
6. 点击 **Stop Session**。
7. 确认页面没有明显的前端或后端报错。
8. 前往 `History Dashboard` 确认录音和转录记录成功落盘。

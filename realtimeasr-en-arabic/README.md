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

## 🚀 部署与运行

### 1. 环境准备
- 确保已安装 Python 3.8 或更高版本。
- 获取 Speechmatics API Key。

### 2. 安装后端依赖
```bash
cd demos/realtimeasr-en-arabic
pip install -r backend/requirements.txt
```

### 3. 环境变量配置
在 `demos/realtimeasr-en-arabic` 或项目根目录创建一个 `.env` 文件，包含以下内容：
```env
# Speechmatics
SPEECHMATICS_API_KEY=你的_API_KEY_填写在这里
SPEECHMATICS_URL=wss://eu2.rt.speechmatics.com/v2

# 服务器配置
HOST=0.0.0.0
PORT=8010
```

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

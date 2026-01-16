# LaTeX Formula Extractor（图片一键提取 LaTeX）

一个本地运行的网页：上传/拖拽/粘贴公式截图或拍照图片，点击一次即可提取 **LaTeX**，并支持 **复制** 与 **KaTeX 实时预览**。

## 功能特性

- **多种输入方式**
  - 图片拖拽/上传 + 实时预览
  - **从剪贴板粘贴**（按钮 + 快捷键 `Ctrl/⌘+V`）
  - 支持 PNG/JPG/JPEG/WebP 格式
- **一键提取 LaTeX**
  - 默认使用 **DashScope（通义千问3-VL-Flash）** 视觉识别
  - 自动清洗输出（去除分隔符、解释文字、代码块标记）
  - 支持多行公式、复杂数学环境
- **结果展示**
  - 一键复制到剪贴板
  - **KaTeX 实时预览**（自动处理 `$$`、`\[...\]`、`\begin{...}` 等格式）
  - 失败提示、超时与文件类型校验

## 环境要求

- Python 3.10+
- 现代浏览器（支持 Clipboard API）

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目后进入项目目录
cd latex-extractor  # 或你的项目目录名

# 创建虚拟环境（可选但推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

**推荐：DashScope（通义千问视觉）**

```bash
export DASHSCOPE_API_KEY="sk-xxxxx"
```

可选环境变量：
- `DASHSCOPE_BASE_URL`：默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `DASHSCOPE_MODEL`：默认 `qwen3-vl-flash`（通义千问3-VL-Flash 视觉模型）
- `ENGINE`：强制指定后端 `auto|dashscope|openai|pix2text`（默认 `auto`）

**兼容：OpenAI / 其他 OpenAI 兼容服务**

```bash
export OPENAI_API_KEY="sk-xxxxx"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export OPENAI_MODEL="gpt-4o-mini"  # 可选，需支持视觉
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开浏览器访问：`http://127.0.0.1:8000`

## 使用技巧

### 图片质量建议
- **裁剪到公式区域**：去掉多余文字/边框/背景，准确率会明显提升
- **清晰度**：避免模糊、过度压缩、强透视变形
- **对比度**：黑字白底或白字黑底效果最佳

### 快捷操作
- **粘贴图片**：截图后直接在页面按 `Ctrl/⌘+V`（或点击"从剪贴板获取"按钮）
- **复制结果**：点击"复制 LaTeX"按钮，或直接选中文本复制

## 常见问题

### 1. 提示"未配置 DASHSCOPE_API_KEY"

**原因**：未设置 API Key 环境变量

**解决**：启动前执行：

```bash
export DASHSCOPE_API_KEY="你的key"
```

如果使用 OpenAI：

```bash
export OPENAI_API_KEY="你的key"
```

### 2. 提示"识别失败：BadRequestError / AuthenticationError"

**可能原因**：
- API Key 无效或已过期
- 账户余额不足
- 模型不支持视觉输入（如 `deepseek-chat` 是纯文本模型）

**解决**：
- 检查 Key 是否正确
- 确认使用的是**视觉模型**（DashScope 的 `qwen3-vl-flash` / OpenAI 的 `gpt-4o-mini` 等）

### 3. KaTeX 预览显示"正在加载"或原始 LaTeX 代码

**原因**：
- CDN 加载失败（网络限制）
- 模型输出包含 KaTeX 不支持的命令

**解决**：
- **网络问题**：刷新页面（`Ctrl/⌘+Shift+R` 强制刷新），或检查浏览器控制台是否有 CDN 加载错误
- **语法问题**：前端已自动清理常见分隔符（`$$`、`\[`、`\(`）和不支持命令（`\tag`、`\label`），如仍不渲染请检查 LaTeX 语法

### 4. 从剪贴板粘贴不工作

**原因**：浏览器不支持 Clipboard API 或未授权

**解决**：
- 使用 **HTTPS** 或 **localhost**（HTTP 仅在本地有效）
- 检查浏览器权限设置，允许网站访问剪贴板
- 部分浏览器（如旧版 Safari）可能不支持，建议使用 Chrome/Edge/Firefox

### 5. 输出结果包含解释文字

**原因**：模型有时会输出额外说明

**解决**：
- 前端已自动清洗（提取代码块、去除前缀）
- 如需更严格控制，可修改 `app/main.py` 中的 `prompt` 提示词

## 技术栈

- **后端**：FastAPI + Uvicorn
- **前端**：原生 HTML/CSS/JavaScript + KaTeX
- **识别**：DashScope（通义千问3-VL-Flash）/ OpenAI Vision API

## 为什么需要 API Key？

因为"图片→LaTeX"识别需要调用**云端大模型的视觉理解能力**：
- **身份认证**：确认调用者身份
- **计费/额度**：大模型推理有成本，Key 关联账户余额
- **限流与风控**：防止滥用

如需**完全离线**，可考虑本地部署开源模型（如 Pix2Text、LaTeX-OCR），但部署复杂度较高。

## 许可

MIT License

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 [Issue](https://github.com/qingguang0309/LaTeX-Formula-Extractor/issues)
- 发送邮件至：qingguang0309@163.com

---

**Star ⭐ 本项目如果你觉得有用！**


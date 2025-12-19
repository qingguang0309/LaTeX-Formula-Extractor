# LaTeX Extractor（图片一键提取 LaTeX）

一个本地运行的网页：上传/拖拽公式截图或拍照图片，点击一次即可提取 **LaTeX**，并支持 **复制** 与 **KaTeX 预览**。

## 功能

- 图片拖拽/上传 + 预览
- 一键提取 LaTeX（默认使用 OpenAI Vision）
- 结果一键复制
- KaTeX 实时预览（行内/展示模式）
- 失败提示、超时与文件类型校验

## 环境要求

- Python 3.10+

## 安装

```bash
cd "/Users/qingguang/Desktop/latex extractor"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置（必需）

推荐使用 DashScope（通义千问视觉）作为识别后端（OpenAI 兼容模式）：

```bash
export DASHSCOPE_API_KEY="你的_key"
```

可选项：

- `DASHSCOPE_BASE_URL`：默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- `DASHSCOPE_MODEL`：默认 `qwen3-vl-flash`（通义千问3-VL-Flash）

如果你想强制使用某个后端（可选）：

- `ENGINE=auto|dashscope|openai|pix2text`（默认 `auto`）

兼容（迁移用）：

- 你也可以继续用 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`

## 启动

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：`http://127.0.0.1:8000`

## 使用建议

- 尽量裁剪到“只有公式”的区域（去掉多余文字/边框），准确率会明显提升
- 图片尽量清晰、对比度高，避免过度压缩/强透视

## 常见问题

### 1) 提示未配置 OPENAI_API_KEY

请在启动前设置：

```bash
export DASHSCOPE_API_KEY="你的_key"
```

### 2) 有时输出带解释文字

前端会尝试做清洗（提取代码块/latex段），但如果你希望 **严格只返回公式**，我可以把提示词进一步收紧并加“强制只输出 LaTeX”校验。



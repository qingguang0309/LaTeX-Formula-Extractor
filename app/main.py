import base64
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI


APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return v.strip()


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def _clean_latex(text: str) -> str:
    """
    Best-effort 清洗：
    - 优先提取 ```latex ...``` 或 ```...``` 代码块内容
    - 否则去掉常见的解释性前缀
    """
    t = (text or "").strip()
    if "```" in t:
        parts = t.split("```")
        # 形如: ["", "latex\n....", ""]
        best = None
        for chunk in parts:
            c = chunk.strip()
            if not c:
                continue
            # 去掉可能的语言标识行
            if "\n" in c:
                first, rest = c.split("\n", 1)
                if first.strip().lower() in {"latex", "tex"}:
                    c = rest.strip()
            if best is None or len(c) > len(best):
                best = c
        if best:
            return best.strip()

    for prefix in [
        "LaTeX:",
        "latex:",
        "答案：",
        "结果：",
        "输出：",
    ]:
        if t.startswith(prefix):
            t = t[len(prefix) :].strip()
    return t


def _extract_with_pix2text(raw: bytes, filename: str) -> str:
    """
    本地识别（可选）：Pix2Text

    安装：
      pip install pix2text
    """
    try:
        from pix2text import Pix2Text  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"未安装 pix2text，无法本地识别：{type(e).__name__}: {str(e)}")

    suffix = os.path.splitext(filename or "")[1] or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as f:
        f.write(raw)
        f.flush()
        p2t = Pix2Text()
        out = p2t(f.name)

    # Pix2Text 输出可能是 list[dict] 或 str，这里做兼容提取
    if isinstance(out, str):
        return out.strip()
    if isinstance(out, list):
        texts = []
        for item in out:
            if isinstance(item, dict) and "text" in item:
                texts.append(str(item["text"]))
            else:
                texts.append(str(item))
        return "\n".join([t for t in (s.strip() for s in texts) if t]).strip()
    return str(out).strip()


def _postprocess_with_deepseek(latex: str) -> str:
    """
    用 DeepSeek 文本模型做 LaTeX 清洗/纠错（不需要图片能力）。
    """
    api_key = _get_env("DEEPSEEK_API_KEY")
    if not api_key:
        return latex

    base_url = _get_env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = _get_env("DEEPSEEK_MODEL", "deepseek-chat")

    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt = (
        "下面是一段从图片识别得到的 LaTeX，可能包含多余解释或格式瑕疵。"
        "请只输出清洗后的 LaTeX 源码（不要 Markdown，不要解释）。\n\n"
        f"{latex}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        cleaned = (resp.choices[0].message.content or "").strip()
        return _clean_latex(cleaned) or latex
    except Exception:
        return latex


app = FastAPI(title="LaTeX Extractor")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(_: Request) -> HTMLResponse:
    html = _read_text(os.path.join(TEMPLATE_DIR, "index.html"))
    return HTMLResponse(html)


@app.post("/api/extract")
async def extract_latex(file: UploadFile = File(...)):
    # 说明：
    # - DeepSeek 常见模型为纯文本（不支持 image_url），因此不能直接用于“图片->LaTeX”。
    # - 这里提供两条路：
    #   1) 云端视觉（需要 OPENAI_API_KEY + 视觉模型）
    #   2) DashScope 视觉（DASHSCOPE_API_KEY + 通义千问视觉模型）
    #   3) 本地 Pix2Text（不需要云端 Key，可选安装），可再用 DeepSeek 做后处理
    #
    # 可选：ENGINE=auto|dashscope|openai|pix2text
    engine = (_get_env("ENGINE", "auto") or "auto").lower()

    dashscope_api_key = _get_env("DASHSCOPE_API_KEY")
    dashscope_base_url = _get_env("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    dashscope_model = _get_env("DASHSCOPE_MODEL", "qwen3-vl-flash")

    openai_api_key = _get_env("OPENAI_API_KEY")
    openai_base_url = _get_env("OPENAI_BASE_URL")
    openai_model = _get_env("OPENAI_MODEL", "gpt-4o-mini")

    # 基础校验
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    mime = file.content_type or _guess_mime(file.filename)
    if not (mime.startswith("image/")):
        raise HTTPException(status_code=400, detail=f"仅支持图片文件，当前: {mime}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片过大（最大 10MB）")

    data_b64 = base64.b64encode(raw).decode("utf-8")
    data_url = f"data:{mime};base64,{data_b64}"

    prompt = (
        "请从图片中识别数学公式，并只输出对应的 LaTeX 源码。"
        "不要输出任何解释文字、不要加前后缀、不要包含 Markdown。"
        "如果图片中包含多行公式，请用换行分隔。"
    )

    # 1) DashScope（通义千问视觉）——优先级最高（你本次需求）
    if engine in {"auto", "dashscope"} and dashscope_api_key:
        try:
            client = OpenAI(api_key=dashscope_api_key, base_url=dashscope_base_url)
            resp = client.chat.completions.create(
                model=dashscope_model,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )
            content = (resp.choices[0].message.content or "").strip()
            latex = _clean_latex(content)
            if latex:
                latex = _postprocess_with_deepseek(latex)
                return {
                    "latex": latex,
                    "engine": "dashscope_qwen_vl",
                    "model": dashscope_model,
                    "base_url": dashscope_base_url,
                }
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"DashScope 视觉识别失败：{type(e).__name__}: {str(e)}")

    # 2) OpenAI 云端视觉
    if engine in {"auto", "openai"} and openai_api_key:
        data_b64 = base64.b64encode(raw).decode("utf-8")
        data_url = f"data:{mime};base64,{data_b64}"

        client = (
            OpenAI(api_key=openai_api_key, base_url=openai_base_url)
            if openai_base_url
            else OpenAI(api_key=openai_api_key)
        )

        try:
            resp = client.chat.completions.create(
                model=openai_model,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )
            content = (resp.choices[0].message.content or "").strip()
            latex = _clean_latex(content)
            if latex:
                return {"latex": latex, "engine": "openai_vision", "model": openai_model, "base_url": openai_base_url}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"云端视觉识别失败：{type(e).__name__}: {str(e)}")

    # 3) 本地 Pix2Text（可选安装），并可用 DeepSeek 再清洗
    if engine not in {"auto", "pix2text"} and engine != "pix2text":
        raise HTTPException(
            status_code=400,
            detail=f"ENGINE={engine} 不受支持，可选：auto|dashscope|openai|pix2text",
        )
    try:
        local = _extract_with_pix2text(raw, file.filename)
        latex = _clean_latex(local)
        if not latex:
            raise HTTPException(status_code=502, detail="本地识别结果为空（Pix2Text）")
        latex = _postprocess_with_deepseek(latex)
        return {"latex": latex, "engine": "pix2text_local"}
    except RuntimeError as e:
        # 给出可操作的提示：DeepSeek 不能直接做图片识别，需要本地模型或视觉模型
        raise HTTPException(
            status_code=400,
            detail=(
                "未检测到可用的视觉识别后端。"
                "请二选一：\n"
                "1) 设置 DASHSCOPE_API_KEY（推荐：通义千问3-VL-Flash）；或\n"
                "2) 设置 OPENAI_API_KEY 使用支持图片的视觉模型；或\n"
                "3) 安装本地识别依赖：pip install pix2text\n\n"
                f"本地识别不可用原因：{str(e)}"
            ),
        )



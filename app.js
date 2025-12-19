const $ = (id) => document.getElementById(id);

const fileInput = $("fileInput");
const dropZone = $("dropZone");
const preview = $("preview");
const extractBtn = $("extractBtn");
const clearBtn = $("clearBtn");
const pasteBtn = $("pasteBtn");
const statusEl = $("status");
const errorBox = $("errorBox");
const latexBox = $("latexBox");
const renderBox = $("renderBox");
const copyBtn = $("copyBtn");
const displayMode = $("displayMode");

let currentFile = null;
let currentLatex = "";

let katexLoadPromise = null;

function setStatus(text) {
  statusEl.textContent = text || "";
}

function showError(msg) {
  errorBox.textContent = msg || "";
  errorBox.classList.toggle("hidden", !msg);
}

function setLatex(text) {
  currentLatex = text || "";
  latexBox.textContent = currentLatex;
  copyBtn.disabled = !currentLatex;
  renderLatex();
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => resolve(true);
    s.onerror = () => reject(new Error(`脚本加载失败：${src}`));
    document.head.appendChild(s);
  });
}

function loadCss(href) {
  return new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    link.onload = () => resolve(true);
    link.onerror = () => reject(new Error(`样式加载失败：${href}`));
    document.head.appendChild(link);
  });
}

async function ensureKatex() {
  if (window.katex) return true;
  if (katexLoadPromise) return katexLoadPromise;
  // 兜底：如果 CDN 脚本没加载上，尝试再加载一次
  katexLoadPromise = (async () => {
    const cssHref = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css";
    const jsSrc = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js";
    try {
      // 即便重复插入 link/script，浏览器通常会去重/复用缓存
      await loadCss(cssHref).catch(() => {});
      await loadScript(jsSrc);
      return !!window.katex;
    } finally {
      // 不清空 promise：避免并发重复加载
    }
  })();
  return katexLoadPromise;
}

async function renderLatex() {
  renderBox.innerHTML = "";
  const src = (currentLatex || "").trim();
  if (!src) return;

  if (!window.katex) {
    renderBox.textContent = "正在加载 KaTeX…";
    try {
      await ensureKatex();
    } catch (e) {
      renderBox.textContent = "KaTeX 未加载，无法预览（可能网络受限或 CDN 被拦截）。";
      return;
    }
    if (!window.katex) {
      renderBox.textContent = "KaTeX 未加载，无法预览（可能网络受限或 CDN 被拦截）。";
      return;
    }
  }

  const isDisplay = !!displayMode.checked;
  function normalizeForKatex(s) {
    let t = (s || "").trim();

    // 去掉常见数学分隔符（KaTeX render 期望“裸表达式”）
    if (t.startsWith("$$") && t.endsWith("$$") && t.length >= 4) t = t.slice(2, -2).trim();
    if (t.startsWith("\\[") && t.endsWith("\\]") && t.length >= 4) t = t.slice(2, -2).trim();
    if (t.startsWith("\\(") && t.endsWith("\\)") && t.length >= 4) t = t.slice(2, -2).trim();
    if (t.startsWith("$") && t.endsWith("$") && t.length >= 2) t = t.slice(1, -1).trim();

    // 删除 KaTeX 常见不支持/没必要的命令
    t = t
      .replace(/\\label\{[^}]*\}/g, "")
      .replace(/\\tag\{[^}]*\}/g, "")
      .replace(/\\nonumber\b/g, "");

    // 如果包含对齐符号或换行，但没有环境，包一层 aligned
    const hasAlignTokens = /(^|[^\\])&/.test(t) || t.includes("\\\\");
    const hasEnv = /\\begin\{[a-zA-Z*]+\}/.test(t);
    if (hasAlignTokens && !hasEnv) {
      t = `\\begin{aligned}\n${t}\n\\end{aligned}`;
    }
    return t.trim();
  }

  // 含环境时不要逐行拆开，否则会把 \begin/\end 拆碎导致渲染失败
  const hasEnv = /\\begin\{[a-zA-Z*]+\}/.test(src);
  const blocks = hasEnv
    ? [src]
    : src
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
  if (blocks.length === 0) return;

  for (const block of blocks) {
    const lineWrap = document.createElement("div");
    lineWrap.className = "py-1";
    const expr = normalizeForKatex(block);
    try {
      window.katex.render(expr, lineWrap, {
        displayMode: isDisplay,
        throwOnError: false,
        strict: "ignore",
      });
    } catch (e) {
      // 极少数情况下 KaTeX 仍可能抛异常（如输入类型/极端非法内容）
      lineWrap.textContent = block;
    }
    renderBox.appendChild(lineWrap);
  }
}

function setFile(file) {
  currentFile = file || null;
  extractBtn.disabled = !currentFile;
  clearBtn.disabled = !currentFile && !currentLatex;
  showError("");
  setStatus("");

  if (!currentFile) {
    preview.classList.add("hidden");
    preview.src = "";
    return;
  }

  const url = URL.createObjectURL(currentFile);
  preview.src = url;
  preview.classList.remove("hidden");
}

async function extract() {
  if (!currentFile) return;
  showError("");
  setStatus("识别中…");
  extractBtn.disabled = true;

  const fd = new FormData();
  fd.append("file", currentFile, currentFile.name);

  try {
    const res = await fetch("/api/extract", {
      method: "POST",
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.detail || `请求失败（HTTP ${res.status}）`;
      throw new Error(msg);
    }
    setLatex(data.latex || "");
    setStatus("完成");
  } catch (e) {
    showError(e?.message || String(e));
    setStatus("");
  } finally {
    extractBtn.disabled = !currentFile;
    clearBtn.disabled = !currentFile && !currentLatex;
  }
}

function clearAll() {
  setFile(null);
  setLatex("");
  showError("");
  setStatus("");
  fileInput.value = "";
}

fileInput.addEventListener("change", () => {
  const f = fileInput.files && fileInput.files[0];
  if (f) setFile(f);
});

extractBtn.addEventListener("click", extract);
clearBtn.addEventListener("click", clearAll);
displayMode.addEventListener("change", () => renderLatex());

copyBtn.addEventListener("click", async () => {
  if (!currentLatex) return;
  try {
    await navigator.clipboard.writeText(currentLatex);
    setStatus("已复制");
    setTimeout(() => setStatus(""), 1200);
  } catch {
    showError("复制失败：浏览器可能禁止了剪贴板访问。你可以手动选中源码复制。");
  }
});

// Drag & drop
["dragenter", "dragover"].forEach((evt) => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add("drop-hover");
  });
});

["dragleave", "drop"].forEach((evt) => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drop-hover");
  });
});

dropZone.addEventListener("drop", (e) => {
  const dt = e.dataTransfer;
  const f = dt && dt.files && dt.files[0];
  if (f) setFile(f);
});

async function pasteFromClipboard() {
  showError("");
  setStatus("");
  // 需要安全上下文：localhost 通常可以
  if (!navigator.clipboard) {
    showError("当前浏览器不支持剪贴板 API。你可以直接在页面按 Ctrl/⌘+V 粘贴图片。");
    return;
  }
  if (!navigator.clipboard.read) {
    showError("当前浏览器不支持读取剪贴板图片。你可以直接在页面按 Ctrl/⌘+V 粘贴图片。");
    return;
  }

  try {
    setStatus("读取剪贴板中…");
    const items = await navigator.clipboard.read();
    for (const item of items) {
      const imgType = item.types.find((t) => t.startsWith("image/"));
      if (!imgType) continue;
      const blob = await item.getType(imgType);
      const ext = imgType === "image/png" ? "png" : imgType === "image/jpeg" ? "jpg" : "img";
      const f = new File([blob], `clipboard.${ext}`, { type: imgType });
      setFile(f);
      setStatus("已从剪贴板获取图片");
      return;
    }
    showError("剪贴板里没有检测到图片。请先截图/复制图片，再点“从剪贴板获取”。");
    setStatus("");
  } catch (e) {
    showError("读取剪贴板失败：请允许浏览器访问剪贴板，或改用 Ctrl/⌘+V 粘贴。");
    setStatus("");
  }
}

function handlePasteEvent(e) {
  const cd = e.clipboardData;
  if (!cd || !cd.items) return;
  for (const it of cd.items) {
    if (it.kind === "file" && it.type && it.type.startsWith("image/")) {
      const blob = it.getAsFile();
      if (!blob) continue;
      const ext = it.type === "image/png" ? "png" : it.type === "image/jpeg" ? "jpg" : "img";
      const f = new File([blob], `paste.${ext}`, { type: it.type });
      setFile(f);
      setStatus("已粘贴图片");
      e.preventDefault();
      return;
    }
  }
}

if (pasteBtn) {
  pasteBtn.addEventListener("click", pasteFromClipboard);
}

window.addEventListener("paste", handlePasteEvent);

// 初始状态
clearAll();



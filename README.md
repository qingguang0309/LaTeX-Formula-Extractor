# LaTeX公式提取器

这是一个从图片中提取数学公式LaTeX代码的工具集合。

## 包含的文件

1. **latex_extractor.html** - Web版本（推荐）
   - 支持拖拽上传
   - 界面友好
   - 无需安装任何依赖

2. **latex_extractor.py** - Python命令行版本
   - 支持批处理
   - 可集成到其他程序中
   - 支持多种OCR API

## 使用方法

### Web版本
1. 在浏览器中打开 `latex_extractor.html`
2. 上传或拖拽图片
3. 点击提取按钮
4. 复制生成的LaTeX代码

### Python版本
```bash
python latex_extractor.py image.png output.tex
```

## OCR服务推荐

1. **Mathpix** (推荐)
   - 网址：https://mathpix.com/
   - 特点：专门针对数学公式优化，准确率高
   - 价格：有免费额度

2. **Microsoft Math Solver API**
   - 免费使用
   - 支持手写公式

3. **开源方案**
   - LaTeX-OCR: https://github.com/lukas-blecher/LaTeX-OCR
   - Pix2Text: https://github.com/breezedeus/Pix2Text

## 注意事项

- 当前版本为演示版，使用预定义的公式
- 实际使用需要配置相应的OCR API
- 建议使用清晰的公式图片以获得最佳效果

## 技术栈

- 前端：HTML5, CSS3, JavaScript
- 后端：Python 3
- OCR：Mathpix API / 其他数学OCR服务
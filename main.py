#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX公式提取器 - Python版本
使用方法：python latex_extractor.py <图片路径>
"""

import sys
import os
import base64
import requests
from PIL import Image
import io

class LaTeXExtractor:
    def __init__(self):
        # 这里可以配置你的OCR API密钥
        self.api_key = "YOUR_API_KEY"
        self.api_url = "https://api.mathpix.com/v3/text"  # Mathpix API示例
        
    def extract_from_image(self, image_path):
        """从图片中提取LaTeX代码"""
        if not os.path.exists(image_path):
            print(f"错误：找不到图片文件 {image_path}")
            return None
            
        try:
            # 读取图片并转换为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode()
            
            # 如果使用Mathpix API
            if self.api_key != "YOUR_API_KEY":
                headers = {
                    'app_id': 'your_app_id',
                    'app_key': self.api_key,
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'src': f'data:image/png;base64,{image_base64}',
                    'formats': ['latex_simplified'],
                    'ocr': ['math', 'text']
                }
                
                response = requests.post(self.api_url, json=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('latex_simplified', '')
                else:
                    print(f"API错误：{response.status_code}")
                    return None
            else:
                # 演示模式：返回示例LaTeX代码
                print("注意：当前为演示模式，请配置API密钥以使用真实OCR功能")
                return r"R^2 = 1 - \frac{\sum_{i=1}^{N}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{N}(y_i - \bar{y})^2}"
                
        except Exception as e:
            print(f"提取失败：{str(e)}")
            return None
            
    def save_to_file(self, latex_code, output_path):
        """保存LaTeX代码到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        print(f"LaTeX代码已保存到：{output_path}")

def main():
    if len(sys.argv) < 2:
        print("使用方法：python latex_extractor.py <图片路径> [输出文件路径]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.tex"
    
    extractor = LaTeXExtractor()
    
    print(f"正在处理图片：{image_path}")
    latex_code = extractor.extract_from_image(image_path)
    
    if latex_code:
        print("\n提取的LaTeX代码：")
        print("-" * 50)
        print(latex_code)
        print("-" * 50)
        
        # 保存到文件
        extractor.save_to_file(latex_code, output_path)
        
        # 复制到剪贴板（如果可用）
        try:
            import pyperclip
            pyperclip.copy(latex_code)
            print("\nLaTeX代码已复制到剪贴板！")
        except ImportError:
            print("\n提示：安装pyperclip库可以自动复制到剪贴板")
            print("pip install pyperclip")
    else:
        print("提取失败")

if __name__ == "__main__":
    main()
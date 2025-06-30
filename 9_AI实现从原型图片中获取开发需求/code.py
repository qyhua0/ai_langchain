from paddleocr import PaddleOCR
import ollama
import base64
import json
import os
from typing import Dict, List, Optional


class ImageRequirementParser:
    """图片解析开发需求工具类"""

    def __init__(self, ocr_lang: str = "ch"):
        """
        初始化OCR和模型配置
        Args:
            ocr_lang: OCR识别语言，默认中文
        """
        self.ocr = PaddleOCR(use_angle_cls=True, lang=ocr_lang)
        self.vision_model = "llama3.2-vision"
        self.analysis_model = "qwen3:14b"  # 可以根据实际情况调整

    def encode_image(self, image_path: str) -> str:
        """
        读取并编码图片为base64
        Args:
            image_path: 图片路径
        Returns:
            base64编码的图片字符串
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

    def extract_text_from_image(self, image_path: str) -> str:
        """
        从图片中提取文字
        Args:
            image_path: 图片路径
        Returns:
            提取的文字内容
        """
        try:
            result = self.ocr.ocr(image_path, cls=True)
            extracted_text = ""

            if result and len(result) > 0:
                for line in result:
                    if line:  # 确保line不为空
                        for word in line:
                            if word and len(word) > 1:  # 确保word格式正确
                                extracted_text += word[1][0] + " "

            return extracted_text.strip()
        except Exception as e:
            print(f"OCR识别出错: {e}")
            return ""

    def analyze_image_content(self, image_path: str) -> Dict:
        """
        分析图片内容，生成初步需求
        Args:
            image_path: 图片路径
        Returns:
            包含分析结果的字典
        """
        # 提取文字
        extracted_text = self.extract_text_from_image(image_path)
        print(f"提取的文字内容:\n{extracted_text}")
        print("-" * 50)

        # 方法1: 使用文件路径直接传递（推荐）
        analysis_result = self._analyze_with_file_path(image_path, extracted_text)

        if analysis_result.get("success", False):
            return analysis_result

        # 方法2: 使用base64编码（备用方案）
        print("文件路径方法失败，尝试base64编码方法...")
        return self._analyze_with_base64(image_path, extracted_text)

    def _analyze_with_file_path(self, image_path: str, extracted_text: str) -> Dict:
        """
        使用文件路径方式分析图片（推荐方法）
        """
        system_prompt = """你是一个专业的UI/UX分析师。请仔细分析这个界面截图，结合OCR提取的文字内容，生成结构化的需求分析。
重要提示：这是一个真实的UI界面截图，请认真观察界面中的所有元素。

请以JSON格式输出分析结果：
{
    "interface_type": "界面类型",
    "main_functions": ["主要功能列表"],
    "query_conditions": {
        "fields": ["查询字段名称"],
        "buttons": ["按钮名称及功能"]
    },
    "table_structure": {
        "columns": ["表格列名"],
        "operations": ["操作按钮"]
    },
    "form_fields": ["表单字段名称"],
    "layout_description": "界面布局描述",
    "ui_components": ["UI组件类型"]
}"""

        user_prompt = f"""这是一个UI界面截图。OCR提取的文字内容：
{extracted_text}

请基于图片内容分析：
1. 界面类型和主要功能
2. 查询条件字段和操作按钮
3. 表格结构和列名
4. 表单字段（如果有）
5. 整体布局和UI组件

请严格按照JSON格式返回结果。"""

        try:
            # 使用文件路径直接传递图片
            response = ollama.chat(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_prompt,
                        "images": [image_path]  # 直接传递文件路径
                    }
                ]
            )

            analysis_result = response['message']['content']
            print(f"文件路径方法分析结果:\n{analysis_result}")
            print("-" * 50)

            return {
                "extracted_text": extracted_text,
                "analysis_result": analysis_result,
                "success": True,
                "method": "file_path"
            }

        except Exception as e:
            print(f"文件路径方法失败: {e}")
            return {"error": f"文件路径方法失败: {e}", "success": False}

    def _analyze_with_base64(self, image_path: str, extracted_text: str) -> Dict:
        """
        使用base64编码方式分析图片（备用方法）
        """
        try:
            # 编码图片为base64
            with open(image_path, "rb") as img_file:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = "image/jpeg"

                img_data = img_file.read()
                base64_image = base64.b64encode(img_data).decode('utf-8')

            # 构建完整的base64数据URI
            data_uri = f"data:{mime_type};base64,{base64_image}"

            system_prompt = """你是一个专业的UI界面分析师。我将为你提供一个UI界面的截图和OCR提取的文字。
请仔细分析界面元素并以JSON格式返回结构化结果。"""

            user_prompt = f"""请分析这个UI界面截图。

OCR提取的文字：{extracted_text}

请识别并分析：
1. 界面的主要功能和类型
2. 查询条件和操作按钮
3. 表格结构
4. 表单字段
5. 整体布局

请以标准JSON格式返回分析结果。"""

            response = ollama.chat(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {
                        "role": "user",
                        "content": data_uri  # 使用完整的data URI
                    }
                ]
            )

            analysis_result = response['message']['content']
            print(f"Base64方法分析结果:\n{analysis_result}")
            print("-" * 50)

            return {
                "extracted_text": extracted_text,
                "analysis_result": analysis_result,
                "success": True,
                "method": "base64"
            }

        except Exception as e:
            print(f"Base64方法也失败: {e}")
            return {"error": f"所有图片分析方法都失败: {e}", "success": False}

    def generate_development_requirements(self, analysis_result: str, extracted_text: str = "") -> str:
        """
        基于初步分析生成详细的开发需求
        如果图片分析失败，则基于OCR文字生成需求
        Args:
            analysis_result: 初步分析结果
            extracted_text: OCR提取的文字（备用）
        Returns:
            详细的开发需求文档
        """
        # 如果图片分析失败，使用OCR文字生成需求
        if "失败" in analysis_result or "错误" in analysis_result:
            return self._generate_requirements_from_text(extracted_text)

        system_prompt = """你是一个高级软件开发需求分析师。
基于提供的UI界面分析结果，请生成详细的开发需求文档。
需求文档应该包含：
1. 功能需求概述
2. 详细的功能点列表
3. 数据结构设计建议
4. API接口需求
5. 前端组件需求
6. 用户交互流程
7. 技术实现建议
8. 可以直接用于开发的详细描述

请用专业的需求分析语言，确保开发人员能够直接根据这个需求进行开发。"""

        user_prompt = f"""基于以下UI界面分析结果，请生成完整的开发需求文档：

{analysis_result}

请生成一个详细的、可执行的开发需求文档，包含所有必要的技术细节和实现指导。"""

        try:
            response = ollama.chat(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            return response['message']['content']

        except Exception as e:
            return f"生成开发需求失败: {e}"

    def _generate_requirements_from_text(self, extracted_text: str) -> str:
        """
        仅基于OCR文字生成开发需求（备用方案）
        """
        if not extracted_text.strip():
            return "无法生成需求：图片分析失败且未提取到文字内容"

        system_prompt = """你是一个软件需求分析师。基于从UI界面中提取的文字内容，
推断界面功能并生成开发需求文档。虽然没有图片信息，但请尽力根据文字内容分析可能的界面结构和功能。"""

        user_prompt = f"""从UI界面中提取到以下文字内容：
{extracted_text}

请根据这些文字内容推断：
1. 这个界面的主要功能
2. 可能的表单字段和表格结构
3. 操作按钮和功能
4. 生成相应的开发需求文档

请提供详细的技术实现建议。"""

        try:
            response = ollama.chat(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            return f"""⚠️ 注意：此需求基于OCR文字生成，图片分析失败

{response['message']['content']}"""

        except Exception as e:
            return f"基于文字生成需求也失败: {e}"

    def parse_image_to_requirements(self, image_path: str) -> Dict:
        """
        完整的图片解析到开发需求的流程
        Args:
            image_path: 图片路径
        Returns:
            包含完整分析结果的字典
        """
        print(f"开始分析图片: {image_path}")
        print("=" * 60)

        # 步骤1&2&3: 分析图片内容
        analysis_data = self.analyze_image_content(image_path)

        if not analysis_data.get("success", False):
            return analysis_data

        # 步骤4: 生成详细开发需求
        print("正在生成详细开发需求...")
        detailed_requirements = self.generate_development_requirements(
            analysis_data["analysis_result"],
            analysis_data["extracted_text"]
        )

        # 整合结果
        final_result = {
            "image_path": image_path,
            "extracted_text": analysis_data["extracted_text"],
            "initial_analysis": analysis_data["analysis_result"],
            "detailed_requirements": detailed_requirements,
            "success": True
        }

        return final_result

    def save_requirements_to_file(self, requirements: Dict, output_path: str = "requirements.md"):
        """
        将需求保存到文件
        Args:
            requirements: 需求字典
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 图片解析开发需求文档\n\n")
                f.write(f"**图片路径**: {requirements.get('image_path', 'N/A')}\n\n")
                f.write("## 提取的文字内容\n\n")
                f.write(f"```\n{requirements.get('extracted_text', 'N/A')}\n```\n\n")
                f.write("## 初步分析结果\n\n")
                f.write(f"{requirements.get('initial_analysis', 'N/A')}\n\n")
                f.write("## 详细开发需求\n\n")
                f.write(f"{requirements.get('detailed_requirements', 'N/A')}\n\n")
                f.write(f"---\n*生成时间: {__import__('datetime').datetime.now()}*\n")

            print(f"需求文档已保存到: {output_path}")

        except Exception as e:
            print(f"保存文件失败: {e}")


def main():
    """主函数示例"""
    # 初始化解析器
    parser = ImageRequirementParser()

    # 图片路径
    image_path = r'E:\dev\test.jpg'  # 请替换为实际图片路径

    try:
        # 执行完整的解析流程
        result = parser.parse_image_to_requirements(image_path)

        if result.get("success", False):
            print("=" * 60)
            print("✅ 解析完成！")
            print("\n📝 详细开发需求:")
            print(result["detailed_requirements"])

            # 保存到文件
            parser.save_requirements_to_file(result, "generated_requirements.md")

        else:
            print("❌ 解析失败:")
            print(result.get("error", "未知错误"))

    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == '__main__':
    main()
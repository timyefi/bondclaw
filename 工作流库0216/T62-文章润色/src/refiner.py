# -*- coding: utf-8 -*-
"""
T62-文章润色 核心模块
提供Markdown文章润色功能
"""

import markdown
import re
import openai
from typing import List, Optional
import config


class ArticleRefiner:
    """文章润色类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化润色器

        Args:
            api_key: API密钥，如不提供则从环境变量获取
            base_url: API基础URL
            model: 使用的模型名称
        """
        self.api_key = api_key or config.DASHSCOPE_API_KEY
        self.base_url = base_url or config.DASHSCOPE_BASE_URL
        self.model = model or config.MODEL_NAME

        if not self.api_key:
            raise ValueError("API密钥未设置，请设置DASHSCOPE_API_KEY环境变量")

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def read_markdown_file(self, file_path: str) -> str:
        """
        读取Markdown文件内容

        Args:
            file_path: Markdown文件路径

        Returns:
            文件内容字符串
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def split_into_paragraphs(self, md_content: str) -> List[str]:
        """
        将Markdown内容分割成段落

        Args:
            md_content: Markdown内容

        Returns:
            段落列表
        """
        html_content = markdown.markdown(md_content)
        paragraphs = re.split(r'<p>(.*?)</p>', html_content)[1::2]
        return paragraphs

    def refine_paragraph(self, paragraph: str) -> str:
        """
        调用大模型润色单个段落

        Args:
            paragraph: 待润色的段落

        Returns:
            润色后的段落
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': config.REFINE_SYSTEM_PROMPT},
                {'role': 'user', 'content': config.REFINE_USER_PROMPT_TEMPLATE.format(paragraph=paragraph)}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
            stream=False
        )
        refined_text = completion.choices[0].message.content.strip()
        return refined_text

    def apply_refinement(self, md_content: str) -> str:
        """
        逐段调用润色函数并保持Markdown格式

        Args:
            md_content: 原始Markdown内容

        Returns:
            润色后的Markdown内容
        """
        paragraphs = self.split_into_paragraphs(md_content)
        refined_paragraphs = [self.refine_paragraph(p) for p in paragraphs]
        refined_md_content = "\n\n".join(refined_paragraphs)
        return refined_md_content

    def save_refined_markdown(self, refined_md_content: str, output_file: str) -> None:
        """
        保存润色后的Markdown内容到文件

        Args:
            refined_md_content: 润色后的内容
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(refined_md_content)

    def process_file(self, input_file: str, output_file: str) -> str:
        """
        处理单个文件：读取、润色、保存

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径

        Returns:
            润色后的内容
        """
        md_content = self.read_markdown_file(input_file)
        refined_md_content = self.apply_refinement(md_content)
        self.save_refined_markdown(refined_md_content, output_file)
        return refined_md_content

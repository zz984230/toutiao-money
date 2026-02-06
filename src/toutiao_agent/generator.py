"""评论生成器模块"""

from pathlib import Path
from typing import Optional
from .config import config


class CommentGenerator:
    """评论生成器类"""

    def __init__(self, prompt_path: Optional[str] = None):
        self.prompt_path = prompt_path or "prompts/comment_generation.txt"
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """加载提示词模板"""
        prompt_file = Path(self.prompt_path)
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return '''你是一个真实的头条用户，正在对新闻发表评论。

新闻标题：{title}
新闻摘要：{abstract}

要求：
1. 长度：50-100字
2. 必须有明确的个人立场（支持/反对/质疑）
3. 使用口语化表达，加入情感词汇
4. 避免"综上所述"、"首先其次"等AI常用词
5. 可以用适当的感叹词、反问句
6. 如果是争议话题，不要骑墙，选边站

参考风格：
- 这事儿吧，我觉得...
- 说实话，我真的不理解...
- 我就问一句，这合理吗？

请直接输出评论，不要任何解释：'''

    def generate_prompt(self, title: str, abstract: str = "") -> str:
        """生成完整的提示词"""
        return self.prompt_template.format(
            title=title,
            abstract=abstract[:200] if abstract else ""
        )

    def generate_comment(self, title: str, abstract: str = "") -> str:
        """
        生成评论（需要外部调用Claude API）

        这个方法返回提示词，实际调用者需要将提示词发送给Claude获取回复
        """
        return self.generate_prompt(title, abstract)

    def save_prompt(self, prompt: str):
        """保存提示词到文件"""
        prompt_file = Path(self.prompt_path)
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)


# 全局实例
generator = CommentGenerator()

# -*- coding: utf-8 -*-
"""发布评论到头条文章"""
import asyncio
import sys
import json
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from toutiao_agent.toutiao_client import ToutiaoClient
from toutiao_agent.storage import storage


async def publish_comment(article_id: str, content: str) -> dict:
    """发布评论到指定文章

    Args:
        article_id: 文章ID
        content: 评论内容

    Returns:
        dict: 发布结果 {'success': bool, 'message': str}
    """
    client = ToutiaoClient()
    await client.start()

    try:
        print("检查登录状态...")
        if not await client.ensure_login():
            return {'success': False, 'message': '登录失败'}

        print(f"正在发布评论到文章 {article_id}...")
        print(f"评论内容: {content}")

        result = await client.post_comment(article_id, content)

        if result.get('success'):
            # 记录到数据库
            storage.add_comment(
                article_id=article_id,
                content=content
            )
            print("[SUCCESS] 评论已发布")
            return {'success': True, 'message': '评论发布成功'}
        else:
            error = result.get('error', '未知错误')
            print("[FAILED] " + error)
            return {'success': False, 'message': error}

    except Exception as e:
        error_msg = "发布评论异常: " + str(e)
        print("[ERROR] " + error_msg)
        return {'success': False, 'message': error_msg}

    finally:
        await client.close()


async def main():
    """从命令行参数获取文章ID和评论内容"""
    if len(sys.argv) < 3:
        print("用法: python publish_comment.py <article_id> <content>")
        print("示例: python publish_comment.py 7400000000000000001 '这是我的评论'")
        return

    article_id = sys.argv[1]
    content = sys.argv[2]

    result = await publish_comment(article_id, content)

    # 输出JSON格式结果供程序解析
    print("\n=== 结果 ===")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

# -*- coding: utf-8 -*-
"""清理 toutiao-inspiration 过程中产生的临时文件

临时文件定义：
- data/temp_*.py（临时分析脚本）
- data/publish_weitou.py（临时发布脚本）
- data/debug/*.png, data/debug/*.html（调试文件，可选）

保留文件：
- data/cookies.json（登录状态）
- data/*.json（话题数据、已参与记录）
- data/published_screenshot.png（发布证据）
"""
import os
import sys
from pathlib import Path
import glob

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def get_project_root():
    """获取项目根目录

    脚本位于 .claude/skills/toutiao-inspiration/scripts/
    需要向上 5 级到达项目根目录
    """
    current = Path(__file__).resolve()
    # 向上查找包含 pyproject.toml 或 .git 的目录
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    # 回退：向上 5 级
    return current.parent.parent.parent.parent.parent


def cleanup_temp_files(project_root=None, dry_run=False, keep_debug=False):
    """清理临时文件

    Args:
        project_root: 项目根目录，默认自动获取
        dry_run: 是否只显示将要删除的文件，不实际删除
        keep_debug: 是否保留调试文件（debug/*.png, debug/*.html）

    Returns:
        deleted: 已删除的文件列表
        kept: 保留的文件列表
    """
    if project_root is None:
        project_root = get_project_root()

    data_dir = project_root / "data"
    debug_dir = data_dir / "debug"

    # 定义要清理的文件模式
    temp_patterns = [
        ("temp_*.py", data_dir),
        ("temp_*.json", data_dir),
        ("publish_weitou.py", data_dir),
        ("published_screenshot.png", data_dir),
    ]

    # 调试文件模式（如果 keep_debug=False）
    if not keep_debug:
        temp_patterns.extend([
            ("*.png", debug_dir),
            ("*.html", debug_dir),
        ])

    deleted = []
    kept = []

    for pattern, base_dir in temp_patterns:
        # 使用 Path.glob() 代替 glob.glob
        for file_path in base_dir.glob(pattern):
            file_path = Path(file_path)

            # 跳过不存在的文件
            if not file_path.exists():
                continue

            # 检查是否是重要文件（双重保险）
            if file_path.name in ["cookies.json"]:
                kept.append(file_path)
                continue

            if dry_run:
                print(f"[DRY RUN] 将删除: {file_path.relative_to(project_root)}")
                deleted.append(file_path)
            else:
                try:
                    file_path.unlink()
                    print(f"✓ 已删除: {file_path.relative_to(project_root)}")
                    deleted.append(file_path)
                except Exception as e:
                    print(f"✗ 删除失败 {file_path.relative_to(project_root)}: {e}")
                    kept.append(file_path)

    return deleted, kept


def list_temp_files(project_root=None):
    """列出所有临时文件"""
    if project_root is None:
        project_root = get_project_root()

    data_dir = project_root / "data"
    debug_dir = data_dir / "debug"

    # 定义要查找的文件模式
    temp_patterns = [
        ("temp_*.py", data_dir),
        ("temp_*.json", data_dir),
        ("publish_weitou.py", data_dir),
        ("published_screenshot.png", data_dir),
        ("*.png", debug_dir),
        ("*.html", debug_dir),
    ]

    print("\n临时文件列表：")
    print("=" * 80)

    found = False
    for pattern, base_dir in temp_patterns:
        for file_path in base_dir.glob(pattern):
            if file_path.exists() and file_path.is_file():
                size = file_path.stat().st_size
                print(f"  {file_path.relative_to(project_root)} ({size} bytes)")
                found = True

    if not found:
        print("  （没有找到临时文件）")

    print("=" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="清理 toutiao-inspiration 临时文件")
    parser.add_argument("--dry-run", "-n", action="store_true", help="只显示将要删除的文件，不实际删除")
    parser.add_argument("--keep-debug", "-k", action="store_true", help="保留调试文件（debug/*.png, debug/*.html）")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有临时文件")
    args = parser.parse_args()

    project_root = get_project_root()

    if args.list:
        list_temp_files(project_root)
        return

    if args.dry_run:
        print("\n[DRY RUN 模式] 不会实际删除文件\n")

    print("清理 toutiao-inspiration 临时文件...")
    print("=" * 80)

    deleted, kept = cleanup_temp_files(
        project_root=project_root,
        dry_run=args.dry_run,
        keep_debug=args.keep_debug
    )

    print("\n" + "=" * 80)
    if args.dry_run:
        print(f"[DRY RUN] 将删除 {len(deleted)} 个文件")
    else:
        print(f"✓ 已删除 {len(deleted)} 个临时文件")

    if kept:
        print(f"✓ 保留了 {len(kept)} 个文件")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

#!/usr/bin/env python3
"""把本仓库 skills/ 下的公开技能链接到 agent 技能目录（默认 ~/.agents/skills）。

跨平台，纯 Python 标准库，不依赖平台特有 shell：
- Windows: 优先建 junction（目录联接，无需管理员/开发者模式），不可用时退回 symlink
- Linux / macOS: 建 symlink

用法:
  python scripts/install.py                    # add：链接全部技能（默认命令，幂等）
  python scripts/install.py add git-finish     # 只链接指定技能
  python scripts/install.py status             # 查看各技能的链接状态
  python scripts/install.py remove             # 移除本仓库技能的链接（只删链接本身）
  python scripts/install.py remove --force     # 连指向别处的链接一并移除

子命令通用 flags:
  -t, --target DIR    技能目录，默认 ~/.agents/skills
  -n, --dry-run       只演示将要做的操作，不实际改动（status 无此选项）

状态符号: + 新建  = 已正确链接/跳过  ~ 重建或指向别处
          ! 受阻（实体目录/失败）  ? 需 --force  - 已移除/未链接

约定与保护:
- ~/.agents/skills/<name> 若是实体目录（私有技能），一律不动。
- 已是指向本仓库的链接 → 跳过；指向别处的旧链接 → 重建。
- status 的退出码：全部技能已正确链接为 0，否则为 1，可用于脚本探测。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_SKILLS = REPO_ROOT / "skills"
DEFAULT_TARGET = Path.home() / ".agents" / "skills"
COMMANDS = ("add", "remove", "status")


def normcase(p: Path) -> str:
    return os.path.normcase(os.path.normpath(str(p)))


def resolve(p: Path) -> str:
    return normcase(Path(os.path.realpath(p)))


def is_link(p: Path) -> bool:
    """symlink 或 Windows junction 都算链接。"""
    if p.is_symlink():
        return True
    if os.name == "nt":
        isjunction = getattr(os.path, "isjunction", None)  # Python 3.12+
        if isjunction is not None:
            return isjunction(p)
        try:  # 老 Python 兜底：重解析点会被 realpath 解析到别处
            return resolve(p) != normcase(p)
        except OSError:
            return False
    return False


def create_link(target: Path, link: Path) -> str:
    """在 link 处建立指向 target 的目录链接，返回所用机制。"""
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return "junction"
        except (ImportError, OSError):
            pass  # junction 建不了（如非常规文件系统），退回 symlink
        os.symlink(str(target), str(link), target_is_directory=True)
        return "symlink"
    os.symlink(str(target), str(link))
    return "symlink"


def remove_link(link: Path) -> None:
    """只删链接本身，不碰链接指向的内容。"""
    if os.name == "nt":
        os.rmdir(str(link))  # Windows 删 junction/symlink-to-dir 用 rmdir
    else:
        os.remove(str(link))  # POSIX 上 unlink 符号链接本身


def link_one(src: Path, dst: Path, dry_run: bool) -> tuple[str, str]:
    """在 dst 建立指向 src 的链接，返回 (符号, 说明)。"""
    if is_link(dst):
        if resolve(dst) == resolve(src):
            return "=", "已链接，跳过"
        old = resolve(dst)
        if dry_run:
            return "~", f"旧链接指向 {old}，将重建（dry-run 未改动）"
        remove_link(dst)
        mech = create_link(src, dst)
        return "~", f"旧链接指向 {old}，已重建为 {mech} → {src}"
    if dst.exists():
        return "!", "已存在实体目录，跳过（私有技能不动）"
    if dry_run:
        return "+", f"将创建链接 → {src}（dry-run 未改动）"
    mech = create_link(src, dst)
    return "+", f"已创建 {mech} → {src}"


def remove_one(dst: Path, expected: str, force: bool, dry_run: bool) -> tuple[str, str]:
    if not is_link(dst):
        if dst.exists():
            return "!", "不是链接，实体目录不动"
        return "-", "本来就不存在"
    if resolve(dst) != expected and not force:
        return "?", f"链接指向 {resolve(dst)}，非本仓库技能（--force 可强制移除）"
    if dry_run:
        return "-", "将移除链接（dry-run 未改动）"
    remove_link(dst)
    return "-", "已移除"


def status_one(dst: Path, expected: str) -> tuple[str, str, bool]:
    """返回 (符号, 说明, 是否已正确链接)。"""
    if is_link(dst):
        if resolve(dst) == expected:
            return "=", "已链接", True
        return "~", f"链接指向 {resolve(dst)}（非本仓库）", False
    if dst.exists():
        return "!", "实体目录（私有技能）", False
    return "-", "未链接", False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/install.py",
        description="把本仓库 skills/ 下的技能链接到 agent 技能目录（默认 ~/.agents/skills）。",
        epilog="不带子命令时等价于 add，如：python scripts/install.py git-finish",
    )
    sub = parser.add_subparsers(dest="command", metavar="{add,remove,status}")

    def common(p: argparse.ArgumentParser, with_dry_run: bool) -> None:
        p.add_argument("names", nargs="*", help="技能名，缺省为仓库里全部技能")
        p.add_argument(
            "-t", "--target", default=None, help="技能目录，默认 ~/.agents/skills"
        )
        if with_dry_run:
            p.add_argument(
                "-n", "--dry-run", action="store_true", help="只演示将做什么，不实际改动"
            )

    p_add = sub.add_parser("add", help="建立/修复链接（默认命令）")
    common(p_add, with_dry_run=True)

    p_remove = sub.add_parser("remove", help="移除链接（只删链接本身，不动实体目录）")
    common(p_remove, with_dry_run=True)
    p_remove.add_argument(
        "--force", action="store_true", help="移除非本仓库技能的链接"
    )

    p_status = sub.add_parser(
        "status", help="查看各技能链接状态（有未链接项时退出码为 1）"
    )
    common(p_status, with_dry_run=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # 兼容旧用法：首个参数是技能名（不以 - 开头、非子命令）时按 add 处理
    if (
        argv
        and argv[0] not in COMMANDS
        and argv[0] not in ("-h", "--help")
        and not argv[0].startswith("-")
    ):
        argv.insert(0, "add")
    args = build_parser().parse_args(argv)
    command = args.command or "add"

    if not REPO_SKILLS.is_dir():
        print(f"错误：找不到 {REPO_SKILLS}", file=sys.stderr)
        return 1
    available = sorted(
        d.name for d in REPO_SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )
    if not available:
        print(f"错误：{REPO_SKILLS} 下没有任何技能", file=sys.stderr)
        return 1

    names = list(dict.fromkeys(args.names)) or available
    unknown = [n for n in names if n not in available]
    if unknown:
        print(
            f"错误：skills/ 下没有 {'、'.join(unknown)}（可用：{'、'.join(available)}）",
            file=sys.stderr,
        )
        return 1

    target_dir = Path(args.target).expanduser() if args.target else DEFAULT_TARGET
    dry_run = getattr(args, "dry_run", False)
    if command != "status" and not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    print(f"仓库: {REPO_SKILLS}")
    suffix = "（dry-run 预览，不改动）" if dry_run else ""
    print(f"目标: {target_dir}{suffix}")

    failed = False
    for name in names:
        src = Path(os.path.realpath(REPO_SKILLS / name))
        dst = target_dir / name
        try:
            if command == "add":
                symbol, message = link_one(src, dst, dry_run)
            elif command == "remove":
                symbol, message = remove_one(
                    dst, resolve(src), args.force, dry_run
                )
            else:
                symbol, message, linked = status_one(dst, resolve(src))
                failed |= not linked
        except OSError as exc:
            symbol, message = "!", f"失败：{exc}"
            failed = True
        print(f"{symbol} {name}: {message}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

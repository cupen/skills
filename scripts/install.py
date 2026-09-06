#!/usr/bin/env python3
"""把本仓库的技能与 subagent 定义安装进各 agent 工具。

- 技能（skills/<name>/SKILL.md）：逐个**链接**到技能目录（默认 ~/.agents/skills），
  单一真源、改完即时生效。
- subagents（subagents/<name>.md）：真源统一按 Claude Code subagent 标准定义（frontmatter
  的 name/description + Markdown 正文即系统提示词）；安装时**按目标工具转换格式后
  写入**（转换式安装，不是链接），改了源文件重跑安装命令同步，status 会提示内容漂移：

    claude    ~/.claude/agents/<name>.md           Claude Code 格式（原样）
    zcode     ~/.zcode/agents/<name>.md            camelCase frontmatter，正文即提示词
    codex     ~/.codex/agents/<name>.toml          OpenAI Codex agent role，正文→developer_instructions
    gemini    ~/.gemini/agents/<name>.md           snake_case 键（如 max_turns），正文即提示词
    opencode  ~/.config/opencode/agents/<name>.md  文件名即身份，强制 mode: subagent
    copilot   ~/.copilot/agents/<name>.agent.md    VS Code / GitHub Copilot 自定义 agent

  源文件 frontmatter 里可用 `targets:` 段按目标补字段（键用目标的原生拼写）：
      targets:
        codex:
          sandbox_mode: workspace-write
  映射不到目标的原生字段会被丢弃并警告。
  DeepSeek Harness (dsh) 目前没有基于文件的 subagent 定义（插件化 preset），暂无对应目标。

跨平台，纯 Python 标准库，不依赖平台特有 shell。技能链接：
- Windows: 优先建 junction（无需管理员/开发者模式），不可用时退回 symlink
- Linux / macOS: 建 symlink

用法:
  python scripts/install.py                      # 一键安装：全部技能 + 全部 subagent（默认，幂等）
  python scripts/install.py skill [名称...]       # 只装技能
  python scripts/install.py subagent [名称...]    # 只装 subagent（默认目标 claude,zcode）
  python scripts/install.py subagent --to all    # subagent 装到全部目标
  python scripts/install.py status [skill|subagent] [--to 目标]            # 查看状态（未就位 exit 1）
  python scripts/install.py remove [skill|subagent] [--to 目标] [--force]  # 卸载

flags（只有这三个）:
  -n         预览模式：只演示将做什么，不改动
  --to       subagent 的安装目标，可重复、可逗号分隔，all=全部；默认 claude,zcode
  --force    remove 时连内容不一致的文件/非本仓库链接一起移除

技能固定链接到 ~/.agents/skills（各工具共享的技能根目录，skills CLI、dsh 也读它）。

状态符号: + 新建  = 已安装且一致/已链接  ~ 内容漂移将更新
          ! 受阻（实体目录/失败）  ? 需 --force  - 已移除/未安装

约定与保护:
- 技能目标处若已存在实体目录（私有技能），一律不动；subagents 只覆盖本脚本生成的同名
  文件，实体目录不碰；绝不通过链接写进本仓库 subagents/。
- status 的退出码：全部就位为 0，否则为 1，可用于脚本探测。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_SKILLS = REPO_ROOT / "skills"
REPO_SUBAGENTS = REPO_ROOT / "subagents"
DEFAULT_TARGET = Path.home() / ".agents" / "skills"


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


# ---------------------------------------------------------------------------
# 技能：逐个链接
# ---------------------------------------------------------------------------


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
        return "!", "已存在实体目录，跳过（私有内容不动）"
    if dry_run:
        return "+", f"将创建链接 → {src}（dry-run 未改动）"
    mech = create_link(src, dst)
    return "+", f"已创建 {mech} → {src}"


def remove_link_one(dst: Path, expected: str, force: bool, dry_run: bool) -> tuple[str, str]:
    if not is_link(dst):
        if dst.exists():
            return "!", "不是链接，实体目录不动"
        return "-", "本来就不存在"
    if resolve(dst) != expected and not force:
        return "?", f"链接指向 {resolve(dst)}，非本仓库（--force 可强制移除）"
    if dry_run:
        return "-", "将移除链接（dry-run 未改动）"
    remove_link(dst)
    return "-", "已移除"


def status_link_one(dst: Path, expected: str) -> tuple[str, str, bool]:
    """返回 (符号, 说明, 是否已正确链接)。"""
    if is_link(dst):
        if resolve(dst) == expected:
            return "=", "已链接", True
        return "~", f"链接指向 {resolve(dst)}（非本仓库）", False
    if dst.exists():
        return "!", "实体目录（私有内容）", False
    return "-", "未链接", False


def discover_skills() -> list[str]:
    if not REPO_SKILLS.is_dir():
        return []
    return sorted(
        d.name for d in REPO_SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    )


def run_skills(command: str, names: list[str], target: Path, force: bool, dry_run: bool) -> bool:
    """处理技能链接，返回是否失败。names 为空表示全部。"""
    available = discover_skills()
    if not available:
        print(f"错误：{REPO_SKILLS} 下没有任何技能", file=sys.stderr)
        return True
    if names:
        unknown = [n for n in names if n not in available]
        if unknown:
            print(
                f"错误：skills/ 下没有 {'、'.join(unknown)}（可用：{'、'.join(available)}）",
                file=sys.stderr,
            )
            return True
    else:
        names = available

    failed = False
    print(f"技能: {REPO_SKILLS}")
    print(f"  目标: {short(target)}")
    for name in names:
        src = Path(os.path.realpath(REPO_SKILLS / name))
        dst = target / name
        try:
            if command == "add":
                symbol, message = link_one(src, dst, dry_run)
            elif command == "remove":
                symbol, message = remove_link_one(dst, resolve(src), force, dry_run)
            else:
                symbol, message, linked = status_link_one(dst, resolve(src))
                failed |= not linked
        except OSError as exc:
            symbol, message = "!", f"失败：{exc}"
            failed = True
        print(f"  {symbol} {name}: {message}")
    return failed


# ---------------------------------------------------------------------------
# subagents：解析 → 按目标转换 → 写入
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$")


def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [_strip_quotes(v.strip()) for v in inner.split(",")] if inner else []
    return _strip_quotes(raw)


def parse_subagent_file(p: Path) -> tuple[dict, dict, str]:
    """解析 subagents/<name>.md，返回 (frontmatter, targets 按目标覆盖, 正文)。

    只支持本仓库用到的 YAML 子集：顶层 `key: value`、内联列表 `[a, b]`、
    两层嵌套的 targets 段。解析失败抛 ValueError。
    """
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("缺少 '---' 开头的 YAML frontmatter")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("frontmatter 没有闭合的 '---'")

    fm: dict = {}
    overrides: dict = {}
    scope: tuple[str, ...] = ()  # () | ("targets",) | ("targets", <目标名>)
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _KEY_RE.match(stripped)
        if not m:
            raise ValueError(f"无法解析 frontmatter 行：{line!r}")
        key, raw = m.group(1), m.group(2)
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            if key == "targets" and raw == "":
                scope = ("targets",)
            else:
                scope = ()
                fm[key] = _parse_scalar(raw)
        elif scope and scope[0] == "targets" and len(scope) <= 2 and indent < 4 and raw == "":
            # targets: 下新的目标名（含兄弟目标）
            scope = ("targets", key)
            overrides[key] = {}
        elif len(scope) == 2 and scope[0] == "targets" and indent >= 4:
            overrides[scope[1]][key] = _parse_scalar(raw)
        else:
            raise ValueError(f"无法解析 frontmatter 行（缩进或位置不对）：{line!r}")
    body = "\n".join(lines[end + 1:]).strip("\n")
    return fm, overrides, body


def discover_subagents() -> list[Path]:
    if not REPO_SUBAGENTS.is_dir():
        return []
    return sorted(p for p in REPO_SUBAGENTS.glob("*.md") if p.is_file())


@dataclass
class Target:
    key: str
    dirname: Path
    filename: str  # "{name}" 占位
    fmt: str  # "md" | "toml"
    fields: tuple  # ((源字段, 目标字段), ...)；不在表里的源字段丢弃并警告
    prompt_field: str | None  # None = 正文即提示词（md）；否则为提示词字段名（toml）
    fixed: dict = field(default_factory=dict)  # 固定注入字段
    tools_list: bool = False  # tools 以列表输出（否则保留源写法）


TARGETS: dict[str, Target] = {
    "claude": Target(
        key="claude",
        dirname=Path.home() / ".claude" / "agents",
        filename="{name}.md",
        fmt="md",
        fields=(
            ("name", "name"), ("description", "description"), ("model", "model"),
            ("tools", "tools"), ("disallowedTools", "disallowedTools"),
            ("maxTurns", "maxTurns"), ("color", "color"), ("mcpServers", "mcpServers"),
            ("permissionMode", "permissionMode"),
            ("author", "author"), ("version", "version"),
        ),
        prompt_field=None,
    ),
    "zcode": Target(
        key="zcode",
        dirname=Path.home() / ".zcode" / "agents",
        filename="{name}.md",
        fmt="md",
        fields=(
            ("name", "name"), ("description", "description"), ("model", "model"),
            ("tools", "tools"), ("disallowedTools", "disallowedTools"),
            ("maxTurns", "maxTurns"), ("color", "color"), ("mcpServers", "mcpServers"),
            ("thoughtLevel", "thoughtLevel"), ("injectAgentsMd", "injectAgentsMd"),
            ("author", "author"), ("version", "version"),
        ),
        prompt_field=None,
    ),
    "codex": Target(
        key="codex",
        dirname=Path.home() / ".codex" / "agents",
        filename="{name}.toml",
        fmt="toml",
        fields=(
            ("name", "name"), ("description", "description"), ("model", "model"),
        ),
        prompt_field="developer_instructions",
    ),
    "gemini": Target(
        key="gemini",
        dirname=Path.home() / ".gemini" / "agents",
        filename="{name}.md",
        fmt="md",
        fields=(
            ("name", "name"), ("description", "description"), ("model", "model"),
            ("tools", "tools"), ("mcpServers", "mcpServers"),
            ("maxTurns", "max_turns"), ("temperature", "temperature"),
            ("author", "author"), ("version", "version"),
        ),
        prompt_field=None,
        tools_list=True,
    ),
    "opencode": Target(
        key="opencode",
        dirname=Path.home() / ".config" / "opencode" / "agents",
        filename="{name}.md",
        fmt="md",
        fields=(
            ("description", "description"), ("model", "model"),
            ("temperature", "temperature"),
            ("author", "author"), ("version", "version"),
        ),
        prompt_field=None,
        fixed={"mode": "subagent"},  # 文件名即身份，强制为 subagent 模式
    ),
    "copilot": Target(
        key="copilot",
        dirname=Path.home() / ".copilot" / "agents",
        filename="{name}.agent.md",
        fmt="md",
        fields=(
            ("name", "name"), ("description", "description"), ("model", "model"),
            ("tools", "tools"), ("mcpServers", "mcp-servers"),
            ("author", "author"), ("version", "version"),
        ),
        prompt_field=None,
        tools_list=True,
    ),
}


def _yaml_scalar(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_yaml_scalar(x) for x in v) + "]"
    s = str(v)
    if s == "" or re.search(r"[:#{}\[\],&*?|>'\"%@`]", s) or s != s.strip():
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def emit_md(fields: dict, body: str) -> str:
    fm = "\n".join(f"{k}: {_yaml_scalar(v)}" for k, v in fields.items())
    return f"---\n{fm}\n---\n\n{body}\n"


def _toml_str(s: str) -> str:
    out = '"'
    for ch in s:
        if ch == '"':
            out += '\\"'
        elif ch == "\\":
            out += "\\\\"
        elif ch == "\n":
            out += "\\n"
        elif ch == "\t":
            out += "\\t"
        elif ord(ch) < 0x20:
            out += f"\\u{ord(ch):04X}"
        else:
            out += ch
    return out + '"'


def _toml_value(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_toml_str(str(x)) for x in v) + "]"
    s = str(v)
    if s.lower() in ("true", "false"):
        return s.lower()
    if re.fullmatch(r"-?\d+", s):
        return s
    return _toml_str(s)


def _toml_multiline(s: str) -> str:
    """系统提示词进 TOML：优先字面量多行字符串（零转义），含 ''' 时退回基本多行。"""
    if "'''" not in s:
        return "'''" + s + "'''"
    body = s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    if body.endswith('"'):
        body = body[:-1] + '\\"'
    return '"""' + body + '"""'


def emit_toml(prompt_field: str, fields: dict, body: str) -> str:
    lines = ["# 由 agent-kit scripts/install.py 生成；请修改仓库 subagents/ 源文件后重装，勿直接改本文件。"]
    for k, v in fields.items():
        lines.append(f"{k} = {_toml_value(v)}")
    lines.append(f"{prompt_field} = {_toml_multiline(body)}")
    return "\n".join(lines) + "\n"


def convert_subagent(name: str, fm: dict, overrides: dict, body: str, t: Target) -> tuple[str, list[str]]:
    """把源 subagent 定义转换为目标格式，返回 (内容, 丢弃警告)。"""
    warnings: list[str] = []
    fields: dict = {}
    mapped = set()
    for src, dst in t.fields:
        if src not in fm:
            continue
        mapped.add(src)
        v = fm[src]
        if src == "tools" and t.tools_list and isinstance(v, str):
            v = [x.strip() for x in v.split(",") if x.strip()]
        fields[dst] = v
    for k in fm:
        if k not in mapped and k != "name" and k != "targets":
            warnings.append(f"{t.key} 不支持 {k}，已丢弃")
    fields.update(t.fixed)
    fields.update(overrides.get(t.key) or {})
    if t.fmt == "toml":
        return emit_toml(t.prompt_field, fields, body), warnings
    return emit_md(fields, body), warnings


def short(p: Path) -> str:
    s = str(p)
    home = str(Path.home())
    if s.startswith(home):
        s = "~" + s[len(home):]
    return s.replace(os.sep, "/")


def _prepare_target_dir(t: Target, command: str, dry_run: bool) -> bool:
    """检查目标目录可写。处理旧版整目录链接的自动迁移；返回 False 表示跳过该目标。"""
    d = t.dirname
    if is_link(d):
        if resolve(d) == resolve(REPO_SUBAGENTS):
            if command == "add" and not dry_run:
                remove_link(d)
                print(f"  ~ {short(d)}: 已移除旧版整目录链接，改为转换式安装")
                return True
            print(f"  ~ {short(d)}: 旧版整目录链接，重跑 add 自动迁移为转换式安装")
            return False
        print(f"  ! {short(d)}: 是指向别处的链接，跳过（不写入他人目录）")
        return False
    if d.exists() and not d.is_dir():
        print(f"  ! {short(d)}: 已存在同名文件，无法作为目标目录")
        return False
    return True


def _is_inside_repo_subagents(dst: Path) -> bool:
    root = resolve(REPO_SUBAGENTS)
    r = resolve(dst)
    return r == root or r.startswith(root + os.sep)


def write_one(dst: Path, content: str, dry_run: bool) -> tuple[str, str]:
    if dst.is_symlink() or _is_inside_repo_subagents(dst):
        return "!", "目标是链接或落在本仓库 subagents/ 内，拒绝写入"
    if dst.is_dir():
        return "!", "目标位置是实体目录，跳过"
    if dst.exists():
        if dst.read_text(encoding="utf-8", errors="replace") == content:
            return "=", "内容一致，跳过"
        if dry_run:
            return "~", "内容不同，将覆盖（dry-run 未改动）"
        dst.write_text(content, encoding="utf-8", newline="\n")
        return "~", "内容不同，已覆盖"
    if dry_run:
        return "+", "将写入（dry-run 未改动）"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8", newline="\n")
    return "+", "已写入"


def unlink_one(dst: Path, content: str, force: bool, dry_run: bool) -> tuple[str, str]:
    if is_link(dst):
        if not force:
            return "?", "是链接，非本脚本产物（--force 可移除）"
        if dry_run:
            return "-", "将移除链接（dry-run 未改动）"
        remove_link(dst)
        return "-", "已移除链接"
    if not dst.exists():
        return "-", "本来就不存在"
    if dst.read_text(encoding="utf-8", errors="replace") != content and not force:
        return "?", "内容与当前生成结果不同（手工改过或旧版），--force 可强制删除"
    if dry_run:
        return "-", "将删除（dry-run 未改动）"
    dst.unlink()
    return "-", "已删除"


def probe_one(dst: Path, content: str) -> tuple[str, str, bool]:
    """返回 (符号, 说明, 是否就位)。"""
    if dst.is_dir() and not dst.is_symlink():
        return "!", "实体目录挡住", False
    if dst.exists() or dst.is_symlink():
        if dst.read_text(encoding="utf-8", errors="replace") == content:
            return "=", "已安装", True
        return "~", "内容不同（重跑 add 更新）", False
    return "-", "未安装", False


def check_subagent_source(files: list[Path]) -> bool:
    """解析体检：失败或缺关键字段时警告（不阻断安装）。返回是否全部正常。"""
    ok = True
    for p in files:
        try:
            fm, _, _ = parse_subagent_file(p)
        except ValueError as exc:
            print(f"警告：subagents/{p.name} 解析失败：{exc}", file=sys.stderr)
            ok = False
            continue
        missing = [k for k in ("name", "description") if k not in fm]
        if missing:
            print(
                f"警告：subagents/{p.name} 的 frontmatter 缺 {'、'.join(missing)}，"
                "多数工具会忽略该 subagent",
                file=sys.stderr,
            )
            ok = False
        elif fm.get("name") != p.stem:
            print(
                f"警告：subagents/{p.name} 的 frontmatter name 是 {fm.get('name')}，"
                "与文件名不一致（部分工具以文件名为身份）",
                file=sys.stderr,
            )
    return ok


def run_subagents(
    command: str, targets: list[Target], names: list[str], force: bool, dry_run: bool
) -> tuple[bool, bool]:
    """转换式安装 subagents，返回 (是否有输出, 是否失败)。names 为空表示全部。"""
    files = discover_subagents()
    if names:
        stems = {p.stem for p in files}
        unknown = [n for n in names if n not in stems]
        if unknown:
            print(
                f"错误：subagents/ 下没有 {'、'.join(unknown)}"
                f"（可用：{'、'.join(sorted(stems)) or '无'}）",
                file=sys.stderr,
            )
            return True, True
        selected = [p for p in files if p.stem in names]
    else:
        selected = files
    if not selected:
        return False, False
    check_subagent_source(selected)

    failed = False
    print(f"Subagents: {REPO_SUBAGENTS}（转换式安装：真源为 Claude Code 格式，按目标转换）")
    for t in targets:
        if not _prepare_target_dir(t, command, dry_run):
            failed |= command == "status"
            continue
        for p in selected:
            try:
                fm, overrides, body = parse_subagent_file(p)
                content, warnings = convert_subagent(p.stem, fm, overrides, body, t)
            except (ValueError, OSError) as exc:
                print(f"  ! {p.stem} → {t.key}: 转换失败：{exc}")
                failed = True
                continue
            for w in warnings:
                print(f"    警告：{p.stem}: {w}", file=sys.stderr)
            dst = t.dirname / t.filename.format(name=p.stem)
            try:
                if command == "add":
                    symbol, message = write_one(dst, content, dry_run)
                elif command == "remove":
                    symbol, message = unlink_one(dst, content, force, dry_run)
                else:
                    symbol, message, ok = probe_one(dst, content)
                    failed |= not ok
            except OSError as exc:
                symbol, message = "!", f"失败：{exc}"
                failed = True
            print(f"  {symbol} {p.stem} → {short(dst)}: {message}")
    return True, failed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def resolve_targets(specs: list[str] | None, parser: argparse.ArgumentParser) -> list[Target]:
    if not specs:
        return [TARGETS["claude"], TARGETS["zcode"]]
    chosen: list[Target] = []
    for spec in " ".join(specs).replace(",", " ").split():
        if spec == "all":
            chosen.extend(t for t in TARGETS.values() if t not in chosen)
            continue
        if spec not in TARGETS:
            parser.error(
                f"未知 subagent 目标 {spec}（可用：{'、'.join(TARGETS)}、all）"
            )
        if TARGETS[spec] not in chosen:
            chosen.append(TARGETS[spec])
    return chosen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/install.py",
        description="技能逐个链接进 ~/.agents/skills（共享格式根）；subagents 以 Claude Code 标准为真源，安装时按目标工具转换格式写入。",
        epilog="不带子命令 = 一键安装全部。例：python scripts/install.py subagent rust-web-engineer",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="预览模式：只演示将做什么，不实际改动（配合 skill/subagent/remove）",
    )
    sub = parser.add_subparsers(dest="command", metavar="{skill,subagent,status,remove}")

    p_skill = sub.add_parser("skill", help="安装/修复技能链接（缺省全部技能）")
    p_skill.add_argument("names", nargs="*", help="技能名，缺省全部")
    p_skill.add_argument("-n", "--dry-run", action="store_true", help=argparse.SUPPRESS)

    p_subagent = sub.add_parser(
        "subagent", help="转换安装 subagent（缺省全部；默认目标 claude,zcode）"
    )
    p_subagent.add_argument("names", nargs="*", help="subagent 名，缺省全部")
    p_subagent.add_argument(
        "--to",
        action="append",
        default=None,
        metavar="TARGET",
        help="安装目标，可重复/逗号分隔：claude、zcode、codex、gemini、opencode、copilot 或 all",
    )
    p_subagent.add_argument("-n", "--dry-run", action="store_true", help=argparse.SUPPRESS)

    p_status = sub.add_parser("status", help="查看安装状态（有未就位项时退出码为 1）")
    p_status.add_argument(
        "kind", nargs="?", choices=("skill", "subagent"), help="只看一类，缺省两类"
    )
    p_status.add_argument(
        "--to",
        action="append",
        default=None,
        metavar="TARGET",
        help="只看这些 subagent 目标（默认 claude,zcode）",
    )

    p_remove = sub.add_parser("remove", help="卸载：只移除本脚本生成的链接/文件")
    p_remove.add_argument(
        "kind", nargs="?", choices=("skill", "subagent"), help="只卸一类，缺省两类"
    )
    p_remove.add_argument(
        "--to", action="append", default=None, metavar="TARGET", help="只卸这些 subagent 目标"
    )
    p_remove.add_argument(
        "--force", action="store_true", help="内容不一致的 subagent 文件/非本仓库链接也移除"
    )
    p_remove.add_argument("-n", "--dry-run", action="store_true", help=argparse.SUPPRESS)

    # 裸调用（不带子命令）时子解析器未运行，其默认值不会进 Namespace，这里补齐
    parser.set_defaults(names=[], to=None, kind=None, force=False, dry_run=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    command = args.command  # None = 一键安装全部
    kind = getattr(args, "kind", None)
    dry_run = args.dry_run
    force = getattr(args, "force", False)
    to = getattr(args, "to", None)
    names = list(dict.fromkeys(getattr(args, "names", []) or []))

    failed = False
    op = {"skill": "add", "subagent": "add", "status": "status", "remove": "remove"}.get(
        command, "add"
    )
    do_skills = command in (None, "skill") or (
        command in ("status", "remove") and kind in (None, "skill")
    )
    do_subagents = command in (None, "subagent") or (
        command in ("status", "remove") and kind in (None, "subagent")
    )

    if do_skills:
        if op != "status" and not dry_run:
            DEFAULT_TARGET.mkdir(parents=True, exist_ok=True)
        failed |= run_skills(
            op, names if command == "skill" else [], DEFAULT_TARGET, force, dry_run
        )

    if do_subagents:
        targets = resolve_targets(to, parser)
        subagent_names = names if command == "subagent" else []
        produced, subagents_failed = run_subagents(op, targets, subagent_names, force, dry_run)
        failed |= subagents_failed
        if not produced and not subagent_names:
            print(f"Subagents: {REPO_SUBAGENTS}（无 subagent，跳过）")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

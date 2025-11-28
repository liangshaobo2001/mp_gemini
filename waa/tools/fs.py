# waa/tools/fs.py
from __future__ import annotations

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from fnmatch import fnmatch

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


def _posix_rel(workdir: Path, p: Path) -> str:
    """
    Return POSIX-style path of p relative to workdir, or a sentinel if outside.
    """
    try:
        rel = p.resolve().relative_to(workdir.resolve())
    except Exception:
        return "__OUTSIDE_WORKDIR__"
    return rel.as_posix()


def _load_config(workdir: Path) -> Dict[str, Any]:
    cfg_path = workdir / ".waa" / "config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


class _FSToolBase(Tool):
    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.cwd: Path = env.working_dir

        # Config
        cfg = _load_config(self.cwd)
        protected_files = cfg.get("protected_files", []) or []
        writable_paths = cfg.get("writable_paths", []) or []

        # Normalize to a simple list of POSIX globs/paths (relative to workdir)
        self.protected_globs: List[str] = list(protected_files)
        self.writable_globs: List[str] = list(writable_paths)

        # Env overrides
        # Kill-switch: allow everything (use sparingly for debugging)
        self.allow_all_writes = os.environ.get("WAA_ALLOW_ALL_WRITES", "0") == "1"

        # Extra allow-list via env (comma-separated globs)
        extra_allow = os.environ.get("WAA_WRITABLE_GLOBS", "")
        if extra_allow.strip():
            self.writable_globs.extend([g.strip() for g in extra_allow.split(",") if g.strip()])

    # Security: resolve to absolute within working dir
    def _resolve(self, rel: str) -> Path:
        p = (self.cwd / rel).resolve()
        root = self.cwd.resolve()
        # Allow exactly the root dir, or any sub-path under it
        if str(p) != str(root) and not str(p).startswith(str(root) + os.sep):
            raise ValueError("Path outside working directory")
        return p

    def _is_protected(self, p: Path) -> bool:
        """
        Decide whether a path is blocked by protection rules.

        Rules:
          1) If kill-switch WAA_ALLOW_ALL_WRITES=1 -> allow.
          2) If relpath matches any allow glob (config 'writable_paths' or env WAA_WRITABLE_GLOBS) -> allow.
          3) If relpath matches any protected glob -> block.
          4) Otherwise -> allow.
        """
        if self.allow_all_writes:
            return False

        rel = _posix_rel(self.cwd, p)
        if rel == "__OUTSIDE_WORKDIR__":
            # Outside workdir -> block
            return True

        # Allow-list wins
        for pat in self.writable_globs:
            if fnmatch(rel, pat):
                return False

        # Block-list
        for pat in self.protected_globs:
            if fnmatch(rel, pat):
                return True

        return False


# ---------- fs.write ----------
class FileCreateTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.write")
        self.schema.register_argument(ToolArgument("path", "Path of file to write (relative to working dir)", True, str))
        self.schema.register_argument(ToolArgument("content", "File content to write", True, str))

    def description(self) -> str:
        return "Create or overwrite a file. Args: path:str, content:str. Creates parent dirs."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            if self._is_protected(path):
                return {"ok": False, "data": None, "error": "Attempt to modify protected file"}
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(input["content"], encoding="utf-8")
            return {"ok": True, "data": {"path": str(path)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.read ----------
class FileReadTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.read")
        self.schema.register_argument(ToolArgument("path", "Path of file to read", True, str))

    def description(self) -> str:
        return "Read a file. Args: path:str. Returns content, size_bytes, line_count."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            if not path.exists() or not path.is_file():
                return {"ok": False, "data": None, "error": "File not found"}
            content = path.read_text(encoding="utf-8")
            size = path.stat().st_size
            # Count lines: number of '\n' + possibly the last line if not ending with \n
            lines = content.count("\n") + (0 if content.endswith("\n") or content == "" else 1)
            return {
                "ok": True,
                "data": {"content": content, "size_bytes": int(size), "line_count": int(lines)},
                "error": None,
            }
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.edit ----------
class FileEditTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.edit")
        self.schema.register_argument(ToolArgument("path", "Path of file to edit", True, str))
        self.schema.register_argument(ToolArgument("old_text", "First occurrence to replace", True, str))
        self.schema.register_argument(ToolArgument("new_text", "Replacement text", True, str))

    def description(self) -> str:
        return "Edit a file by replacing the FIRST occurrence of old_text with new_text. Args: path, old_text, new_text."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            if self._is_protected(path):
                return {"ok": False, "data": None, "error": "Attempt to modify protected file"}
            if not path.exists() or not path.is_file():
                return {"ok": False, "data": None, "error": "File not found"}

            s = path.read_text(encoding="utf-8")
            old = input["old_text"]
            new = input["new_text"]
            idx = s.find(old)
            if idx < 0:
                return {"ok": False, "data": None, "error": "old_text not found"}
            new_s = s[:idx] + new + s[idx + len(old) :]
            path.write_text(new_s, encoding="utf-8")
            return {"ok": True, "data": {"path": str(path)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.delete ----------
class FileDeleteTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.delete")
        self.schema.register_argument(ToolArgument("path", "Path of file to delete", True, str))

    def description(self) -> str:
        return "Delete a file. Args: path:str."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            if self._is_protected(path):
                return {"ok": False, "data": None, "error": "Attempt to modify protected file"}
            if not path.exists() or not path.is_file():
                return {"ok": False, "data": None, "error": "File not found"}
            path.unlink()
            return {"ok": True, "data": {"path": str(path)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.mkdir ----------
class DirMakeTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.mkdir")
        self.schema.register_argument(ToolArgument("path", "Directory to create", True, str))

    def description(self) -> str:
        return "Create a directory (parents ok). Args: path:str."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            # Directory creation typically shouldn't be blocked; if you want to protect
            # whole subtrees, list them explicitly in protected_files as globs.
            path.mkdir(parents=True, exist_ok=True)
            return {"ok": True, "data": {"path": str(path)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.rmdir ----------
class DirRemoveTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.rmdir")
        self.schema.register_argument(ToolArgument("path", "Directory to remove", True, str))
        self.schema.register_argument(ToolArgument("recursive", "Remove recursively", False, bool))

    def description(self) -> str:
        return "Remove a directory. Args: path:str, recursive:bool=False."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            path = self._resolve(input["path"])
            recursive = bool(input.get("recursive", False))
            if not path.exists() or not path.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found"}
            if recursive:
                shutil.rmtree(path)
            else:
                try:
                    path.rmdir()  # only empty dir
                except OSError:
                    return {"ok": False, "data": None, "error": "Directory not empty"}
            return {"ok": True, "data": {"path": str(path)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.ls ----------
class DirListTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.ls")
        self.schema.register_argument(ToolArgument("path", "Directory to list (default '.')", False, str))

    def description(self) -> str:
        return "List directory contents. Args: path:str='.'. Returns {entries:[{name,type,size}], count:int}."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel = input.get("path", ".")
            path = self._resolve(rel)
            if not path.exists() or not path.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found"}

            entries: List[Dict[str, Any]] = []
            for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                try:
                    size = 0 if child.is_dir() else int(child.stat().st_size)
                except Exception:
                    size = 0
                entries.append(
                    {
                        "name": child.name,
                        "type": "dir" if child.is_dir() else "file",
                        "size": size,
                    }
                )
            return {"ok": True, "data": {"entries": entries, "count": len(entries)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


# ---------- fs.tree ----------
class DirTreeTool(_FSToolBase):
    def __init__(self):
        super().__init__("fs.tree")
        self.schema.register_argument(ToolArgument("path", "Directory to show as a tree", False, str))
        self.schema.register_argument(ToolArgument("max_depth", "Max depth to display", False, int))

    def description(self) -> str:
        return "Render a simple directory tree. Args: path:str='.', max_depth:int=3. Returns {tree:str}."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel = input.get("path", ".")
            max_depth = int(input.get("max_depth", 3))
            base = self._resolve(rel)
            if not base.exists() or not base.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found"}

            lines: List[str] = [base.name]

            def walk(d: Path, prefix: str = "", depth: int = 0):
                if depth >= max_depth:
                    return
                children = sorted(list(d.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
                for i, child in enumerate(children):
                    is_last = i == len(children) - 1
                    connector = "└── " if is_last else "├── "
                    lines.append(prefix + connector + child.name)
                    if child.is_dir():
                        new_prefix = prefix + ("    " if is_last else "│   ")
                        walk(child, new_prefix, depth + 1)

            walk(base)
            # ✅ Return list, not string
            return {"ok": True, "data": {"tree": lines}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}

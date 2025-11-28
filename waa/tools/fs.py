import shutil
import os
from pathlib import Path
from typing import Dict, Any, List

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


class FileCreateTool(Tool):
    def __init__(self):
        super().__init__("fs.write")
        self.schema.register_argument(ToolArgument("path", "Relative path to the file", True, str))
        self.schema.register_argument(ToolArgument("content", "Content to write to the file", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.write` - Create or overwrite a file with the given content. Automatically creates parent directories."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            content = input["content"]
            
            # Security Checks
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()
            
            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": f"Access denied: Path {rel_path} is outside working directory."}
            
            protected = self.env.get_config_value("protected_files", [])
            if rel_path in protected:
                return {"ok": False, "data": None, "error": f"Access denied: {rel_path} is a protected file."}

            # Operation
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {"ok": True, "data": {"path": rel_path, "size": len(content)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class FileDeleteTool(Tool):
    def __init__(self):
        super().__init__("fs.delete")
        self.schema.register_argument(ToolArgument("path", "Relative path to the file", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.delete` - Delete a file permanently."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied: Path outside working directory."}

            protected = self.env.get_config_value("protected_files", [])
            if rel_path in protected:
                return {"ok": False, "data": None, "error": f"Access denied: {rel_path} is a protected file."}

            if not full_path.exists() or not full_path.is_file():
                return {"ok": False, "data": None, "error": f"File not found: {rel_path}"}

            os.remove(full_path)
            return {"ok": True, "data": {"message": f"Deleted {rel_path}"}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class FileReadTool(Tool):
    def __init__(self):
        super().__init__("fs.read")
        self.schema.register_argument(ToolArgument("path", "Relative path to the file", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.read` - Read the content of a file."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied: Path outside working directory."}
            
            if not full_path.exists():
                return {"ok": False, "data": None, "error": f"File not found: {rel_path}"}

            content = full_path.read_text(encoding='utf-8')
            return {"ok": True, "data": {"content": content, "size": len(content)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class FileEditTool(Tool):
    def __init__(self):
        super().__init__("fs.edit")
        self.schema.register_argument(ToolArgument("path", "Relative path", True, str))
        self.schema.register_argument(ToolArgument("old_text", "Exact text segment to replace", True, str))
        self.schema.register_argument(ToolArgument("new_text", "New text to insert", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.edit` - Replace the first occurrence of `old_text` with `new_text` in a file."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            old_text = input["old_text"]
            new_text = input["new_text"]

            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()
            
            # Security Checks
            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied: Path outside working directory."}
            
            protected = self.env.get_config_value("protected_files", [])
            if rel_path in protected:
                return {"ok": False, "data": None, "error": f"Access denied: {rel_path} is a protected file."}

            if not full_path.exists():
                return {"ok": False, "data": None, "error": f"File not found: {rel_path}"}

            content = full_path.read_text(encoding='utf-8')
            if old_text not in content:
                return {"ok": False, "data": None, "error": "old_text not found in file."}

            new_content = content.replace(old_text, new_text, 1) # Replace only first occurrence
            full_path.write_text(new_content, encoding='utf-8')

            return {"ok": True, "data": {"message": f"Successfully edited {rel_path}"}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class DirectoryCreateTool(Tool):
    def __init__(self):
        super().__init__("fs.mkdir")
        self.schema.register_argument(ToolArgument("path", "Directory path", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.mkdir` - Create a new directory (and parent directories if needed)."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied."}

            full_path.mkdir(parents=True, exist_ok=True)
            return {"ok": True, "data": {"message": f"Created directory {rel_path}"}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class DirectoryDeleteTool(Tool):
    def __init__(self):
        super().__init__("fs.rmdir")
        self.schema.register_argument(ToolArgument("path", "Directory path", True, str))
        self.schema.register_argument(ToolArgument("recursive", "Delete recursively?", False, bool))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.rmdir` - Remove a directory. Use recursive=True to delete non-empty directories."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            recursive = input.get("recursive", False)
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied."}

            if not full_path.exists() or not full_path.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found."}

            if recursive:
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()
            
            return {"ok": True, "data": {"message": f"Removed directory {rel_path}"}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class DirectoryListTool(Tool):
    def __init__(self):
        super().__init__("fs.ls")
        self.schema.register_argument(ToolArgument("path", "Directory path", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.ls` - List all files and folders in a directory."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied."}

            if not full_path.exists() or not full_path.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found."}

            entries = []
            for item in full_path.iterdir():
                entries.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })

            return {"ok": True, "data": {"entries": entries}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}

class DirectoryTreeTool(Tool):
    def __init__(self):
        super().__init__("fs.tree")
        self.schema.register_argument(ToolArgument("path", "Directory path", True, str))
        self.schema.register_argument(ToolArgument("max_depth", "Max recursion depth", False, int))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`fs.tree` - List directory structure recursively."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rel_path = input["path"]
            max_depth = input.get("max_depth", 2)
            working_dir = self.env.get_working_dir()
            full_path = (working_dir / rel_path).resolve()

            if not str(full_path).startswith(str(working_dir.resolve())):
                return {"ok": False, "data": None, "error": "Access denied."}
            
            if not full_path.exists() or not full_path.is_dir():
                return {"ok": False, "data": None, "error": "Directory not found."}

            tree_lines = []
            
            def build_tree(current_path, prefix="", current_depth=0):
                if current_depth > max_depth:
                    return
                
                # Sort for deterministic output
                try:
                    items = sorted([p for p in current_path.iterdir() if not p.name.startswith('.')])
                except Exception:
                    return # Permission denied or other error

                for i, item in enumerate(items):
                    is_last = (i == len(items) - 1)
                    connector = "└── " if is_last else "├── "
                    tree_lines.append(f"{prefix}{connector}{item.name}")
                    
                    if item.is_dir():
                        extension = "    " if is_last else "│   "
                        build_tree(item, prefix + extension, current_depth + 1)

            build_tree(full_path)
            
            return {"ok": True, "data": {"tree": tree_lines}, "error": None} 

        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}
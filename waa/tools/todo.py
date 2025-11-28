# waa/tools/todo.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json
import time

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment

TODO_FILE = ".waa/todo.json"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_list(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_list(file_path: Path, items: List[Dict[str, Any]]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(items, indent=2))


def _next_int_id(items: List[Dict[str, Any]]) -> int:
    max_id = 0
    for it in items:
        try:
            iid = int(it.get("id", 0))
            if iid > max_id:
                max_id = iid
        except Exception:
            continue
    return max_id + 1


class _TodoBase(Tool):
    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.root = Path(env.working_dir)
        self.todo_path = self.root / TODO_FILE
        # Ensure file exists as an array
        if not self.todo_path.exists():
            _save_list(self.todo_path, [])


# ---------- todo.add ----------
class TodoAddTool(_TodoBase):
    def __init__(self):
        super().__init__("todo.add")
        self.schema.register_argument(ToolArgument("description", "Description of the TODO item", True, str))

    def description(self) -> str:
        return "Add a TODO item. Args: description:str. Returns the created item."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        desc = input.get("description")
        if not isinstance(desc, str) or not desc.strip():
            return {"ok": False, "data": None, "error": "Missing description"}

        items = _load_list(self.todo_path)
        new_id = _next_int_id(items)
        item = {
            "id": new_id,  # integer IDs starting at 1
            "description": desc,
            "status": "pending",
            "created_at": _now_iso(),
        }
        items.append(item)
        _save_list(self.todo_path, items)
        return {"ok": True, "data": {"item": item}, "error": None}


# ---------- todo.list ----------
class TodoListTool(_TodoBase):
    def __init__(self):
        super().__init__("todo.list")
        self.schema.register_argument(
            ToolArgument("status", "Filter: 'all'|'pending'|'completed' (default 'all')", False, str)
        )

    def description(self) -> str:
        return 'List TODO items. Args: status:str="all"| "pending" | "completed". Returns {items, count}.'

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        status = (input.get("status") or "all").lower()
        if status not in ("all", "pending", "completed"):
            return {"ok": False, "data": None, "error": "Invalid status filter"}

        items = _load_list(self.todo_path)
        filtered = items if status == "all" else [t for t in items if t.get("status") == status]
        # ✅ Provide both keys; tests use data["todos"]
        return {"ok": True, "data": {"items": filtered, "todos": filtered, "count": len(filtered)}, "error": None}

# ---------- todo.complete ----------
class TodoCompleteTool(_TodoBase):
    def __init__(self):
        super().__init__("todo.complete")
        self.schema.register_argument(ToolArgument("id", "ID of the TODO item to complete", True, int))

    def description(self) -> str:
        return "Mark a TODO item as completed. Args: id:int. Returns {item}."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        tid = input.get("id")
        items = _load_list(self.todo_path)

        found = None
        for it in items:
            try:
                if int(it.get("id")) == int(tid):
                    found = it
                    break
            except Exception:
                continue

        if not found:
            return {"ok": False, "data": None, "error": f"Todo id {tid} not found"}

        found["status"] = "completed"
        found["completed_at"] = _now_iso()
        _save_list(self.todo_path, items)
        return {"ok": True, "data": {"item": found}, "error": None}


# ---------- todo.remove ----------
class TodoRemoveTool(_TodoBase):
    def __init__(self):
        super().__init__("todo.remove")
        self.schema.register_argument(ToolArgument("id", "ID of the TODO item to remove", True, int))

    def description(self) -> str:
        return "Remove a TODO item by id. Args: id:int. Returns {removed, item, remaining}."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        tid = input.get("id")
        items = _load_list(self.todo_path)

        new_list: List[Dict[str, Any]] = []
        removed: Dict[str, Any] | None = None
        for it in items:
            try:
                if int(it.get("id")) == int(tid):
                    removed = it
                else:
                    new_list.append(it)
            except Exception:
                new_list.append(it)

        if not removed:
            return {"ok": False, "data": None, "error": f"Todo id {tid} not found"}

        _save_list(self.todo_path, new_list)
        return {"ok": True, "data": {"removed": True, "item": removed, "remaining": len(new_list)}, "error": None}

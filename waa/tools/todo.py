import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


class TodoAddTool(Tool):
    def __init__(self):
        super().__init__("todo.add")
        self.schema.register_argument(ToolArgument("description", "Description of the task", True, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.todo_file = env.get_working_dir() / ".waa" / "todo.json"

    def description(self) -> str:
        return "`todo.add` - Add a new task to the TODO list."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            description = input["description"]
            
            todos = []
            if self.todo_file.exists():
                with open(self.todo_file, 'r') as f:
                    todos = json.load(f)
            
            new_id = 1
            if todos:
                new_id = max(t["id"] for t in todos) + 1
            
            new_task = {
                "id": new_id,
                "description": description,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            todos.append(new_task)
            
            with open(self.todo_file, 'w') as f:
                json.dump(todos, f, indent=4)
                
            return {"ok": True, "data": new_task, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class TodoListTool(Tool):
    def __init__(self):
        super().__init__("todo.list")
        self.schema.register_argument(ToolArgument("status", "Filter by status: 'pending', 'completed', or 'all'", False, str))

    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.todo_file = env.get_working_dir() / ".waa" / "todo.json"

    def description(self) -> str:
        return "`todo.list` - List tasks. Optionally filter by status ('pending', 'completed')."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            status_filter = input.get("status", "all")
            if status_filter not in ["pending", "completed", "all"]:
                return {"ok": False, "data": None, "error": "Invalid status filter. Use 'pending', 'completed', or 'all'."}

            if not self.todo_file.exists():
                return {"ok": True, "data": {"todos": [], "count": 0}, "error": None}
                
            with open(self.todo_file, 'r') as f:
                todos = json.load(f)
            
            filtered = todos
            if status_filter != "all":
                filtered = [t for t in todos if t["status"] == status_filter]
                
            return {"ok": True, "data": {"todos": filtered, "count": len(filtered)}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class TodoCompleteTool(Tool):
    def __init__(self):
        super().__init__("todo.complete")
        self.schema.register_argument(ToolArgument("id", "ID of the task to complete", True, int))

    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.todo_file = env.get_working_dir() / ".waa" / "todo.json"

    def description(self) -> str:
        return "`todo.complete` - Mark a task as completed."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_id = input["id"]
            
            if not self.todo_file.exists():
                return {"ok": False, "data": None, "error": "No TODO list found."}
                
            with open(self.todo_file, 'r') as f:
                todos = json.load(f)
            
            found = False
            for task in todos:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    task["completed_at"] = datetime.now().isoformat()
                    found = True
                    break
            
            if not found:
                return {"ok": False, "data": None, "error": f"Task with ID {task_id} not found."}
                
            with open(self.todo_file, 'w') as f:
                json.dump(todos, f, indent=4)
                
            return {"ok": True, "data": {"message": f"Task {task_id} completed."}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}


class TodoRemoveTool(Tool):
    def __init__(self):
        super().__init__("todo.remove")
        self.schema.register_argument(ToolArgument("id", "ID of the task to remove", True, int))

    def initialize(self, env: AgentEnvironment):
        self.env = env
        self.todo_file = env.get_working_dir() / ".waa" / "todo.json"

    def description(self) -> str:
        return "`todo.remove` - Remove a task from the list."

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_id = input["id"]
            
            if not self.todo_file.exists():
                return {"ok": False, "data": None, "error": "No TODO list found."}
                
            with open(self.todo_file, 'r') as f:
                todos = json.load(f)
            
            initial_len = len(todos)
            todos = [t for t in todos if t["id"] != task_id]
            
            if len(todos) == initial_len:
                return {"ok": False, "data": None, "error": f"Task with ID {task_id} not found."}
                
            with open(self.todo_file, 'w') as f:
                json.dump(todos, f, indent=4)
                
            return {"ok": True, "data": {"message": f"Task {task_id} removed."}, "error": None}
        except Exception as e:
            return {"ok": False, "data": None, "error": str(e)}
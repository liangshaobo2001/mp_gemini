import json
import os
from pathlib import Path
from typing import Dict, Any, List

from ..tool import Tool, ToolArgument, ToolSchema
from ..env import AgentEnvironment

class ComponentRegisterTool(Tool):
    def __init__(self):
        super().__init__("component.register")
        self.schema.register_argument(ToolArgument("name", "Name of the component (e.g., 'navbar')", True, str))
        self.schema.register_argument(ToolArgument("path", "Path to the component file (relative to components/)", True, str))
        self.schema.register_argument(ToolArgument("description", "Description of what the component does", False, str))
        self.env = None

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "Register a reusable UI component. Usage: component.register(name='navbar', path='navbar.html', description='Main navigation bar')"

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        name = input["name"]
        path = input["path"]
        description = input.get("description", "")

        components_dir = self.env.working_dir / "components"
        if not components_dir.exists():
            components_dir.mkdir(parents=True, exist_ok=True)

        registry_path = self.env.working_dir / ".waa" / "components.json"
        
        registry = {}
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
            except json.JSONDecodeError:
                pass

        registry[name] = {
            "path": path,
            "description": description
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        return {"ok": True, "data": f"Component '{name}' registered successfully."}

class ComponentListTool(Tool):
    def __init__(self):
        super().__init__("component.list")
        self.env = None

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "List all registered reusable components. Usage: component.list()"

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        registry_path = self.env.working_dir / ".waa" / "components.json"
        
        if not registry_path.exists():
            return {"ok": True, "data": "No components registered."}

        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            return {"ok": True, "data": registry}
        except json.JSONDecodeError:
            return {"ok": False, "error": "Failed to parse component registry."}

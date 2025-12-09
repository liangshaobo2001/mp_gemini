import json
import os
from pathlib import Path
from typing import Dict, Any, List

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment

class PageRegisterTool(Tool):
    def __init__(self):
        super().__init__("page.register")
        self.schema.register_argument(ToolArgument("name", "Name of the page file (e.g., 'index.html')", True, str))
        self.schema.register_argument(ToolArgument("route", "Route path (e.g., '/' or '/about')", False, str))
        self.schema.register_argument(ToolArgument("title", "Page title", False, str))
        self.schema.register_argument(ToolArgument("components", "List of components used in this page", False, list))
        self.env = None

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "Register a new page in the project. Usage: page.register(name='about.html', route='/about', title='About Us', components=['navbar', 'footer'])"

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        name = input["name"]
        route = input.get("route", "/" + name.replace(".html", ""))
        if name == "index.html":
            route = "/"
        title = input.get("title", name)
        components = input.get("components", [])

        registry_path = self.env.working_dir / ".waa" / "pages.json"
        
        registry = {}
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
            except json.JSONDecodeError:
                pass

        registry[name] = {
            "route": route,
            "title": title,
            "components": components
        }

        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        return {"ok": True, "data": f"Page '{name}' registered successfully."}

class PageListTool(Tool):
    def __init__(self):
        super().__init__("page.list")
        self.env = None

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "List all registered pages. Usage: page.list()"

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        registry_path = self.env.working_dir / ".waa" / "pages.json"
        
        if not registry_path.exists():
            return {"ok": True, "data": {}}

        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            return {"ok": True, "data": registry}
        except json.JSONDecodeError:
            return {"ok": False, "error": "Failed to parse page registry."}

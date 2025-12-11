from typing import Dict, Any, List
from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment
from ..ui_builder import UIBuilder

class UIUpdateConfigTool(Tool):
    def __init__(self):
        super().__init__("ui.update_config")
        self.schema.register_argument(ToolArgument("inputs", "List of input definitions. Each input must have 'type' and 'id'.", False, list))
        self.schema.register_argument(ToolArgument("title", "Title of the web interface", False, str))
        self.schema.register_argument(ToolArgument("style", "CSS styles: background_color, text_color, primary_color, font_family", False, dict))

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`ui.update_config` - Update the UI configuration to add/remove inputs or change styles. The config defines what inputs are available in the web interface."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ui_builder = UIBuilder(self.env.working_dir)
            
            # Handle case where agent wraps everything in "config"
            data = args.get("config", args)

            if "inputs" in data:
                ui_builder.config["inputs"] = data["inputs"]
            
            if "title" in data:
                ui_builder.config["title"] = data["title"]

            if "style" in data:
                current_style = ui_builder.config.get("style", {})
                current_style.update(data["style"])
                ui_builder.config["style"] = current_style
                
            ui_builder._save_config()
            ui_builder.generate_ui()
            
            return {
                "success": True, 
                "message": "UI configuration updated and interface rebuilt.",
                "config": ui_builder.config
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class UIRebuildTool(Tool):
    def __init__(self):
        super().__init__("ui.rebuild")

    def initialize(self, env: AgentEnvironment):
        self.env = env

    def description(self) -> str:
        return "`ui.rebuild` - Rebuild the UI files (HTML/CSS/JS) based on the current configuration."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ui_builder = UIBuilder(self.env.working_dir)
            ui_builder.generate_ui()
            return {"success": True, "message": "UI rebuilt successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

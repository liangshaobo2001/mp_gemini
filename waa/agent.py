import os
import re
import json
import traceback
from typing import Dict, Any, List, Optional
from pathlib import Path

from .llm import LanguageModel, GeminiLanguageModel, MockLanguageModel
from .tool import ToolRegistry, Tool
from .history import HistoryEntry, SystemPrompt, UserInstruction, LLMResponse, ToolCallResult
from .logger import Logger
from .env import AgentEnvironment

# Import Tools
from .tools.server import NPMInitTool, NPMStartTool, NPMStopTool, NPMStatusTool, NPMLogsTool
from .tools.fs import FileCreateTool, FileDeleteTool, FileReadTool, FileEditTool, DirectoryCreateTool, DirectoryDeleteTool, DirectoryListTool, DirectoryTreeTool
from .tools.todo import TodoAddTool, TodoListTool, TodoCompleteTool, TodoRemoveTool
from .tools.playwright import PlaywrightInitTool, PlaywrightRunTool
from .tools.supertest import SupertestInitTool, SupertestRunTool

class Agent:
    working_dir: Path
    llm: LanguageModel
    tool_registry: ToolRegistry
    config: Dict[str, Any]
    max_turns: int
    history: List[HistoryEntry]
    logger: Logger
    env: AgentEnvironment
    debug: bool

    def __init__(self, working_dir: Path, debug: bool = False):
        self.working_dir = working_dir
        self.config = None
        self.debug = debug
        self.llm = None
        self.tool_registry = None
        self.max_turns = 0
        self.history = []
        self.logger = None
        self.env = None

    def initialize_environment(self):
        config_path = self.working_dir / ".waa" / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.env = AgentEnvironment(self.working_dir, self.config)
        self.max_turns = self.env.get_config_value("max_turns", 50)

    def initialize_llm(self):
        llm_type = self.config.get("llm_type", "mock")
        if llm_type == "gemini":
            model_name = self.config.get("model", "gemini-1.5-flash") 
            api_key = self.config.get("api_key", os.getenv("GEMINI_API_KEY"))
            self.llm = GeminiLanguageModel(model_name=model_name, api_key=api_key)
        elif llm_type == "mock":
            responses = self.config.get("mock_responses")
            self.llm = MockLanguageModel(responses=responses)
        else:
            raise ValueError(f"Unknown llm_type: {llm_type}. Use 'gemini' or 'mock'.")

    def initialize_logger(self):
        log_path = self.working_dir / ".waa" / "agent.log"
        # In a real run, we might want to fail if log exists to ensure clean state
        # But for development, we can just append or overwrite.
        self.logger = Logger(log_path, self.debug)
        self.logger.log("Agent initialization started")
        self.logger.log(f"Working directory: {self.working_dir}")

    def initialize_tool_registry(self):
        self.tool_registry = ToolRegistry()
        
        # Instantiate all available tools
        all_tools = [
            NPMInitTool(), NPMStartTool(), NPMStopTool(), NPMStatusTool(), NPMLogsTool(),
            FileCreateTool(), FileDeleteTool(), FileReadTool(), FileEditTool(), 
            DirectoryCreateTool(), DirectoryDeleteTool(), DirectoryListTool(), DirectoryTreeTool(),
            TodoAddTool(), TodoListTool(), TodoCompleteTool(), TodoRemoveTool(),
            PlaywrightInitTool(), PlaywrightRunTool(),
            SupertestInitTool(), SupertestRunTool()
        ]

        allowed_tools = self.env.get_config_value("allowed_tools", None)
        
        for tool in all_tools:
            # If allowed_tools is None (default), register everything.
            # Otherwise, check if tool name is in the allowed list.
            if allowed_tools is None or tool.name in allowed_tools:
                tool.initialize(self.env)
                self.tool_registry.register_tool(tool)

    def load_system_prompt(self):
        tools_desc = "\n".join([f"- {t.name}: {t.description()}" for t in self.tool_registry.list_tools()])
        
        prompt = f"""You are WAA (Web-App Agent), an expert full-stack developer.
Your goal is to build web applications based on user instructions.

AVAILABLE TOOLS:
{tools_desc}

PROTOCOL:
1. You must think step-by-step.
2. To use a tool, you MUST use this format:
   <tool_call>{{"tool": "tool_name", "arguments": {{"arg": "value"}}}}</tool_call>
3. Only one tool call per turn. Wait for the result before proceeding.
4. When the task is complete, output:
   <terminate>

RULES:
- Always check if files exist (fs.ls, fs.read) before editing.
- Create a 'todo' list (todo.add) at the start to track your plan.
- Use 'npm.init' to setup Node.js projects.
- Use 'fs.write' to create HTML/CSS/JS files.
- Always run tests (playwright.run or supertest.run) to verify your work.
"""
        system_entry = SystemPrompt(prompt)
        self.history.append(system_entry)
        self.logger.log_system_prompt(prompt)

    def load_instruction(self):
        instruction_path = self.working_dir / ".waa" / "instruction.md"
        if not instruction_path.exists():
            raise FileNotFoundError("instruction.md not found")
            
        content = instruction_path.read_text(encoding='utf-8')
        user_entry = UserInstruction(content)
        self.history.append(user_entry)
        self.logger.log_user_instruction(content)

    def initialize(self):
        self.initialize_environment()
        self.initialize_llm()
        self.initialize_logger()
        self.initialize_tool_registry()

        self.load_system_prompt()
        self.load_instruction()

    def query_llm(self, turn: int):
        # Convert history to format expected by LLM
        messages = [{"role": h.role, "content": h.get_content()} for h in self.history]
        
        self.logger.log_llm_query(turn, len(messages))
        response_text = self.llm.generate(messages)
        
        response_entry = LLMResponse(response_text)
        self.history.append(response_entry)
        self.logger.log_llm_response(turn, response_text)
        
        return response_entry

    def execute_tool(self, tool_call_text: str):
        try:
            # Extract JSON from <tool_call>... </tool_call>
            match = re.search(r'<tool_call>(.*?)</tool_call>', tool_call_text, re.DOTALL)
            if not match:
                return

            json_str = match.group(1).strip()
            call_data = json.loads(json_str)
            
            tool_name = call_data.get("tool")
            args = call_data.get("arguments", {})

            self.logger.log_tool_call(tool_name, args)

            try:
                tool = self.tool_registry.get_tool(tool_name)
            except KeyError:
                 result = {"ok": False, "error": f"Tool '{tool_name}' not found."}
                 self.logger.log_tool_result(tool_name, None, result["error"])
                 result_entry = ToolCallResult(tool_name, args, None, result["error"])
                 self.history.append(result_entry)
                 return

            # Validate and Execute
            if tool.schema.validate(args):
                result = tool.execute(args)
            else:
                result = {"ok": False, "error": "Invalid arguments"}

            # Log and Append to History
            self.logger.log_tool_result(tool_name, result.get("data"), result.get("error"))
            
            result_entry = ToolCallResult(tool_name, args, result.get("data"), result.get("error"))
            self.history.append(result_entry)

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}\n{traceback.format_exc()}"
            self.logger.log_error(error_msg)
            result_entry = ToolCallResult("unknown", {}, None, error_msg)
            self.history.append(result_entry)

    def run(self):
        self.initialize()
        
        for turn in range(1, self.max_turns + 1):
            # 1. Query
            response_entry = self.query_llm(turn)
            
            # 2. Check Termination
            if response_entry.is_termination():
                self.logger.log_termination(turn, "LLM requested termination")
                break

            # 3. Check and Execute Tool
            if response_entry.is_tool_call():
                self.execute_tool(response_entry.response)

        else:
            self.logger.log_termination(self.max_turns, "Max turns reached")
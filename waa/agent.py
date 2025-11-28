import os
import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .llm import LanguageModel, create_language_model
from .tool import ToolRegistry
from .history import HistoryEntry, SystemPrompt, UserInstruction, LLMResponse, ToolCallResult
from .logger import Logger
from .env import AgentEnvironment
from .llm import MockLanguageModel

# Tools (server/testing provided; fs/todo implemented in Part 2)
from .tools import server as _server
from .tools import supertest as _supertest
from .tools import playwright as _playwright
from .tools import fs as _fs
from .tools import todo as _todo


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

    # ---------- Initialization helpers ----------

    def initialize_environment(self):
        config_path = self.working_dir / ".waa" / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            self.config = json.load(f)

        self.env = AgentEnvironment(self.working_dir, self.config)
        self.max_turns = self.env.get_config_value("max_turns", 50)

    def initialize_llm(self):
        # prefer explicit mock when requested
        llm_type = (self.config or {}).get("llm_type", "mock").lower()

        if llm_type == "mock":
            # 1) config-provided responses
            cfg_responses = self.config.get("mock_responses") if isinstance(self.config, dict) else None
            if isinstance(cfg_responses, list) and all(isinstance(x, str) for x in cfg_responses) and cfg_responses:
                self.llm = MockLanguageModel(responses=cfg_responses)
                return

            # 2) .waa/mock_responses.json
            mr_json = self.working_dir / ".waa" / "mock_responses.json"
            if mr_json.exists():
                try:
                    import json as _json
                    data = _json.loads(mr_json.read_text())
                    if isinstance(data, list) and all(isinstance(x, str) for x in data) and data:
                        self.llm = MockLanguageModel(responses=data)
                        return
                except Exception:
                    pass  # fall through to other sources

            # 3) .waa/mock_responses.txt (one response per line)
            mr_txt = self.working_dir / ".waa" / "mock_responses.txt"
            if mr_txt.exists():
                try:
                    lines = [ln.rstrip("\n") for ln in mr_txt.read_text().splitlines()]
                    lines = [ln for ln in lines if ln.strip()]
                    if lines:
                        self.llm = MockLanguageModel(responses=lines)
                        return
                except Exception:
                    pass

            # default mock if none provided
            self.llm = MockLanguageModel()
            return

        # Non-mock: use the factory (handles Gemini etc.)
        self.llm = create_language_model(self.config)

        # print the name of LM being used.
        if self.logger:
            self.logger.log_debug(
                f"LLM selected: {type(self.llm).__name__} "
                f"model={getattr(self.llm, 'model', None) or getattr(self.llm, 'model_name', None)} "
                f"llm_type={(self.config or {}).get('llm_type')}"
            )

        # optional hard guard so we never silently fall back to mock when llm_type != "mock"
        if llm_type != "mock" and type(self.llm).__name__ == "MockLanguageModel":
            raise RuntimeError("Expected a real LLM, but MockLanguageModel was instantiated.")


    def initialize_logger(self):
        log_path = self.working_dir / ".waa" / "agent.log"
        # if log_path.exists():
        #     raise RuntimeError(
        #         f"Log file already exists: {log_path}. Remove it to start a new run."
        #     )

        self.logger = Logger(log_path, self.debug)
        self.logger.log("Agent initialization started")
        self.logger.log(f"Working directory: {self.working_dir}")
        self.logger.log(f"Debug mode: {self.debug}")
        self.logger.log(f"Max turns: {self.max_turns}")

    def initialize_tool_registry(self):
        self.tool_registry = ToolRegistry()

        # Build all tools first (but don't register yet)
        all_tool_classes = [
            # Server tools
            _server.NPMInitTool,
            _server.NPMStartTool,
            _server.NPMStopTool,
            _server.NPMStatusTool,
            _server.NPMLogsTool,
            # Testing tools
            _supertest.SupertestInitTool,
            _supertest.SupertestRunTool,
            _playwright.PlaywrightInitTool,
            _playwright.PlaywrightRunTool,
            # FS tools (Part 2)
            _fs.FileCreateTool,
            _fs.FileReadTool,
            _fs.FileEditTool,
            _fs.FileDeleteTool,
            _fs.DirMakeTool,
            _fs.DirRemoveTool,
            _fs.DirListTool,
            getattr(_fs, "DirTreeTool", None),  # optional
            # TODO tools (Part 2)
            _todo.TodoAddTool,
            _todo.TodoListTool,
            _todo.TodoCompleteTool,
            _todo.TodoRemoveTool,
        ]

        tools_by_name = {}
        for ToolCls in all_tool_classes:
            if ToolCls is None:
                continue
            t = ToolCls()
            t.initialize(self.env)
            tools_by_name[t.name] = t

        # Only register tools that are allowed by config
        allowed = self.env.get_config_value("allowed_tools", None)
        if isinstance(allowed, list) and allowed:
            for name in allowed:
                if name in tools_by_name:
                    self.tool_registry.register_tool(tools_by_name[name])
        else:
            # If no allowlist specified, register all
            for t in tools_by_name.values():
                self.tool_registry.register_tool(t)


    # ---------- System/User context ----------

    def _build_system_prompt_text(self) -> str:
        tools_desc = "\n".join(
            [f"- {t.name}: {t.description()}" for t in self.tool_registry.list_tools()]
        )
        return (
            "You are WAA, a deterministic web-app coding agent.\n"
            "Protocols:\n"
            '<tool_call>{"tool":"TOOL_NAME","arguments":{"arg1":"val"}}</tool_call>\n'
            "<terminate>\n"
            "Strategy: (1) Read instruction; (2) Initialize project; (3) Create/edit files; "
            "(4) Run tests; (5) Iterate on failures; (6) Terminate when done.\n"
            "Constraints: stay within working directory; never modify protected_files; "
            "make minimal, explicit edits; include filenames in actions.\n\n"
            "Available tools:\n"
            f"{tools_desc}\n"
        )

    def load_system_prompt(self):
        text = self._build_system_prompt_text()
        self.history.append(SystemPrompt(text))
        if self.logger:
            self.logger.log_system_prompt(text)

    def load_instruction(self):
        instr_path = self.working_dir / ".waa" / "instruction.md"
        if not instr_path.exists():
            raise FileNotFoundError(f"Instruction not found: {instr_path}")
        content = instr_path.read_text()
        self.history.append(UserInstruction(content))
        if self.logger:
            self.logger.log_user_instruction(content)

    # ---------- Loop plumbing ----------

    def initialize(self):
        self.initialize_environment()
        self.initialize_llm()
        self.initialize_logger()
        self.initialize_tool_registry()
        self.load_system_prompt()
        self.load_instruction()

    def _history_to_messages(self) -> List[Dict[str, Any]]:
        msgs: List[Dict[str, Any]] = []
        for h in self.history:
            d = h.to_json()
            msgs.append({"role": d["role"], "content": d["content"]})
        return msgs

    def query_llm(self, turn: int) -> LLMResponse:
        messages = self._history_to_messages()
        if self.logger:
            self.logger.log_llm_query(turn, messages)
        resp_text = self.llm.generate(messages)


        if self.logger:
            self.logger.log_debug(f"Raw LLM text: {resp_text!r}")


        resp = LLMResponse(resp_text)
        self.history.append(resp)
        if self.logger:
            self.logger.log_llm_response(turn, resp_text)
        return resp

    def _parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        m = re.search(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL)
        if not m:
            return None
        inner = m.group(1).strip()
        try:
            obj = json.loads(inner)
            if not isinstance(obj, dict) or "tool" not in obj or "arguments" not in obj:
                raise ValueError("Malformed tool_call JSON")
            return obj
        except Exception as e:
            self.history.append(
                ToolCallResult("INVALID", {}, None, f"Invalid tool_call JSON: {e}")
            )
            if self.logger:
                self.logger.log_error(f"Invalid tool_call JSON: {e}")
            return None

    def execute_tool(self, tool_call: Dict[str, Any]):
        tool_name = tool_call.get("tool")
        arguments = tool_call.get("arguments", {})

        # Unknown tool
        try:
            tool = self.tool_registry.get_tool(tool_name)
        except KeyError:
            res = ToolCallResult(tool_name or "UNKNOWN", arguments, None, f"Unknown tool: {tool_name}")
            self.history.append(res)
            if self.logger:
                self.logger.log_tool_result(tool_name or "UNKNOWN", {
                    "arguments": arguments,
                    "result": None,
                    "error": res.error,
                })
            return

        # Validate arguments
        try:
            tool.schema.validate(arguments)
        except Exception as e:
            res = ToolCallResult(tool_name, arguments, None, f"Argument validation failed: {e}")
            self.history.append(res)
            if self.logger:
                self.logger.log_tool_result(tool_name, {
                    "arguments": arguments,
                    "result": None,
                    "error": res.error,
                })
            return

        # Execute
        try:
            result = tool.execute(arguments)
            error = None if result.get("ok") else (result.get("error") or "Unknown tool error")
        except Exception as e:
            result = {"ok": False, "data": None, "error": str(e)}
            error = str(e)

        res = ToolCallResult(tool_name, arguments, result, error)
        self.history.append(res)
        if self.logger:
            self.logger.log_tool_result(tool_name, {
                "arguments": arguments,
                "result": result,
                "error": error,
            })

    # def run(self):
    #     # 1) initialize
    #     self.initialize()

    #     # 2) agentic loop
    #     for turn in range(1, self.max_turns + 1):
    #         resp = self.query_llm(turn)

    #         if resp.is_termination():
    #             if self.logger:
    #                 self.logger.log_termination(turn, "LLM requested termination")
    #             break

    #         tool_call = self._parse_tool_call(resp.response)
    #         if tool_call:
    #             if self.logger:
    #                 self.logger.log_tool_call(tool_call.get("tool"), tool_call.get("arguments", {}))
    #             self.execute_tool(tool_call)
    #             continue

    #         if self.logger and resp.is_message():
    #             self.logger.log_debug(f"Assistant message (turn {turn}): {resp.response}")
    #     else:
    #         if self.logger:
    #             self.logger.log_termination(self.max_turns, "Max turns reached without termination")
    def run(self):
        # 1) initialize
        self.initialize()

        # 2) agentic loop
        for turn in range(1, self.max_turns + 1):
            resp = self.query_llm(turn)

            # Execute every <tool_call> found in this single response
            for m in re.finditer(r"<tool_call>(.*?)</tool_call>", resp.response, flags=re.DOTALL):
                try:
                    obj = json.loads(m.group(1).strip())
                    if isinstance(obj, dict) and "tool" in obj and "arguments" in obj:
                        if self.logger:
                            self.logger.log_tool_call(obj.get("tool"), obj.get("arguments", {}))
                        self.execute_tool(obj)
                except Exception as e:
                    self.history.append(ToolCallResult("INVALID", {}, None, f"Invalid tool_call JSON: {e}"))
                    if self.logger:
                        self.logger.log_error(f"Invalid tool_call JSON: {e}")

            # Only terminate if the *entire* message is exactly "<terminate>"
            if resp.response.strip() == "<terminate>":
                if self.logger:
                    self.logger.log_termination(turn, "LLM requested termination")
                break

            if self.logger and resp.is_message():
                self.logger.log_debug(f"Assistant message (turn {turn}): {resp.response}")
        else:
            if self.logger:
                self.logger.log_termination(self.max_turns, "Max turns reached without termination")

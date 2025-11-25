import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from .llm import LanguageModel, GeminiLanguageModel, MockLanguageModel
from .tool import ToolRegistry
from .history import HistoryEntry, SystemPrompt, UserInstruction, LLMResponse, ToolCallResult
from .logger import Logger
from .env import AgentEnvironment

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
            model_name = self.config.get("model", "gemini-2.0-flash-thinking-exp-01-21")
            api_key = self.config.get("api_key", os.getenv("GEMINI_API_KEY"))
            return GeminiLanguageModel(model_name=model_name, api_key=api_key)
        elif llm_type == "mock":
            responses = self.config.get("mock_responses")
            return MockLanguageModel(responses=responses)
        else:
            raise ValueError(f"Unknown llm_type: {llm_type}. Use 'gemini' or 'mock'.")

    def initialize_logger(self):
        log_path = self.working_dir / ".waa" / "agent.log"
        if log_path.exists():
            raise RuntimeError(f"Log file already exists: {log_path}. Remove it to start a new run.")

        self.logger = Logger(log_path, self.debug)
        self.logger.log("Agent initialization started")
        self.logger.log(f"Working directory: {self.working_dir}")
        self.logger.log(f"Debug mode: {self.debug}")
        self.logger.log(f"Max turns: {self.max_turns}")

    def initialize_tool_registry(self):
        self.tool_registry = ToolRegistry()
        allowed_tools = self.env.get_config_value("allowed_tools", None)
        #########################################################
        # TODO: Load the tools into the tool registry           #
        #########################################################
        pass

    def load_system_prompt(self):
        #########################################################
        # TODO: Load the system prompt in to the history        #
        #########################################################
        pass

    def load_instruction(self):
        #########################################################
        # TODO: Load the user instruction in to the history     #
        #########################################################
        pass

    def initialize(self):
        self.initialize_environment()
        self.initialize_llm()
        self.initialize_logger()
        self.initialize_tool_registry()

        self.load_system_prompt()
        self.load_instruction()

    def query_llm(self, turn: int):
        #########################################################
        # TODO: Query the LLM                                   #
        #########################################################
        pass

    def execute_tool(self, tool_call: Dict[str, Any]):
        #########################################################
        # TODO: Execute the tool                                #
        #########################################################
        pass

    def run(self):
        #########################################################
        # TODO: Run the agent                                   #
        # 1. initialize the agent                               #
        # 2. enter the agentic loop                             #
        #########################################################
        pass

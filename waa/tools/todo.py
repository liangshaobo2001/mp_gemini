import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..tool import Tool, ToolArgument
from ..env import AgentEnvironment


class TodoAddTool(Tool):
    def __init__(self):
        super().__init__("todo.add")
        #########################################################
        # TODO: Initialize the schema                           #
        #########################################################
        pass

    def initialize(self, env: AgentEnvironment):
        #########################################################
        # TODO: Initialize the tool according to the environment#
        #########################################################
        pass

    def description(self) -> str:
        #########################################################
        # TODO: Return the description of the tool              #
        #########################################################
        pass

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        #########################################################
        # TODO: Execute the tool given the input arguments      #
        #########################################################
        pass


class TodoListTool(Tool):
    def __init__(self):
        super().__init__("todo.list")
        #########################################################
        # TODO: Initialize the schema                           #
        #########################################################
        pass

    def initialize(self, env: AgentEnvironment):
        #########################################################
        # TODO: Initialize the tool according to the environment#
        #########################################################
        pass

    def description(self) -> str:
        #########################################################
        # TODO: Return the description of the tool              #
        #########################################################
        pass

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        #########################################################
        # TODO: Execute the tool given the input arguments      #
        #########################################################
        pass


class TodoCompleteTool(Tool):
    def __init__(self):
        super().__init__("todo.complete")
        #########################################################
        # TODO: Initialize the schema                           #
        #########################################################
        pass

    def initialize(self, env: AgentEnvironment):
        #########################################################
        # TODO: Initialize the tool according to the environment#
        #########################################################
        pass

    def description(self) -> str:
        #########################################################
        # TODO: Return the description of the tool              #
        #########################################################
        pass

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        #########################################################
        # TODO: Execute the tool given the input arguments      #
        #########################################################
        pass


class TodoRemoveTool(Tool):
    def __init__(self):
        super().__init__("todo.remove")
        #########################################################
        # TODO: Initialize the schema                           #
        #########################################################
        pass

    def initialize(self, env: AgentEnvironment):
        #########################################################
        # TODO: Initialize the tool according to the environment#
        #########################################################
        pass

    def description(self) -> str:
        #########################################################
        # TODO: Return the description of the tool              #
        #########################################################
        pass

    def execute(self, input: Dict[str, Any]) -> Dict[str, Any]:
        #########################################################
        # TODO: Execute the tool given the input arguments      #
        #########################################################
        pass

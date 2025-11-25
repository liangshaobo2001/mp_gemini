"""
Unit tests for the TODO agent functionality.
Tests the agent's ability to manage TODO items using mock LLM responses.
"""

import unittest
import tempfile
import shutil
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

solution_parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(solution_parent_dir))

from waa.agent import Agent
from waa.env import AgentEnvironment
from waa.history import ToolCallResult


class TestTodoAgentRunner(unittest.TestCase):
    """
    Base test case runner that provides utilities for testing TODO agents
    with temporary directories.
    """

    def setUp(self):
        """Set up test environment before each test."""
        self.temp_dir = None
        self.agent = None

    def tearDown(self):
        """Clean up test environment after each test."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Failed to remove temp directory: {e}")

    def create_temp_workspace(self, config: Dict[str, Any], instruction: str = "") -> Path:
        """
        Create a temporary workspace directory with config and instruction files.

        Args:
            config: Configuration dictionary to write to config.json
            instruction: Instruction text to write to instruction.md

        Returns:
            Path to the temporary workspace directory
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="test_todo_agent_"))
        self.temp_dir = temp_dir

        waa_dir = temp_dir / ".waa"
        waa_dir.mkdir(parents=True, exist_ok=True)

        config_path = waa_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        instruction_path = waa_dir / "instruction.md"
        with open(instruction_path, 'w') as f:
            f.write(instruction)

        return temp_dir

    def run_agent(self, working_dir: Path, debug: bool = False) -> Agent:
        """
        Initialize and run an agent in the specified working directory.

        Args:
            working_dir: Path to the working directory
            debug: Enable debug mode (default: False)

        Returns:
            The agent instance after running
        """
        agent = Agent(working_dir, debug=debug)
        self.agent = agent
        agent.run()
        return agent

    def assert_todo_file_exists(self, msg: Optional[str] = None):
        """Assert that the todo.json file exists."""
        todo_file = self.temp_dir / ".waa" / "todo.json"
        self.assertTrue(todo_file.exists(), msg or f"Todo file should exist: {todo_file}")

    def assert_todo_file_not_exists(self, msg: Optional[str] = None):
        """Assert that the todo.json file does not exist."""
        todo_file = self.temp_dir / ".waa" / "todo.json"
        self.assertFalse(todo_file.exists(), msg or f"Todo file should not exist: {todo_file}")

    def get_todos_from_file(self) -> list:
        """Get the list of todos from the file."""
        todo_file = self.temp_dir / ".waa" / "todo.json"
        if not todo_file.exists():
            return []

        with open(todo_file, 'r') as f:
            return json.load(f)


class TestTodoAgentBasic(TestTodoAgentRunner):
    """Basic tests for TODO agent functionality."""

    def test_agent_initialization(self):
        """Test that the agent can be initialized with TODO tools."""
        config = {
            "llm_type": "mock",
            "max_turns": 1,
            "allowed_tools": ["todo.add"],
            "mock_responses": ["<terminate>"]
        }

        temp_dir = self.create_temp_workspace(config, "Test instruction")
        agent = Agent(temp_dir)
        agent.initialize()

        self.assertIsNotNone(agent.llm)
        self.assertIsNotNone(agent.tool_registry)
        self.assertIsNotNone(agent.env)
        self.assertEqual(agent.max_turns, 1)
        self.assertEqual(len(agent.tool_registry.list_tools()), 1)

    def test_agent_missing_config(self):
        """Test that agent raises error when config.json is missing."""
        temp_dir = Path(tempfile.mkdtemp(prefix="test_todo_agent_"))
        self.temp_dir = temp_dir

        agent = Agent(temp_dir)
        with self.assertRaises(FileNotFoundError):
            agent.initialize()

    def test_agent_missing_instruction(self):
        """Test that agent raises error when instruction.md is missing."""
        config = {
            "llm_type": "mock",
            "max_turns": 1,
            "allowed_tools": [],
            "mock_responses": ["<terminate>"]
        }

        temp_dir = Path(tempfile.mkdtemp(prefix="test_todo_agent_"))
        self.temp_dir = temp_dir

        waa_dir = temp_dir / ".waa"
        waa_dir.mkdir(parents=True, exist_ok=True)

        config_path = waa_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        agent = Agent(temp_dir)
        with self.assertRaises(FileNotFoundError):
            agent.initialize()


class TestTodoAgentAdd(TestTodoAgentRunner):
    """Tests for todo_add tool."""

    def test_todo_add_creates_todo(self):
        """Test that todo_add creates a todo item."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Implement login feature"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Add a todo item")
        agent = self.run_agent(temp_dir)

        self.assert_todo_file_exists()

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["description"], "Implement login feature")
        self.assertEqual(todos[0]["status"], "pending")
        self.assertEqual(todos[0]["id"], 1)

    def test_todo_add_multiple_todos(self):
        """Test that multiple todos can be added."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 3"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Add multiple todos")
        agent = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 3)
        self.assertEqual(todos[0]["id"], 1)
        self.assertEqual(todos[1]["id"], 2)
        self.assertEqual(todos[2]["id"], 3)

    def test_todo_add_without_description(self):
        """Test that todo_add handles missing description."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Add todo without description")
        agent = self.run_agent(temp_dir)

        add_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.add"
        ]

        self.assertEqual(len(add_results), 1)
        has_error = (add_results[0].error is not None) or (add_results[0].result and not add_results[0].result["ok"])
        self.assertTrue(has_error)


class TestTodoAgentList(TestTodoAgentRunner):
    """Tests for todo_list tool."""

    def test_todo_list_empty(self):
        """Test that todo_list handles empty todo list."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.list", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "List empty todos")
        agent = self.run_agent(temp_dir)

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 1)
        self.assertTrue(list_results[0].result["ok"])
        self.assertEqual(list_results[0].result["data"]["count"], 0)

    def test_todo_list_all(self):
        """Test that todo_list returns all todos."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "List all todos")
        agent = self.run_agent(temp_dir)

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 1)
        self.assertTrue(list_results[0].result["ok"])
        self.assertEqual(list_results[0].result["data"]["count"], 2)
        todos = list_results[0].result["data"]["todos"]
        self.assertEqual(len(todos), 2)

    def test_todo_list_filter_pending(self):
        """Test that todo_list can filter by pending status."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.complete", "todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {"status": "pending"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "List pending todos")
        agent = self.run_agent(temp_dir)

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 1)
        self.assertEqual(list_results[0].result["data"]["count"], 1)
        todos = list_results[0].result["data"]["todos"]
        self.assertEqual(todos[0]["id"], 2)

    def test_todo_list_filter_completed(self):
        """Test that todo_list can filter by completed status."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.complete", "todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {"status": "completed"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "List completed todos")
        agent = self.run_agent(temp_dir)

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 1)
        self.assertEqual(list_results[0].result["data"]["count"], 1)
        todos = list_results[0].result["data"]["todos"]
        self.assertEqual(todos[0]["id"], 1)
        self.assertEqual(todos[0]["status"], "completed")


class TestTodoAgentComplete(TestTodoAgentRunner):
    """Tests for todo_complete tool."""

    def test_todo_complete_marks_as_completed(self):
        """Test that todo_complete marks a todo as completed."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.complete"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Complete a todo")
        agent = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["status"], "completed")
        self.assertIn("completed_at", todos[0])

    def test_todo_complete_nonexistent(self):
        """Test that todo_complete handles nonexistent todo."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.complete"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 999}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Complete nonexistent todo")
        agent = self.run_agent(temp_dir)

        complete_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.complete"
        ]

        self.assertEqual(len(complete_results), 1)
        self.assertFalse(complete_results[0].result["ok"])


class TestTodoAgentRemove(TestTodoAgentRunner):
    """Tests for todo_remove tool."""

    def test_todo_remove_deletes_todo(self):
        """Test that todo_remove deletes a todo item."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.remove"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.remove", "arguments": {"id": 1}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Remove a todo")
        agent = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["id"], 2)

    def test_todo_remove_nonexistent(self):
        """Test that todo_remove handles nonexistent todo."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.remove"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.remove", "arguments": {"id": 999}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Remove nonexistent todo")
        agent = self.run_agent(temp_dir)

        remove_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.remove"
        ]

        self.assertEqual(len(remove_results), 1)
        self.assertFalse(remove_results[0].result["ok"])


class TestTodoAgentFullCycle(TestTodoAgentRunner):
    """Tests for full TODO lifecycle operations."""

    def test_full_todo_lifecycle(self):
        """Test complete todo lifecycle: add, list, complete, remove."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["todo.add", "todo.list", "todo.complete", "todo.remove"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 3"}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 2}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {"status": "completed"}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {"status": "pending"}}</tool_call>',
                '<tool_call>{"tool": "todo.remove", "arguments": {"id": 1}}</tool_call>',
                '<tool_call>{"tool": "todo.list", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test full todo lifecycle")
        agent = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 2)  # 3 added, 1 removed

        todo_by_id = {t["id"]: t for t in todos}
        self.assertEqual(todo_by_id[2]["status"], "completed")
        self.assertEqual(todo_by_id[3]["status"], "pending")
        self.assertNotIn(1, todo_by_id)  # ID 1 was removed

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 4)

        self.assertEqual(list_results[0].result["data"]["count"], 3)

        self.assertEqual(list_results[1].result["data"]["count"], 2)

        self.assertEqual(list_results[2].result["data"]["count"], 1)

        self.assertEqual(list_results[3].result["data"]["count"], 2)

    def test_multiple_complete_operations(self):
        """Test that completing a todo multiple times works correctly."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["todo.add", "todo.complete"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                '<tool_call>{"tool": "todo.complete", "arguments": {"id": 1}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Complete todo multiple times")
        agent = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["status"], "completed")


class TestTodoAgentErrorHandling(TestTodoAgentRunner):
    """Tests for error handling in TODO agent."""

    def test_invalid_status_filter(self):
        """Test that todo_list handles invalid status filter."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.list", "arguments": {"status": "invalid"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Invalid status filter")
        agent = self.run_agent(temp_dir)

        list_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "todo.list"
        ]

        self.assertEqual(len(list_results), 1)
        self.assertFalse(list_results[0].result["ok"])

    def test_todo_persistence(self):
        """Test that todos persist across agent runs."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 1"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Add a todo")
        agent1 = self.run_agent(temp_dir)

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 1)

        config2 = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["todo.add", "todo.list"],
            "mock_responses": [
                '<tool_call>{"tool": "todo.list", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "todo.add", "arguments": {"description": "Task 2"}}</tool_call>',
                "<terminate>"
            ]
        }

        config_path = temp_dir / ".waa" / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config2, f, indent=4)

        log_file = temp_dir / ".waa" / "agent.log"
        if log_file.exists():
            log_file.unlink()

        agent2 = Agent(temp_dir)
        agent2.run()

        todos = self.get_todos_from_file()
        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0]["id"], 1)
        self.assertEqual(todos[1]["id"], 2)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()

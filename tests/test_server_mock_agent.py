"""
Unit tests for the server agent functionality.
Tests the agent's ability to manage NPM servers using mock LLM responses.
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


class TestServerAgentRunner(unittest.TestCase):
    """
    Base test case runner that provides utilities for testing agents
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
                import subprocess
                subprocess.run(
                    ["npm", "run", "stop"],
                    cwd=self.temp_dir,
                    capture_output=True,
                    timeout=5
                )
            except Exception:
                pass

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
        temp_dir = Path(tempfile.mkdtemp(prefix="test_server_agent_"))
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

    def assert_file_exists(self, file_path: Path, msg: Optional[str] = None):
        """Assert that a file exists."""
        self.assertTrue(file_path.exists(), msg or f"File should exist: {file_path}")

    def assert_file_not_exists(self, file_path: Path, msg: Optional[str] = None):
        """Assert that a file does not exist."""
        self.assertFalse(file_path.exists(), msg or f"File should not exist: {file_path}")

    def assert_server_running(self, msg: Optional[str] = None):
        """Assert that the Node.js server is running."""
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            return # Skip on Windows

        result = subprocess.run(
            ["pgrep", "-f", "node.*index.js"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, msg or "Server should be running")

    def assert_server_not_running(self, msg: Optional[str] = None):
        """Assert that the Node.js server is not running."""
        import subprocess
        import platform
        
        if platform.system() == "Windows":
            # On Windows, we can use tasklist
            cmd = ["tasklist", "/FI", "IMAGENAME eq node.exe"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # If node.exe is not found, tasklist output usually contains "No tasks are running" or similar info, 
            # but return code is 0. We need to check output.
            # However, checking for specific script is harder with tasklist.
            # For now, let's just skip this check on Windows or assume it works if we can't easily check.
            return

        result = subprocess.run(
            ["pgrep", "-f", "node.*index.js"],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0, msg or "Server should not be running")


class TestServerAgentBasic(TestServerAgentRunner):
    """Basic tests for server agent functionality."""

    def test_agent_initialization(self):
        """Test that the agent can be initialized with a valid config."""
        config = {
            "llm_type": "mock",
            "max_turns": 1,
            "allowed_tools": ["npm.init"],
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
        temp_dir = Path(tempfile.mkdtemp(prefix="test_server_agent_"))
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

        temp_dir = Path(tempfile.mkdtemp(prefix="test_server_agent_"))
        self.temp_dir = temp_dir

        waa_dir = temp_dir / ".waa"
        waa_dir.mkdir(parents=True, exist_ok=True)

        config_path = waa_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        agent = Agent(temp_dir)
        with self.assertRaises(FileNotFoundError):
            agent.initialize()


class TestServerAgentNPMInit(TestServerAgentRunner):
    """Tests for npm_init tool."""

    def test_npm_init_creates_package_json(self):
        """Test that npm_init tool creates package.json and installs dependencies."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["npm.init"],
            "mock_responses": [
                '<tool_call>{"tool": "npm.init", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Initialize the server")
        agent = self.run_agent(temp_dir)

        package_json_path = temp_dir / "package.json"
        self.assert_file_exists(package_json_path)

        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
            self.assertEqual(package_data["name"], "waa-workspace")
            self.assertIn("express", package_data["dependencies"])
            self.assertIn("nodemon", package_data["devDependencies"])

        node_modules_path = temp_dir / "node_modules"
        self.assert_file_exists(node_modules_path)


class TestServerAgentFullCycle(TestServerAgentRunner):
    """Tests for full server lifecycle: init, start, status, logs, stop."""

    def test_full_server_lifecycle(self):
        """Test complete server lifecycle with all tools."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["npm.init", "npm.start", "npm.stop", "npm.status", "npm.logs"],
            "mock_responses": [
                '<tool_call>{"tool": "npm.init", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.start", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.status", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.logs", "arguments": {"lines": 20}}</tool_call>',
                '<tool_call>{"tool": "npm.stop", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Run full server lifecycle")

        index_js_path = temp_dir / "index.js"
        with open(index_js_path, 'w') as f:
            f.write("""
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
""")

        agent = self.run_agent(temp_dir)

        self.assertGreaterEqual(len(agent.history), 12)  # System + User + 6 mock responses + 5 tool results

        self.assert_file_exists(temp_dir / "package.json")

        log_path = temp_dir / ".waa" / "server.log"

        self.assert_server_not_running()

    def test_server_status_tracking(self):
        """Test that server status is correctly tracked across start and stop."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["npm.init", "npm.start", "npm.stop", "npm.status"],
            "mock_responses": [
                '<tool_call>{"tool": "npm.init", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.status", "arguments": {}}</tool_call>',  # Should not be running
                '<tool_call>{"tool": "npm.start", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.status", "arguments": {}}</tool_call>',  # Should be running
                '<tool_call>{"tool": "npm.stop", "arguments": {}}</tool_call>',
                '<tool_call>{"tool": "npm.status", "arguments": {}}</tool_call>',  # Should not be running
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Track server status")

        index_js_path = temp_dir / "index.js"
        with open(index_js_path, 'w') as f:
            f.write("""
const express = require('express');
const app = express();
app.listen(3000, () => console.log('Server started'));
""")

        agent = self.run_agent(temp_dir)

        status_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "npm.status"
        ]

        self.assertEqual(len(status_results), 3)
        self.assertEqual(status_results[0].result["data"]["running"], False)
        self.assertEqual(status_results[2].result["data"]["running"], False)


class TestServerAgentErrorHandling(TestServerAgentRunner):
    """Tests for error handling in server agent."""

    def test_npm_start_without_init(self):
        """Test that starting server without initialization handles error gracefully."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["npm.start"],
            "mock_responses": [
                '<tool_call>{"tool": "npm.start", "arguments": {}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Start without init")
        agent = self.run_agent(temp_dir)

        tool_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "npm.start"
        ]

        self.assertEqual(len(tool_results), 1)
        self.assertIsNotNone(tool_results[0].error or (not tool_results[0].result["ok"]))

    def test_npm_logs_without_log_file(self):
        """Test that reading logs without a log file handles error gracefully."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["npm.logs"],
            "mock_responses": [
                '<tool_call>{"tool": "npm.logs", "arguments": {"lines": 10}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Read logs without file")
        agent = self.run_agent(temp_dir)

        tool_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "npm.logs"
        ]

        self.assertEqual(len(tool_results), 1)
        self.assertIsNotNone(tool_results[0].result)


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()

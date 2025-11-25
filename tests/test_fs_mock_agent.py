"""
Unit tests for the file system agent functionality.
Tests the agent's ability to manage files and directories using mock LLM responses.
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


class TestFSAgentRunner(unittest.TestCase):
    """
    Base test case runner that provides utilities for testing file system agents
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
        temp_dir = Path(tempfile.mkdtemp(prefix="test_fs_agent_"))
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

    def assert_file_content(self, file_path: Path, expected_content: str, msg: Optional[str] = None):
        """Assert that a file has the expected content."""
        self.assert_file_exists(file_path)
        actual_content = file_path.read_text(encoding='utf-8')
        self.assertEqual(actual_content, expected_content, msg or f"File content mismatch: {file_path}")

    def assert_directory_exists(self, dir_path: Path, msg: Optional[str] = None):
        """Assert that a directory exists."""
        self.assertTrue(dir_path.exists() and dir_path.is_dir(), msg or f"Directory should exist: {dir_path}")

    def assert_directory_not_exists(self, dir_path: Path, msg: Optional[str] = None):
        """Assert that a directory does not exist."""
        self.assertFalse(dir_path.exists(), msg or f"Directory should not exist: {dir_path}")


class TestFSAgentBasic(TestFSAgentRunner):
    """Basic tests for file system agent functionality."""

    def test_agent_initialization(self):
        """Test that the agent can be initialized with a valid config."""
        config = {
            "llm_type": "mock",
            "max_turns": 1,
            "allowed_tools": ["fs.write"],
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
        temp_dir = Path(tempfile.mkdtemp(prefix="test_fs_agent_"))
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

        temp_dir = Path(tempfile.mkdtemp(prefix="test_fs_agent_"))
        self.temp_dir = temp_dir

        waa_dir = temp_dir / ".waa"
        waa_dir.mkdir(parents=True, exist_ok=True)

        config_path = waa_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        agent = Agent(temp_dir)
        with self.assertRaises(FileNotFoundError):
            agent.initialize()


class TestFSAgentFileWrite(TestFSAgentRunner):
    """Tests for fs_write tool."""

    def test_fs_write_creates_file(self):
        """Test that fs_write tool creates a file with content."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Hello, World!"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Create a test file")
        agent = self.run_agent(temp_dir)

        test_file = temp_dir / "test.txt"
        self.assert_file_exists(test_file)
        self.assert_file_content(test_file, "Hello, World!")

    def test_fs_write_creates_nested_file(self):
        """Test that fs_write creates directories if they don't exist."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "subdir/nested/test.txt", "content": "Nested content"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Create a nested file")
        agent = self.run_agent(temp_dir)

        nested_file = temp_dir / "subdir" / "nested" / "test.txt"
        self.assert_file_exists(nested_file)
        self.assert_file_content(nested_file, "Nested content")

    def test_fs_write_overwrites_file(self):
        """Test that fs_write overwrites existing files."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "First content"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Second content"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Overwrite a file")
        agent = self.run_agent(temp_dir)

        test_file = temp_dir / "test.txt"
        self.assert_file_exists(test_file)
        self.assert_file_content(test_file, "Second content")


class TestFSAgentFileRead(TestFSAgentRunner):
    """Tests for fs_read tool."""

    def test_fs_read_reads_file(self):
        """Test that fs_read tool reads a file correctly."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.read"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Test content"}}</tool_call>',
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "test.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Read a file")
        agent = self.run_agent(temp_dir)

        read_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.read"
        ]

        self.assertEqual(len(read_results), 1)
        self.assertEqual(read_results[0].result["data"]["content"], "Test content")

    def test_fs_read_nonexistent_file(self):
        """Test that fs_read handles nonexistent files gracefully."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.read"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "nonexistent.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Read nonexistent file")
        agent = self.run_agent(temp_dir)

        read_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.read"
        ]

        self.assertEqual(len(read_results), 1)
        self.assertFalse(read_results[0].result["ok"])


class TestFSAgentFileEdit(TestFSAgentRunner):
    """Tests for fs_edit tool."""

    def test_fs_edit_edits_file(self):
        """Test that fs_edit tool edits a file correctly."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.edit", "fs.read"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Hello World"}}</tool_call>',
                '<tool_call>{"tool": "fs.edit", "arguments": {"path": "test.txt", "old_text": "World", "new_text": "Universe"}}</tool_call>',
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "test.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Edit a file")
        agent = self.run_agent(temp_dir)

        test_file = temp_dir / "test.txt"
        self.assert_file_content(test_file, "Hello Universe")

    def test_fs_edit_text_not_found(self):
        """Test that fs_edit handles text not found error."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.edit"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Hello World"}}</tool_call>',
                '<tool_call>{"tool": "fs.edit", "arguments": {"path": "test.txt", "old_text": "Nonexistent", "new_text": "Something"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Edit with text not found")
        agent = self.run_agent(temp_dir)

        edit_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.edit"
        ]

        self.assertEqual(len(edit_results), 1)
        self.assertFalse(edit_results[0].result["ok"])


class TestFSAgentFileDelete(TestFSAgentRunner):
    """Tests for fs_delete tool."""

    def test_fs_delete_deletes_file(self):
        """Test that fs_delete tool deletes a file."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.delete"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test.txt", "content": "Delete me"}}</tool_call>',
                '<tool_call>{"tool": "fs.delete", "arguments": {"path": "test.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Delete a file")
        agent = self.run_agent(temp_dir)

        test_file = temp_dir / "test.txt"
        self.assert_file_not_exists(test_file)

    def test_fs_delete_nonexistent_file(self):
        """Test that fs_delete handles nonexistent files."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.delete"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.delete", "arguments": {"path": "nonexistent.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Delete nonexistent file")
        agent = self.run_agent(temp_dir)

        delete_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.delete"
        ]

        self.assertEqual(len(delete_results), 1)
        self.assertFalse(delete_results[0].result["ok"])


class TestFSAgentDirectory(TestFSAgentRunner):
    """Tests for directory operations."""

    def test_fs_mkdir_creates_directory(self):
        """Test that fs_mkdir creates a directory."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.mkdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "new_dir"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Create a directory")
        agent = self.run_agent(temp_dir)

        new_dir = temp_dir / "new_dir"
        self.assert_directory_exists(new_dir)

    def test_fs_mkdir_creates_nested_directory(self):
        """Test that fs_mkdir creates nested directories."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.mkdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "parent/child/grandchild"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Create nested directories")
        agent = self.run_agent(temp_dir)

        nested_dir = temp_dir / "parent" / "child" / "grandchild"
        self.assert_directory_exists(nested_dir)

    def test_fs_rmdir_removes_empty_directory(self):
        """Test that fs_rmdir removes an empty directory."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.mkdir", "fs.rmdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "test_dir"}}</tool_call>',
                '<tool_call>{"tool": "fs.rmdir", "arguments": {"path": "test_dir"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Remove empty directory")
        agent = self.run_agent(temp_dir)

        test_dir = temp_dir / "test_dir"
        self.assert_directory_not_exists(test_dir)

    def test_fs_rmdir_removes_nonempty_directory_recursively(self):
        """Test that fs_rmdir removes a non-empty directory with recursive flag."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.mkdir", "fs.write", "fs.rmdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "test_dir"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "test_dir/file.txt", "content": "content"}}</tool_call>',
                '<tool_call>{"tool": "fs.rmdir", "arguments": {"path": "test_dir", "recursive": true}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Remove non-empty directory")
        agent = self.run_agent(temp_dir)

        test_dir = temp_dir / "test_dir"
        self.assert_directory_not_exists(test_dir)


class TestFSAgentDirectoryListing(TestFSAgentRunner):
    """Tests for directory listing operations."""

    def test_fs_ls_lists_directory(self):
        """Test that fs_ls lists directory contents."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.mkdir", "fs.ls"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "file1.txt", "content": "content1"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "file2.txt", "content": "content2"}}</tool_call>',
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "subdir"}}</tool_call>',
                '<tool_call>{"tool": "fs.ls", "arguments": {"path": "."}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "List directory contents")
        agent = self.run_agent(temp_dir)

        ls_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.ls"
        ]

        self.assertEqual(len(ls_results), 1)
        entries = ls_results[0].result["data"]["entries"]

        entry_names = [e["name"] for e in entries]
        self.assertIn("file1.txt", entry_names)
        self.assertIn("file2.txt", entry_names)
        self.assertIn("subdir", entry_names)

    def test_fs_tree_shows_tree(self):
        """Test that fs_tree shows directory tree structure."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.mkdir", "fs.tree"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "dir1/subdir"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "dir1/file1.txt", "content": "content"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "dir1/subdir/file2.txt", "content": "content"}}</tool_call>',
                '<tool_call>{"tool": "fs.tree", "arguments": {"path": ".", "max_depth": 3}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Show directory tree")
        agent = self.run_agent(temp_dir)

        tree_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.tree"
        ]

        self.assertEqual(len(tree_results), 1)
        self.assertTrue(tree_results[0].result["ok"])
        tree = tree_results[0].result["data"]["tree"]
        self.assertIsInstance(tree, list)


class TestFSAgentFullCycle(TestFSAgentRunner):
    """Tests for full file system lifecycle operations."""

    def test_full_file_lifecycle(self):
        """Test complete file lifecycle: create, read, edit, delete."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["fs.write", "fs.read", "fs.edit", "fs.delete"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "lifecycle.txt", "content": "Initial content"}}</tool_call>',
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "lifecycle.txt"}}</tool_call>',
                '<tool_call>{"tool": "fs.edit", "arguments": {"path": "lifecycle.txt", "old_text": "Initial", "new_text": "Modified"}}</tool_call>',
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "lifecycle.txt"}}</tool_call>',
                '<tool_call>{"tool": "fs.delete", "arguments": {"path": "lifecycle.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test full file lifecycle")
        agent = self.run_agent(temp_dir)

        self.assertGreaterEqual(len(agent.history), 12)  # System + User + 6 mock responses + 5 tool results

        lifecycle_file = temp_dir / "lifecycle.txt"
        self.assert_file_not_exists(lifecycle_file)

        read_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.read"
        ]

        self.assertEqual(len(read_results), 2)
        self.assertEqual(read_results[0].result["data"]["content"], "Initial content")
        self.assertEqual(read_results[1].result["data"]["content"], "Modified content")

    def test_full_directory_lifecycle(self):
        """Test complete directory lifecycle: create, populate, list, delete."""
        config = {
            "llm_type": "mock",
            "max_turns": 50,
            "allowed_tools": ["fs.mkdir", "fs.write", "fs.ls", "fs.rmdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.mkdir", "arguments": {"path": "project"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "project/readme.md", "content": "# Project"}}</tool_call>',
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "project/index.js", "content": "console.log()"}}</tool_call>',
                '<tool_call>{"tool": "fs.ls", "arguments": {"path": "project"}}</tool_call>',
                '<tool_call>{"tool": "fs.rmdir", "arguments": {"path": "project", "recursive": true}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test full directory lifecycle")
        agent = self.run_agent(temp_dir)

        project_dir = temp_dir / "project"
        self.assert_directory_not_exists(project_dir)

        ls_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.ls"
        ]

        self.assertEqual(len(ls_results), 1)
        entries = ls_results[0].result["data"]["entries"]
        entry_names = [e["name"] for e in entries]
        self.assertIn("readme.md", entry_names)
        self.assertIn("index.js", entry_names)


class TestFSAgentErrorHandling(TestFSAgentRunner):
    """Tests for error handling in file system agent."""

    def test_path_outside_main_folder(self):
        """Test that operations outside main folder are rejected."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "../outside.txt", "content": "content"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test path outside main folder")
        agent = self.run_agent(temp_dir)

        write_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.write"
        ]

        self.assertEqual(len(write_results), 1)
        self.assertFalse(write_results[0].result["ok"])
        self.assertIn("outside", write_results[0].result["error"])

    def test_delete_nonexistent_directory(self):
        """Test that deleting nonexistent directory handles error gracefully."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.rmdir"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.rmdir", "arguments": {"path": "nonexistent_dir"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Delete nonexistent directory")
        agent = self.run_agent(temp_dir)

        rmdir_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.rmdir"
        ]

        self.assertEqual(len(rmdir_results), 1)
        self.assertFalse(rmdir_results[0].result["ok"])


class TestFSAgentProtectedFiles(TestFSAgentRunner):
    """Tests for protected files functionality."""

    def test_protected_file_cannot_be_written(self):
        """Test that protected files cannot be overwritten."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write"],
            "protected_files": ["protected.txt"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "protected.txt", "content": "new content"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test protected file write")

        protected_file = temp_dir / "protected.txt"
        protected_file.write_text("original content")

        agent = self.run_agent(temp_dir)

        write_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.write"
        ]

        self.assertEqual(len(write_results), 1)
        self.assertFalse(write_results[0].result["ok"])
        self.assertIn("protected", write_results[0].result["error"].lower())

        self.assertEqual(protected_file.read_text(), "original content")

    def test_protected_file_cannot_be_edited(self):
        """Test that protected files cannot be edited."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.edit"],
            "protected_files": ["protected.txt"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.edit", "arguments": {"path": "protected.txt", "old_text": "original", "new_text": "modified"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test protected file edit")

        protected_file = temp_dir / "protected.txt"
        protected_file.write_text("original content")

        agent = self.run_agent(temp_dir)

        edit_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.edit"
        ]

        self.assertEqual(len(edit_results), 1)
        self.assertFalse(edit_results[0].result["ok"])
        self.assertIn("protected", edit_results[0].result["error"].lower())

        self.assertEqual(protected_file.read_text(), "original content")

    def test_protected_file_cannot_be_deleted(self):
        """Test that protected files cannot be deleted."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.delete"],
            "protected_files": ["protected.txt"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.delete", "arguments": {"path": "protected.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test protected file delete")

        protected_file = temp_dir / "protected.txt"
        protected_file.write_text("original content")

        agent = self.run_agent(temp_dir)

        delete_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.delete"
        ]

        self.assertEqual(len(delete_results), 1)
        self.assertFalse(delete_results[0].result["ok"])
        self.assertIn("protected", delete_results[0].result["error"].lower())

        self.assertTrue(protected_file.exists())
        self.assertEqual(protected_file.read_text(), "original content")

    def test_protected_file_can_be_read(self):
        """Test that protected files can still be read."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.read"],
            "protected_files": ["protected.txt"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.read", "arguments": {"path": "protected.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test protected file read")

        protected_file = temp_dir / "protected.txt"
        protected_file.write_text("original content")

        agent = self.run_agent(temp_dir)

        read_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.read"
        ]

        self.assertEqual(len(read_results), 1)
        self.assertTrue(read_results[0].result["ok"])
        self.assertEqual(read_results[0].result["data"]["content"], "original content")

    def test_non_protected_file_can_be_modified(self):
        """Test that non-protected files can still be modified when protected_files is set."""
        config = {
            "llm_type": "mock",
            "max_turns": 10,
            "allowed_tools": ["fs.write", "fs.edit", "fs.delete"],
            "protected_files": ["protected.txt"],
            "mock_responses": [
                '<tool_call>{"tool": "fs.write", "arguments": {"path": "normal.txt", "content": "content"}}</tool_call>',
                '<tool_call>{"tool": "fs.edit", "arguments": {"path": "normal.txt", "old_text": "content", "new_text": "modified"}}</tool_call>',
                '<tool_call>{"tool": "fs.delete", "arguments": {"path": "normal.txt"}}</tool_call>',
                "<terminate>"
            ]
        }

        temp_dir = self.create_temp_workspace(config, "Test non-protected file")
        agent = self.run_agent(temp_dir)

        write_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.write"
        ]
        edit_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.edit"
        ]
        delete_results = [
            entry for entry in agent.history
            if isinstance(entry, ToolCallResult) and entry.tool_name == "fs.delete"
        ]

        self.assertEqual(len(write_results), 1)
        self.assertTrue(write_results[0].result["ok"])

        self.assertEqual(len(edit_results), 1)
        self.assertTrue(edit_results[0].result["ok"])

        self.assertEqual(len(delete_results), 1)
        self.assertTrue(delete_results[0].result["ok"])


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()

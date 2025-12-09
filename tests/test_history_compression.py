import unittest
import tempfile
import shutil
import json
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from waa.agent import Agent
from waa.history import ToolCallResult

class TestHistoryCompression(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.waa_dir = self.temp_dir / ".waa"
        self.waa_dir.mkdir()
        
        # Create config with many mock responses to trigger compression
        responses = []
        for i in range(60):
            responses.append(f'<tool_call>{{"tool": "fs.read", "arguments": {{"path": "file{i}.txt"}} }}</tool_call>')
        responses.append('<terminate>')

        with open(self.waa_dir / "config.json", "w") as f:
            json.dump({
                "llm_type": "mock",
                "mock_responses": responses
            }, f)
            
        with open(self.waa_dir / "instruction.md", "w") as f:
            f.write("Do a lot of things.")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_history_compression(self):
        agent = Agent(self.temp_dir)
        # We need to mock tool execution to avoid actual file reads failing
        # But since we use mock LLM, the agent will try to execute tools.
        # We can just let it fail or mock the tool registry.
        # Easier: let it run, it will log errors but continue until max turns or terminate.
        # We just want to check history state.
        
        agent.max_turns = 70 # Allow enough turns
        agent.run()

        # Check if history items are summarized
        # We expect > 50 items.
        self.assertGreater(len(agent.history), 50)
        
        # Check if an item in the middle is summarized
        # Index 0 is system, 1 is user. 2+ should be summarized if we have enough.
        # The loop in agent.py is: for i in range(2, len(self.history) - 10): self.history[i].summarize()
        # So item 10 should be summarized.
        
        item = agent.history[10]
        if isinstance(item, ToolCallResult):
            content = item.get_content()
            self.assertIn("summary", content)
            self.assertEqual(content["summary"], "Tool execution completed (details hidden)")

if __name__ == "__main__":
    unittest.main()

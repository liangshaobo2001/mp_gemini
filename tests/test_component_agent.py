import unittest
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from waa.agent import Agent

class TestComponentAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.waa_dir = self.temp_dir / ".waa"
        self.waa_dir.mkdir()
        
        # Create config
        with open(self.waa_dir / "config.json", "w") as f:
            json.dump({
                "llm_type": "mock",
                "mock_responses": [
                    # 1. Create components directory
                    '<tool_call>{"tool": "fs.create_directory", "arguments": {"path": "components"}}</tool_call>',
                    # 2. Create navbar component
                    '<tool_call>{"tool": "fs.write", "arguments": {"path": "components/navbar.html", "content": "<nav>Navbar</nav>"}}</tool_call>',
                    # 3. Register navbar component
                    '<tool_call>{"tool": "component.register", "arguments": {"name": "navbar", "path": "navbar.html", "description": "Main navigation"}}</tool_call>',
                    # 4. List components
                    '<tool_call>{"tool": "component.list", "arguments": {}}</tool_call>',
                    # 5. Terminate
                    '<terminate>'
                ]
            }, f)
            
        # Create instruction
        with open(self.waa_dir / "instruction.md", "w") as f:
            f.write("Create a reusable navbar component.")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_component_lifecycle(self):
        agent = Agent(self.temp_dir)
        agent.run()

        # Verify components directory exists
        self.assertTrue((self.temp_dir / "components").exists())
        
        # Verify navbar file exists
        self.assertTrue((self.temp_dir / "components" / "navbar.html").exists())
        
        # Verify registry exists and contains navbar
        registry_path = self.waa_dir / "components.json"
        self.assertTrue(registry_path.exists())
        
        with open(registry_path, "r") as f:
            registry = json.load(f)
            self.assertIn("navbar", registry)
            self.assertEqual(registry["navbar"]["path"], "navbar.html")

if __name__ == "__main__":
    unittest.main()

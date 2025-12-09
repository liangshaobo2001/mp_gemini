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

class TestPageAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.waa_dir = self.temp_dir / ".waa"
        self.waa_dir.mkdir()
        
        # Create config
        with open(self.waa_dir / "config.json", "w") as f:
            json.dump({
                "llm_type": "mock",
                "mock_responses": [
                    # 1. Register index page
                    '<tool_call>{"tool": "page.register", "arguments": {"name": "index.html", "title": "Home", "components": ["navbar"]}}</tool_call>',
                    # 2. Register about page
                    '<tool_call>{"tool": "page.register", "arguments": {"name": "about.html", "route": "/about", "title": "About", "components": ["navbar", "footer"]}}</tool_call>',
                    # 3. List pages
                    '<tool_call>{"tool": "page.list", "arguments": {}}</tool_call>',
                    # 4. Terminate
                    '<terminate>'
                ]
            }, f)
            
        # Create instruction
        with open(self.waa_dir / "instruction.md", "w") as f:
            f.write("Create pages and register them.")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_page_lifecycle(self):
        agent = Agent(self.temp_dir)
        agent.run()

        # Verify registry exists
        registry_path = self.waa_dir / "pages.json"
        self.assertTrue(registry_path.exists())
        
        with open(registry_path, "r") as f:
            registry = json.load(f)
            
            # Check index
            self.assertIn("index.html", registry)
            self.assertEqual(registry["index.html"]["route"], "/")
            self.assertEqual(registry["index.html"]["components"], ["navbar"])
            
            # Check about
            self.assertIn("about.html", registry)
            self.assertEqual(registry["about.html"]["route"], "/about")
            self.assertEqual(registry["about.html"]["components"], ["navbar", "footer"])

if __name__ == "__main__":
    unittest.main()

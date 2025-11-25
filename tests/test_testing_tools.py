"""
Test the Playwright and Supertest tools.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path

from waa.env import AgentEnvironment
from waa.tools.playwright import PlaywrightInitTool, PlaywrightRunTool
from waa.tools.supertest import SupertestInitTool, SupertestRunTool


class TestPlaywrightTools(unittest.TestCase):
    """Test Playwright tools."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env = AgentEnvironment(self.temp_dir, {})

    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_playwright_init_tool_creation(self):
        """Test that PlaywrightInitTool can be created and initialized."""
        tool = PlaywrightInitTool()
        self.assertEqual(tool.name, "playwright.init")

        tool.initialize(self.env)
        self.assertEqual(tool.main_folder, self.temp_dir)

    def test_playwright_run_tool_creation(self):
        """Test that PlaywrightRunTool can be created and initialized."""
        tool = PlaywrightRunTool()
        self.assertEqual(tool.name, "playwright.run")

        tool.initialize(self.env)
        self.assertEqual(tool.main_folder, self.temp_dir)

    def test_playwright_init_creates_config(self):
        """Test that playwright_init creates playwright.config.js."""
        tool = PlaywrightInitTool()
        tool.initialize(self.env)

        package_json = {
            "name": "test",
            "version": "1.0.0"
        }
        with open(self.temp_dir / "package.json", "w") as f:
            json.dump(package_json, f)

        result = tool.execute({})

        config_path = self.temp_dir / "playwright.config.js"
        self.assertTrue(config_path.exists(), "playwright.config.js should be created")

        with open(config_path, "r") as f:
            config_content = f.read()
            self.assertIn("defineConfig", config_content)
            self.assertIn("testDir", config_content)
            self.assertIn("baseURL", config_content)

    def test_playwright_init_updates_package_json(self):
        """Test that playwright_init updates package.json."""
        tool = PlaywrightInitTool()
        tool.initialize(self.env)

        package_json = {
            "name": "test",
            "version": "1.0.0"
        }
        with open(self.temp_dir / "package.json", "w") as f:
            json.dump(package_json, f)

        result = tool.execute({})

        with open(self.temp_dir / "package.json", "r") as f:
            updated = json.load(f)

        self.assertIn("devDependencies", updated)
        self.assertIn("@playwright/test", updated["devDependencies"])

        self.assertIn("scripts", updated)
        self.assertIn("test:ui", updated["scripts"])


class TestSupertestTools(unittest.TestCase):
    """Test Supertest tools."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env = AgentEnvironment(self.temp_dir, {})

    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_supertest_init_tool_creation(self):
        """Test that SupertestInitTool can be created and initialized."""
        tool = SupertestInitTool()
        self.assertEqual(tool.name, "supertest.init")

        tool.initialize(self.env)
        self.assertEqual(tool.main_folder, self.temp_dir)

    def test_supertest_run_tool_creation(self):
        """Test that SupertestRunTool can be created and initialized."""
        tool = SupertestRunTool()
        self.assertEqual(tool.name, "supertest.run")

        tool.initialize(self.env)
        self.assertEqual(tool.main_folder, self.temp_dir)

    def test_supertest_init_updates_package_json(self):
        """Test that supertest_init updates package.json."""
        tool = SupertestInitTool()
        tool.initialize(self.env)

        package_json = {
            "name": "test",
            "version": "1.0.0"
        }
        with open(self.temp_dir / "package.json", "w") as f:
            json.dump(package_json, f)

        result = tool.execute({})

        with open(self.temp_dir / "package.json", "r") as f:
            updated = json.load(f)

        self.assertIn("devDependencies", updated)
        self.assertIn("jest", updated["devDependencies"])
        self.assertIn("supertest", updated["devDependencies"])

        self.assertIn("scripts", updated)
        self.assertIn("test", updated["scripts"])
        self.assertIn("test:api", updated["scripts"])

    def test_tool_arguments(self):
        """Test that tools have correct arguments."""
        playwright_run = PlaywrightRunTool()
        supertest_run = SupertestRunTool()

        args = set(playwright_run.schema.arguments.keys())
        self.assertIn("test_file", args)
        self.assertIn("headed", args)

        args = set(supertest_run.schema.arguments.keys())
        self.assertIn("test_file", args)
        self.assertIn("verbose", args)


class TestToolDescriptions(unittest.TestCase):
    """Test tool descriptions are informative."""

    def test_playwright_descriptions(self):
        """Test Playwright tool descriptions."""
        init_tool = PlaywrightInitTool()
        run_tool = PlaywrightRunTool()

        init_desc = init_tool.description()
        run_desc = run_tool.description()

        self.assertIn("playwright.config.js", init_desc)
        self.assertIn("Initialize", init_desc)

        self.assertIn("UI tests", run_desc)
        self.assertIn("port 3000", run_desc)

    def test_supertest_descriptions(self):
        """Test Supertest tool descriptions."""
        init_tool = SupertestInitTool()
        run_tool = SupertestRunTool()

        init_desc = init_tool.description()
        run_desc = run_tool.description()

        self.assertIn("Jest", init_desc)
        self.assertIn("Supertest", init_desc)

        self.assertIn("API tests", run_desc)
        self.assertIn("Jest", run_desc)


if __name__ == "__main__":
    unittest.main()

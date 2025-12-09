import unittest
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from waa.layout_parser import LayoutParser

class TestLayoutParser(unittest.TestCase):
    def setUp(self):
        self.parser = LayoutParser()

    def test_parse_wireframe(self):
        wireframe_data = {
            "sections": [
                {"type": "navbar", "links": ["Home", "Contact"]},
                {"type": "hero", "title": "My Website", "subtitle": "Welcome"},
                {"type": "footer", "text": "Copyright 2025"}
            ]
        }

        files = self.parser.parse_wireframe(wireframe_data)
        
        self.assertIn("index.html", files)
        self.assertIn("style.css", files)

        html = files["index.html"]
        self.assertIn('<nav class="navbar">', html)
        self.assertIn("Home", html)
        self.assertIn("Contact", html)
        self.assertIn('<header class="hero">', html)
        self.assertIn("My Website", html)
        self.assertIn('<footer class="footer">', html)

    def test_unknown_section(self):
        wireframe_data = {
            "sections": [
                {"type": "unknown_widget"}
            ]
        }
        files = self.parser.parse_wireframe(wireframe_data)
        html = files["index.html"]
        self.assertIn("generic-section", html)
        self.assertIn("Placeholder for unknown_widget", html)

    def test_extended_sections(self):
        wireframe_data = {
            "sections": [
                {"type": "sidebar", "links": ["A", "B"]},
                {"type": "form", "fields": ["Username"]},
                {"type": "gallery", "images": 2}
            ]
        }
        files = self.parser.parse_wireframe(wireframe_data)
        html = files["index.html"]
        
        self.assertIn("sidebar", html)
        self.assertIn("form", html)
        self.assertIn("gallery", html)
        self.assertIn("Username", html)

if __name__ == "__main__":
    unittest.main()

import os
import json
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
WORKSPACE_DIR = Path("targets/autoweb_demo")

def print_step(step):
    print(f"\n{'='*50}\n{step}\n{'='*50}")

def main():
    print_step("Starting Demo Script")
    
    # Ensure server is running (user must start it separately)
    try:
        requests.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print("Error: Server is not running. Please run 'python server_bridge.py' in another terminal.")
        return

    # 1. Send Wireframe
    print_step("1. Sending Wireframe to /wireframe")
    wireframe_payload = {
        "message": "Create a portfolio site for a photographer.",
        "wireframe": {
            "sections": [
                {"type": "navbar", "links": ["Home", "Gallery", "Contact"]},
                {"type": "hero", "title": "John Doe Photography", "subtitle": "Capturing Moments", "backgroundImage": "https://via.placeholder.com/1200x600"},
                {"type": "gallery", "images": 6},
                {"type": "footer", "text": "© 2025 John Doe"}
            ]
        }
    }
    
    resp = requests.post(f"{BASE_URL}/wireframe", json=wireframe_payload)
    if resp.status_code == 200:
        data = resp.json()
        print("Response:", data["reply"])
        print("Files created:", list(data["files"].keys()))
    else:
        print("Error:", resp.text)

    # 2. Register Pages
    print_step("2. Registering Pages via Chat")
    chat_payload = {
        "message": "Please register the index.html page and create a new contact.html page with a form. Use the same navbar and footer components."
    }
    
    # This might take a while as the agent thinks
    print("Sending chat message... (this may take 10-20 seconds)")
    resp = requests.post(f"{BASE_URL}/chat", json=chat_payload)
    if resp.status_code == 200:
        data = resp.json()
        print("Response:", data["reply"])
        print("Files updated:", list(data["files"].keys()))
    else:
        print("Error:", resp.text)

    print_step("Demo Completed")
    print(f"Check the workspace at: {WORKSPACE_DIR.absolute()}")

if __name__ == "__main__":
    main()

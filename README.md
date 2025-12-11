# AutoWeb: Evolutionary Web-Building Agent

This project transforms the baseline WAA (Web-App Agent) into a **self-evolutionary system**. 
AutoWeb is not just a tool for building websites; it is a tool that **builds itself** to better serve the user.

The agent can:
- **Modify its own User Interface** based on user requests (e.g., "Add a file upload button", "Change to dark mode").
- **Build project structures** from natural-language instructions.
- **Generate and refine websites** through conversational iteration.
- **Manage reusable components** and multi-page architectures.
- **Convert wireframe sketches** (JSON) into HTML/CSS.
- **Maintain long-term context** with history compression.

---

## Table of Contents

1. [Evolutionary Features](#1-evolutionary-features)
2. [Architecture Overview](#2-architecture-overview)
3. [Installation](#3-installation)
4. [How to Run](#4-how-to-run)
5. [Self-Evolution Guide](#5-self-evolution-guide)
6. [Component & Page System](#6-component--page-system)
7. [Wireframe JSON Format](#7-wireframe-json-format)
8. [Running Tests](#8-running-tests)

---

## 1. Evolutionary Features

### Self-Modifying UI
The agent controls its own frontend configuration (`.waa/ui_config.json`). 
If you ask for a new input type (e.g., "I need a video upload field"), the agent will:
1.  Update its internal config.
2.  Rebuild the HTML/JS for the interface.
3.  Refresh the UI instantly.

**Dual Input System:** To prevent confusion, the interface provides separate inputs for:
*   **Website Instruction:** For building the target user project.
*   **UI Evolution Instruction:** For modifying the agent's own interface.

### Safety Reset Mechanism
If the agent accidentally breaks the UI or removes essential inputs, a **"Reset UI"** button is available to restore the default configuration immediately.

### Dynamic Styling
You can control the look and feel of the agent's interface via natural language.
*   "Make the UI dark mode."
*   "Change the primary button color to purple."

### Integrated Preview
The interface includes a live preview pane that renders the website being built in real-time.

### Robust Error Handling
The system wraps LLM calls in a robust error handling layer that catches API failures (Rate Limits, Auth Errors) and surfaces them as clean JSON responses to the UI, preventing server crashes.

---

## 2. Architecture Overview

Directory `waa/` contains the AutoWeb engine:

```text
waa/
├── agent.py            # Core agent logic (updated with UI tools)
├── ui_builder.py       # NEW: Generates the agent's UI from config
├── tools/
│   ├── ui.py           # NEW: Tools for self-modification
│   ├── component.py    # Component registry tools
│   ├── page.py         # Page registry tools
│   └── ...
├── layout_parser.py    # Wireframe to HTML converter
└── server_bridge.py    # Flask server for UI and API
```

**Evolutionary Loop:**
1.  User interacts via the web UI (`/ui`).
2.  Agent receives instruction + structured data.
3.  Agent decides to use standard tools (`fs.write`) OR evolutionary tools (`ui.update_config`).
4.  If `ui.update_config` is called, `ui_builder.py` regenerates the frontend.
5.  Browser refreshes to show the new capabilities.

---

## 3. Installation

1.  **Clone the repository**
2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```
3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set API Key**
    ```bash
    export GEMINI_API_KEY="your_key_here"
    # or on Windows PowerShell:
    # $env:GEMINI_API_KEY="your_key_here"
    ```

---

## 4. How to Run

### Start the Evolutionary Server
This starts the Flask server which hosts both the Agent API and the Self-Modifying UI.

```bash
python server_bridge.py
```

- **Access the UI:** Open `http://localhost:5000`
- **Preview Target Site:** The right-hand pane shows the live site.
- **API Endpoint:** `POST /chat`

### CLI Mode (Legacy)
You can still run the agent in CLI mode for headless operation:
```bash
python -m waa.cli "Create a simple portfolio page"
```

---

## 5. Self-Evolution Guide

The interface now separates concerns to ensure safety and clarity:

*   **Website Instruction Box**: Use this for standard web development tasks (e.g., "Create a contact form").
*   **UI Evolution Box**: Use this for modifying the tool itself (e.g., "Add a file upload input").

Try these prompts in the **UI Evolution Box** to see the agent modify itself:

**1. Add New Inputs**
> "I want to upload a logo image. Add a file upload button to this interface."

**2. Change Aesthetics**
> "Change the UI background to black and text to white."

**3. Repurpose the Tool**
> "I want to use this tool for writing blogs. Remove the wireframe input and add a 'Blog Title' field."

---

## 6. Component & Page System

### Components
- Stored in `components/`
- Registered in `.waa/components.json`
- Agent uses `component.register` to save reusable parts (navbars, footers).
- Client-side `loader.js` injects them dynamically.

### Pages
- Metadata in `.waa/pages.json`
- Agent uses `page.register` to track multi-page sites.

---

## 7. Wireframe JSON Format

The agent accepts structural JSON to scaffold sites quickly.
Paste this into the "Wireframe JSON" input (if enabled):

```json
{
  "sections": [
    { "type": "navbar", "links": ["Home", "About"] },
    { "type": "hero", "title": "Welcome", "subtitle": "Built by AutoWeb" },
    { "type": "grid", "items": ["Feature 1", "Feature 2"] }
  ]
}
```

---

## 8. Running Tests

Run the full test suite to verify all capabilities:

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_component_agent.py
```

2.  Agent parses intent
3.  LLM decides whether to call tools
4.  Filesystem updates
5.  Project structure evolves iteratively

-----

## 3\. Installation

### Create environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

### Set Gemini API key (Linux/macOS)

```bash
export GEMINI_API_KEY="YOUR_KEY"
```

### Set Gemini API key (Windows CMD)

```cmd
setx GEMINI_API_KEY "YOUR_KEY"
```

### Set Gemini API key (PowerShell)

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
```

-----

## 4\. How to Run AutoWeb

### CLI Mode (local agent loop)

```bash
python -m waa.cli -w targets/example_project --debug
```

### Interactive Chat Mode (browser UI)

Start the server:

```bash
python server_bridge.py
```

Then send requests via:
`POST http://localhost:5000/chat`

### Wireframe Layout Generation

`POST http://localhost:5000/wireframe`

**Example payload:**

```json
{
  "project": "autoweb_demo",
  "wireframe": [
    { "type": "navbar" },
    { "type": "hero", "title": "Hello", "subtitle": "World" },
    { "type": "grid", "items": ["A", "B", "C"] },
    { "type": "footer" }
  ]
}
```

-----

## 5\. Directory Structure

```text
mp_gemini/
├── waa/
├── tools/
├── layout_parser.py
├── agent.py
├── history.py
├── server_bridge.py
├── targets/
├── tests/
├── README.md
└── demo.py
```

-----

## 6\. Component System

Register a component:

```python
component.register(
    name="navbar",
    path="components/navbar.html",
    description="Top navigation bar"
)
```

List components:

```python
component.list()
```

Components are auto-loaded into pages via `loader.js`.

-----

## 7\. Page System

Register a page:

```python
page.register(
    name="about",
    route="/about",
    title="About Us",
    components=["navbar","footer"]
)
```

List pages:

```python
page.list()
```

Pages are tracked in `.waa/pages.json`.

-----

## 8\. Wireframe JSON Format

Wireframe blocks:

```json
[
  { "type": "navbar" },
  {
    "type": "hero",
    "title": "Welcome",
    "subtitle": "We build things"
  },
  {
    "type": "grid",
    "items": ["Card A","Card B","Card C"]
  },
  { "type": "footer" }
]
```

AutoWeb converts these into structured HTML and Tailwind CSS.

-----

## 9\. History Compression

When the conversation grows too long, older entries are replaced with summaries:

```json
{
  "tool_name": "fs.write",
  "summary": "Tool execution completed (details hidden)"
}
```

This preserves relevance while staying within token limits.

-----

## 10\. Running Tests

```bash
pytest -q
```

Tests cover:

  - wireframe → layout parsing
  - component system
  - page system
  - fs operations
  - todo system
  - conversation history compression

-----

## 11\. Demo Script

For an automated demonstration:

```bash
python demo.py
```

This simulates:

1.  Project creation
2.  Base webpage generation
3.  Component creation
4.  Page registration
5.  Wireframe layout synthesis

<!-- end list -->

```

### Next Steps
Would you like me to generate the `demo.py` script mentioned in the README to ensure your automated demonstration runs correctly?
```
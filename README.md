# AutoWeb: A Conversational Multimodal Web-Building Agent

This project extends the baseline WAA (Web-App Agent) from the Machine Programming course into a fully interactive, multimodal, component-based web-building system.
AutoWeb can:

- Build project structures from natural-language instructions
- Generate and refine websites through conversational iteration
- Manage reusable components across multiple pages
- Maintain structured page metadata
- Convert wireframe-style JSON sketches into HTML/CSS
- Maintain long-term context with history compression

This repository provides a complete end-to-end toolchain for intelligent web synthesis and modification.

---

## Table of Contents

1. [Features](#1-features)
2. [Architecture Overview](#2-architecture-overview)
3. [Installation](#3-installation)
4. [How to Run AutoWeb](#4-how-to-run-autoweb)
   - CLI Mode
   - Interactive Chat Mode
   - Wireframe Layout Generation
5. [Directory Structure](#5-directory-structure)
6. [Component System](#6-component-system)
7. [Page System](#7-page-system)
8. [Wireframe JSON Format](#8-wireframe-json-format)
9. [History Compression](#9-history-compression)
10. [Running Tests](#10-running-tests)
11. [Demo Script](#11-demo-script)

---

## 1. Features

### Conversational Iteration
Modify existing webpages through natural language without regenerating from scratch.
AutoWeb inspects and edits code incrementally via tool calls.

### Component-Based Architecture
- Components stored in `components/`
- Registry in `.waa/components.json`
- Tools: `component.register`, `component.list`
- Auto-inclusion via Loader.js pattern

### Multi-Page Website Support
- Per-page metadata stored in `.waa/pages.json`
- Tools: `page.register`, `page.list`
- AutoWeb can build navigable multi-page sites

### Multimodal Wireframe Input
Convert structural JSON wireframes into HTML/CSS through the `/wireframe` REST endpoint.

AutoWeb currently supports common layout primitives:
- navbar
- hero section
- grid layouts
- text blocks
- footer

### History Compression
Older LLM interactions are summarized automatically to prevent context overflow.

### Extensive Test Coverage
Tests cover:
- components
- pages
- wireframe parsing
- history compression
- baseline WAA tools

---

## 2. Architecture Overview

Directory `waa/` contains the AutoWeb engine:

```text
waa/
├── agent.py
├── history.py
├── tools/
│   ├── fs.py
│   ├── server.py
│   ├── todo.py
│   ├── component.py
│   ├── page.py
│   └── ...
├── layout_parser.py
├── llm/
│   ├── base.py
│   └── gemini.py
└── server_bridge.py
````

**High-level flow:**

1.  User sends instruction
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
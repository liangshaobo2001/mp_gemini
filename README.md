# Interactive Web-Building Agent (WAA++)

This project extends the baseline WAA (Web-App Agent) from the Machine Programming course into a fully interactive, multimodal, component-based web-building system.  
The agent can:

- Build project structures from natural-language instructions  
- Generate and refine websites through conversational iteration  
- Manage reusable components across multiple pages  
- Maintain structured page metadata  
- Convert wireframe-style JSON sketches into HTML/CSS  
- Maintain long-term context with history compression  

This repository provides a complete end-to-end toolchain for intelligent web synthesis and modification.

## Table of Contents

1. Features  
2. Architecture Overview  
3. Installation  
4. How to Run the Agent  
   - CLI Mode  
   - Interactive Chat Mode  
   - Wireframe Layout Generation  
5. Directory Structure  
6. Component System  
7. Page System  
8. Wireframe JSON Format  
9. History Compression  
10. Running Tests  
11. Demo Script  

## Features

### Conversational Iteration  
Modify existing webpages through natural language without regenerating from scratch.  
The agent inspects and edits code incrementally via tool calls.

### Component-Based Architecture
- Components stored in `components/`  
- Registry in `.waa/components.json`  
- Tools: `component.register`, `component.list`  
- Loader.js pattern to include components automatically

### Multi-Page Website Support
- Per-page metadata stored in `.waa/pages.json`  
- Tools: `page.register`, `page.list`  
- System prompt instructs the agent to build navigable multi-page sites

### Multimodal Wireframe Input
Convert structural JSON wireframes into HTML/CSS through the `/wireframe` endpoint.

### History Compression
Older LLM interactions are automatically summarized to prevent context overflow.

### Extensive Test Coverage
Includes tests for components, pages, wireframe parsing, history compression, and baseline WAA tools.

## Architecture Overview

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
├── server_bridge.py        
└── ...

## Installation

1. Create environment:
```
python3 -m venv venv
source venv/bin/activate
```

2. Install requirements:
```
pip install -r requirements.txt
```

3. Set Gemini API key:
```
export GEMINI_API_KEY="YOUR_KEY"
```

## How to Run the Agent

### CLI Mode
```
python -m waa.cli -w targets/example_project --debug
```

### Interactive Chat Mode
```
python server_bridge.py
```

### Wireframe Layout Generation
```
POST http://localhost:5000/wireframe
```

## Directory Structure
mp_gemini/
  waa/
    tools/
    layout_parser.py
    agent.py
    history.py
    server_bridge.py
  targets/
  tests/
  README.md
  demo.py

## Component System

Register:
```
component.register(name="navbar", path="components/navbar.html", description="Top navigation bar")
```

List:
```
component.list()
```

## Page System

Register:
```
page.register(name="about", route="/about", title="About Us", components=["navbar","footer"])
```

List:
```
page.list()
```

## Wireframe JSON Format
```
[
  { "type": "navbar" },
  { "type": "hero", "title": "Hello", "subtitle": "World" },
  { "type": "grid", "items": ["A","B","C"] },
  { "type": "footer" }
]
```

## History Compression
Old entries:
```
{
  "tool_name": "fs.write",
  "summary": "Tool execution completed (details hidden)"
}
```

## Running Tests
```
pytest -q
```

## Demo Script
```
python demo.py
```


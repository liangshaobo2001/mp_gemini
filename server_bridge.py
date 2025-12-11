import os
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

# Import your actual Agent code
from waa.agent import Agent
from waa.history import UserInstruction, ToolCallResult
from waa.layout_parser import LayoutParser
from waa.llm import LLMError
from waa.ui_builder import UIBuilder

app = Flask(__name__)
CORS(app)  # Enable React to talk to this server

# --- CONFIGURATION ---
# We will use a dedicated demo folder for the web interface
WORKING_DIR = Path("targets/autoweb_demo")
API_KEY = os.environ.get("GEMINI_API_KEY")

# Global Instances
active_agent = None
ui_builder = None

def setup_demo_environment():
    """Ensures the demo directory and config exist."""
    global ui_builder
    if not WORKING_DIR.exists():
        WORKING_DIR.mkdir(parents=True, exist_ok=True)
    
    waa_dir = WORKING_DIR / ".waa"
    waa_dir.mkdir(exist_ok=True)

    # Initialize UI Builder
    ui_builder = UIBuilder(WORKING_DIR)
    ui_builder.generate_ui() # Ensure UI exists on startup

    # create minimal config if missing
    config_path = waa_dir / "config.json"
    if not config_path.exists():
        config = {
            "llm_type": "gemini",
            "model": "gemini-2.5-pro",
            "max_turns": 100,
            "allowed_tools": [
                "fs.write", "fs.read", "fs.edit", "fs.delete", 
                "fs.mkdir", "fs.ls", "fs.tree", 
                "npm.init",
                "ui.update_config", "ui.rebuild",
                "page.register", "page.list",
                "component.register", "component.list"
            ]
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    
    # create dummy instruction if missing (required by Agent.initialize)
    instr_path = waa_dir / "instruction.md"
    if not instr_path.exists():
        with open(instr_path, "w") as f:
            f.write("Interactive Web Session")

def get_file_state():
    """Scans the working dir to send files to the Frontend."""
    files = {}
    # Recursively find all text files (limit to standard web types)
    extensions = {'.html', '.css', '.js', '.jsx', '.json', '.md', '.txt'}
    
    for path in WORKING_DIR.rglob('*'):
        if path.is_file() and path.suffix in extensions:
            # Skip hidden files/dirs (like .waa or .git)
            if any(part.startswith('.') for part in path.parts):
                continue
                
            try:
                rel_path = path.relative_to(WORKING_DIR).as_posix()
                files[rel_path] = path.read_text(encoding='utf-8')
            except Exception:
                pass # Skip binary or unreadable files
    return files

@app.route('/ui')
def serve_ui_index():
    setup_demo_environment()
    return send_from_directory(WORKING_DIR / "ui", "index.html")

@app.route('/ui/<path:filename>')
def serve_ui_files(filename):
    return send_from_directory(WORKING_DIR / "ui", filename)

@app.route('/ui-config', methods=['GET', 'POST'])
def handle_ui_config():
    setup_demo_environment()
    if request.method == 'GET':
        ui_builder.load_config() # Refresh from disk
        return jsonify(ui_builder.config)
    else:
        new_config = request.json
        ui_builder.config = new_config
        ui_builder._save_config()
        ui_builder.generate_ui()
        return jsonify({"success": True, "config": ui_builder.config})

@app.route('/ui-reset', methods=['POST'])
def handle_ui_reset():
    setup_demo_environment()
    ui_builder.reset_config()
    return jsonify({"success": True, "message": "UI reset to default"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        global active_agent
        
        # 1. Initialize Agent if not running
        if not active_agent:
            if not API_KEY:
                return jsonify({"success": False, "error": {"type": "ConfigError", "message": "GEMINI_API_KEY not found in environment."}}), 500
            
            setup_demo_environment()
            active_agent = Agent(WORKING_DIR, debug=True)
            active_agent.initialize()
            print("--- Agent Initialized for Web Session ---")

        data = request.json
        
        # Handle structured input data
        raw_inputs = data.get('data', {})
        
        website_instruction = raw_inputs.get('message', '')
        ui_instruction = raw_inputs.get('ui_instruction', '')
        
        final_prompt = ""
        if website_instruction:
            final_prompt += f"[WEBSITE INSTRUCTION]: {website_instruction}\n"
        if ui_instruction:
            final_prompt += f"[UI EVOLUTION REQUEST]: {ui_instruction}\n"
            
        # Add other inputs (wireframes, etc)
        other_inputs = {k:v for k,v in raw_inputs.items() if k not in ['message', 'ui_instruction', 'instruction']}
        if other_inputs:
            final_prompt += f"\n[ADDITIONAL INPUTS]: {json.dumps(other_inputs, indent=2)}"
            
        if not final_prompt:
             # Fallback if app.js sent something else
             final_prompt = data.get('message', 'No instruction provided.')

        # 2. Inject User Message into History
        print(f"\n[User]: {final_prompt}")
        user_entry = UserInstruction(final_prompt)
        active_agent.history.append(user_entry)
        active_agent.logger.log_user_instruction(final_prompt)

        # 3. Run the Agent Loop (The "Step" Logic)
        # We loop until the agent produces a text response or terminates.
        # We allow up to 15 sub-turns (tools) before forcing a break to avoid timeouts.
        response_text = ""
        sub_turns = 0
        MAX_SUB_TURNS = 15

        while sub_turns < MAX_SUB_TURNS:
            sub_turns += 1
            
            # Calculate turn number based on history length
            current_turn_idx = len(active_agent.history)
            
            # Query LLM
            response_entry = active_agent.query_llm(current_turn_idx)
            
            # Handle Termination
            if response_entry.is_termination():
                response_text = "I have finished the task."
                break
                
            # Handle Tool Calls
            if response_entry.is_tool_call():
                # If it's a tool, execute it and CONTINUE the loop 
                # (The agent needs to see the tool result to decide what to do next)
                active_agent.execute_tool(response_entry.response)
                continue 
            
            # Handle Text Response (The Agent is talking to the user)
            response_text = response_entry.response
            break

        # 4. Return Response + Updated Files
        current_files = get_file_state()
        
        return jsonify({
            "success": True,
            "reply": response_text,
            "files": current_files
        })

    except LLMError as e:
        app.logger.exception("LLM Error in /chat")
        return jsonify({
            "success": False,
            "error": {
                "type": e.error_type,
                "message": str(e),
                "retry_after": e.retry_after,
            }
        }), 200

    except Exception as e:
        app.logger.exception("Unexpected Error in /chat")
        return jsonify({
            "success": False,
            "error": {
                "type": "ServerError",
                "message": "An unexpected server error occurred. Please check server logs."
            }
        }), 500

@app.route('/wireframe', methods=['POST'])
def wireframe():
    try:
        global active_agent
        
        # 1. Initialize Agent if not running
        if not active_agent:
            if not API_KEY:
                return jsonify({"success": False, "error": {"type": "ConfigError", "message": "GEMINI_API_KEY not found in environment."}}), 500
            
            setup_demo_environment()
            active_agent = Agent(WORKING_DIR, debug=True)
            active_agent.initialize()
            print("--- Agent Initialized for Wireframe Session ---")

        data = request.json
        user_message = data.get('message', 'Generate site from wireframe')
        wireframe_data = data.get('wireframe', {})

        # 2. Parse Wireframe
        parser = LayoutParser()
        generated_files = parser.parse_wireframe(wireframe_data)

        # 3. Write files to workspace
        for filename, content in generated_files.items():
            file_path = WORKING_DIR / filename
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Log tool execution manually to history so agent knows files exist
            # We simulate a tool call for each file write
            active_agent.history.append(
                ToolCallResult(
                    "fs.write", 
                    {"path": filename, "content": "..." }, # Truncate content in history to save tokens
                    f"File {filename} written successfully.", 
                    None
                )
            )

        # 4. Inject User Message
        print(f"\n[User Wireframe]: {user_message}")
        user_entry = UserInstruction(f"{user_message}\n[System: I have processed the wireframe and created initial files: {', '.join(generated_files.keys())}]")
        active_agent.history.append(user_entry)
        active_agent.logger.log_user_instruction(user_message)

        # 5. Return Updated Files (No LLM query needed immediately, or we could trigger one)
        current_files = get_file_state()
        
        # Get registered components and pages
        components = []
        pages = []
        
        try:
            comp_reg = WORKING_DIR / ".waa" / "components.json"
            if comp_reg.exists():
                with open(comp_reg, 'r') as f:
                    components = list(json.load(f).keys())
                    
            page_reg = WORKING_DIR / ".waa" / "pages.json"
            if page_reg.exists():
                with open(page_reg, 'r') as f:
                    pages = list(json.load(f).keys())
        except:
            pass

        return jsonify({
            "success": True,
            "reply": "I have generated the initial layout based on your wireframe. You can now ask me to refine it.",
            "files": current_files,
            "components": components,
            "pages": pages,
            "next_steps": [
                "Review the generated layout.",
                "Ask me to add more pages using 'page.register'.",
                "Ask me to extract sections into reusable components."
            ]
        })

    except LLMError as e:
        app.logger.exception("LLM Error in /wireframe")
        return jsonify({
            "success": False,
            "error": {
                "type": e.error_type,
                "message": str(e),
                "retry_after": e.retry_after,
            }
        }), 200

    except Exception as e:
        app.logger.exception("Unexpected Error in /wireframe")
        return jsonify({
            "success": False,
            "error": {
                "type": "ServerError",
                "message": "An unexpected server error occurred. Please check server logs."
            }
        }), 500

# --- STATIC FILE SERVING FOR GUI ---

@app.route('/')
def serve_index():
    return redirect('/ui')

@app.route('/preview')
def serve_preview_index():
    return send_from_directory(WORKING_DIR, 'index.html')

@app.route('/preview/<path:filename>')
def serve_preview_assets(filename):
    return send_from_directory(WORKING_DIR, filename)

@app.route('/<path:filename>')
def serve_root_assets(filename):
    # Fallback for assets requested from root (like style.css if base href is not set)
    if (WORKING_DIR / filename).exists():
        return send_from_directory(WORKING_DIR, filename)
    return "File not found", 404

if __name__ == '__main__':
    print(f"AutoWeb Bridge running on http://localhost:5000")
    print(f"Target Directory: {WORKING_DIR.resolve()}")
    app.run(host='0.0.0.0', port=5000)
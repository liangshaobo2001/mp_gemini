import os
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import your actual Agent code
from waa.agent import Agent
from waa.history import UserInstruction

app = Flask(__name__)
CORS(app)  # Enable React to talk to this server

# --- CONFIGURATION ---
# We will use a dedicated demo folder for the web interface
WORKING_DIR = Path("targets/autoweb_demo")
API_KEY = os.environ.get("GEMINI_API_KEY")

# Global Agent Instance (Single Session)
active_agent = None

def setup_demo_environment():
    """Ensures the demo directory and config exist."""
    if not WORKING_DIR.exists():
        WORKING_DIR.mkdir(parents=True, exist_ok=True)
    
    waa_dir = WORKING_DIR / ".waa"
    waa_dir.mkdir(exist_ok=True)

    # create minimal config if missing
    config_path = waa_dir / "config.json"
    if not config_path.exists():
        config = {
            "llm_type": "gemini",
            "model": "gemini-1.5-flash",
            "max_turns": 100,
            "allowed_tools": [
                "fs.write", "fs.read", "fs.edit", "fs.delete", 
                "fs.mkdir", "fs.ls", "fs.tree", 
                "npm.init" # Allow npm init for setup
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

@app.route('/chat', methods=['POST'])
def chat():
    global active_agent
    
    # 1. Initialize Agent if not running
    if not active_agent:
        if not API_KEY:
            return jsonify({"reply": "Error: GEMINI_API_KEY not found in environment.", "files": {}}), 500
        
        setup_demo_environment()
        active_agent = Agent(WORKING_DIR, debug=True)
        active_agent.initialize()
        print("--- Agent Initialized for Web Session ---")

    data = request.json
    user_message = data.get('message', '')

    # 2. Inject User Message into History
    print(f"\n[User]: {user_message}")
    user_entry = UserInstruction(user_message)
    active_agent.history.append(user_entry)
    active_agent.logger.log_user_instruction(user_message)

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
        "reply": response_text,
        "files": current_files
    })

if __name__ == '__main__':
    print(f"AutoWeb Bridge running on http://localhost:5000")
    print(f"Target Directory: {WORKING_DIR.resolve()}")
    app.run(host='0.0.0.0', port=5000)
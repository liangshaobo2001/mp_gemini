import json
import os
from pathlib import Path
from typing import List, Dict, Any

class UIBuilder:
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.waa_dir = self.working_dir / ".waa"
        self.ui_dir = self.working_dir / "ui"
        self.config_path = self.waa_dir / "ui_config.json"
        
        self._ensure_dirs()
        self.load_config()

    def _ensure_dirs(self):
        if not self.waa_dir.exists():
            self.waa_dir.mkdir(parents=True, exist_ok=True)
        if not self.ui_dir.exists():
            self.ui_dir.mkdir(parents=True, exist_ok=True)
        (self.ui_dir / "components").mkdir(exist_ok=True)

    def load_config(self):
        if not self.config_path.exists():
            self.config = {
                "title": "AutoWeb Evolutionary UI",
                "style": {
                    "background_color": "#f4f4f9",
                    "text_color": "#333333",
                    "primary_color": "#007bff",
                    "font_family": "sans-serif"
                },
                "inputs": [
                    {"type": "text", "id": "message", "label": "Website Instruction", "placeholder": "Describe what you want to build for the target website..."},
                    {"type": "text", "id": "ui_instruction", "label": "UI Evolution Instruction", "placeholder": "Describe how you want to modify this tool/interface..."},
                    {"type": "textarea", "id": "wireframe_json", "label": "Wireframe JSON", "placeholder": "Paste wireframe JSON here..."}
                ]
            }
            self._save_config()
        else:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            # Ensure style exists for old configs
            if "style" not in self.config:
                self.config["style"] = {
                    "background_color": "#f4f4f9",
                    "text_color": "#333333",
                    "primary_color": "#007bff",
                    "font_family": "sans-serif"
                }

    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def reset_config(self):
        if self.config_path.exists():
            os.remove(self.config_path)
        self.load_config()
        self.generate_ui()

    def add_input(self, input_def: Dict[str, Any]):
        """
        Add a new input definition to the config.
        Example: {"type": "file", "id": "wireframe_image", "label": "Upload Sketch", "accept": "image/*"}
        """
        # Check if id exists, replace if so
        for i, inp in enumerate(self.config["inputs"]):
            if inp["id"] == input_def["id"]:
                self.config["inputs"][i] = input_def
                self._save_config()
                return
        
        self.config["inputs"].append(input_def)
        self._save_config()

    def remove_input(self, input_id: str):
        self.config["inputs"] = [i for i in self.config["inputs"] if i["id"] != input_id]
        self._save_config()

    def generate_ui(self):
        """
        Generates index.html, style.css, and app.js based on current config.
        """
        self._generate_html()
        self._generate_css()
        self._generate_js()
        self._generate_components()

    def _generate_components(self):
        # Generate standalone component files for reference/usage
        for inp in self.config["inputs"]:
            comp_path = self.ui_dir / "components" / f"input_{inp['type']}_{inp['id']}.html"
            with open(comp_path, 'w') as f:
                f.write(self._render_input_html(inp))

    def _render_input_html(self, inp: Dict[str, Any]) -> str:
        inp_type = inp.get("type", "text")
        inp_id = inp.get("id", "unknown")
        label = inp.get("label", inp_id)
        placeholder = inp.get("placeholder", "")
        
        html = f'<div class="form-group" data-id="{inp_id}" data-type="{inp_type}">\n'
        html += f'  <label for="{inp_id}">{label}</label>\n'
        
        if inp_type == "textarea":
            html += f'  <textarea id="{inp_id}" placeholder="{placeholder}"></textarea>\n'
        elif inp_type == "file":
            accept = inp.get("accept", "*/*")
            html += f'  <input type="file" id="{inp_id}" accept="{accept}">\n'
        elif inp_type == "select":
            options = inp.get("options", [])
            html += f'  <select id="{inp_id}">\n'
            for opt in options:
                html += f'    <option value="{opt}">{opt}</option>\n'
            html += '  </select>\n'
        else:
            # Default text-like input
            html += f'  <input type="{inp_type}" id="{inp_id}" placeholder="{placeholder}">\n'
            
        html += '</div>'
        return html

    def _generate_html(self):
        inputs_html = "\n".join([self._render_input_html(inp) for inp in self.config["inputs"]])
        
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.get('title', 'AutoWeb')}</title>
    <link rel="stylesheet" href="/ui/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{self.config.get('title', 'AutoWeb')}</h1>
            <p>Evolutionary Interface</p>
        </header>
        
        <main>
            <div class="panel input-panel">
                <h2>Inputs</h2>
                <div id="dynamic-inputs">
                    {inputs_html}
                </div>
                <div class="controls">
                    <button id="submit-btn">Process Request</button>
                    <button id="reset-btn" style="margin-top: 0.5rem; background: #6c757d;">Reset UI</button>
                </div>
                <div id="status-msg" class="hidden"></div>
            </div>
            
            <div class="panel output-panel">
                <h2>Agent Response</h2>
                <div id="chat-history"></div>
            </div>
            
            <div class="panel preview-panel">
                <div class="preview-header">
                    <h2>Live Preview</h2>
                    <button id="refresh-btn">Refresh</button>
                </div>
                <iframe id="preview-frame" src="/preview"></iframe>
            </div>
        </main>
    </div>
    <script src="/ui/app.js"></script>
</body>
</html>"""
        with open(self.ui_dir / "index.html", 'w') as f:
            f.write(content)

    def _generate_css(self):
        style = self.config.get("style", {})
        bg = style.get("background_color", "#f4f4f9")
        text = style.get("text_color", "#333")
        primary = style.get("primary_color", "#007bff")
        font = style.get("font_family", "sans-serif")

        content = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: {font}; background: {bg}; color: {text}; height: 100vh; display: flex; flex-direction: column; }}
.container {{ flex: 1; display: flex; flex-direction: column; padding: 1rem; gap: 1rem; max-width: 1400px; margin: 0 auto; width: 100%; }}
header {{ padding-bottom: 1rem; border-bottom: 1px solid #ddd; }}
main {{ flex: 1; display: grid; grid-template-columns: 300px 1fr 1fr; gap: 1rem; overflow: hidden; }}
.panel {{ background: white; border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; box-shadow: 0 2px 5px rgba(0,0,0,0.05); overflow: hidden; }}
h2 {{ font-size: 1.1rem; margin-bottom: 1rem; color: #555; border-bottom: 1px solid #eee; padding-bottom: 0.5rem; }}

/* Inputs */
.input-panel {{ overflow-y: auto; }}
.form-group {{ margin-bottom: 1rem; }}
.form-group label {{ display: block; margin-bottom: 0.3rem; font-weight: 500; font-size: 0.9rem; }}
.form-group input, .form-group textarea, .form-group select {{ width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; }}
.form-group textarea {{ min-height: 100px; resize: vertical; }}
.controls button {{ width: 100%; padding: 0.75rem; background: {primary}; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }}
.controls button:hover {{ opacity: 0.9; }}
.controls button:disabled {{ background: #ccc; }}

/* Chat */
.output-panel {{ overflow-y: auto; }}
#chat-history {{ flex: 1; display: flex; flex-direction: column; gap: 0.5rem; overflow-y: auto; }}
.message {{ padding: 0.8rem; border-radius: 6px; font-size: 0.9rem; line-height: 1.4; }}
.message.user {{ background: #e3f2fd; align-self: flex-end; max-width: 90%; color: #333; }}
.message.assistant {{ background: #f1f1f1; align-self: flex-start; max-width: 90%; color: #333; }}
.message.system {{ font-size: 0.8rem; color: #888; text-align: center; width: 100%; }}

/* Preview */
.preview-panel {{ padding: 0; }}
.preview-header {{ padding: 0.5rem 1rem; background: #f8f9fa; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; }}
.preview-header h2 {{ margin: 0; border: none; padding: 0; }}
#preview-frame {{ flex: 1; border: none; width: 100%; height: 100%; }}

/* Utilities */
.hidden {{ display: none; }}
.error {{ color: #dc3545; margin-top: 0.5rem; font-size: 0.9rem; }}
"""
        with open(self.ui_dir / "style.css", 'w') as f:
            f.write(content)

    def _generate_js(self):
        # We need to dynamically gather inputs based on config
        input_ids = [inp["id"] for inp in self.config["inputs"]]
        
        js_content = f"""
document.addEventListener('DOMContentLoaded', () => {{
    const submitBtn = document.getElementById('submit-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const resetBtn = document.getElementById('reset-btn');
    const statusMsg = document.getElementById('status-msg');
    const chatHistory = document.getElementById('chat-history');
    
    submitBtn.addEventListener('click', handleSubmit);
    refreshBtn.addEventListener('click', () => {{
        document.getElementById('preview-frame').src = '/preview?t=' + Date.now();
    }});
    
    if (resetBtn) {{
        resetBtn.addEventListener('click', async () => {{
            if (confirm('Are you sure you want to reset the UI to default? This will remove custom inputs.')) {{
                try {{
                    await fetch('/ui-reset', {{ method: 'POST' }});
                    window.location.reload();
                }} catch (e) {{
                    alert('Failed to reset UI');
                }}
            }}
        }});
    }}

    async function handleSubmit() {{
        submitBtn.disabled = true;
        statusMsg.classList.add('hidden');
        
        // Gather data dynamically
        const payload = {{}};
        const inputIds = {json.dumps(input_ids)};
        
        for (const id of inputIds) {{
            const el = document.getElementById(id);
            if (!el) continue;
            
            if (el.type === 'file') {{
                // For now, we just send the filename or base64 if we implemented that.
                // To keep it simple for this iteration, we'll just send the name.
                // Real implementation would read the file.
                if (el.files.length > 0) {{
                    payload[id] = el.files[0].name; 
                    // In a real app, you'd readAsDataURL here
                }}
            }} else {{
                payload[id] = el.value;
            }}
        }}
        
        // Construct message for the agent
        // We prioritize 'message' or 'instruction' fields if they exist
        let userMessage = payload['message'] || payload['instruction'] || JSON.stringify(payload);
        
        appendMessage('user', userMessage);
        
        try {{
            // Decide endpoint based on payload content? 
            // For now, we route everything to /chat but include the full payload in the body
            // The backend agent will need to see this extra data.
            
            const response = await fetch('/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    message: userMessage,
                    data: payload // Send all inputs as structured data
                }})
            }});
            
            const data = await response.json();
            
            if (data.success) {{
                appendMessage('assistant', data.reply);
                if (data.files) refreshBtn.click();
            }} else {{
                appendMessage('system', 'Error: ' + (data.error ? data.error.message : 'Unknown error'));
            }}
            
        }} catch (e) {{
            console.error(e);
            appendMessage('system', 'Network Error');
        }} finally {{
            submitBtn.disabled = false;
        }}
    }}
    
    function appendMessage(role, text) {{
        const div = document.createElement('div');
        div.className = 'message ' + role;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }}
}});
"""
        with open(self.ui_dir / "app.js", 'w') as f:
            f.write(js_content)

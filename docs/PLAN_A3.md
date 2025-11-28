
# Assignment 3 — Execution Plan (WAA)

This file is the action checklist we’ll follow. Mirror of the plan we discussed.

## 0) Environment & Smoke Checks
- [ ] `python -m venv .venv && source .venv/bin/activate`
- [ ] `pip install -r requirements.txt && pip install -e .`
- [ ] Verify Node tooling: `node -v` (>= 18), `npm -v` (>= 9), `npx -v` (>= 9)
- [ ] Dry-run tests (expect failures now): `python tests/test_fs_mock_agent.py`

**Done when**: `waa --help` shows CLI usage.

## 1) Part 1 — Agent Core
- [ ] `waa/agent.py`: implement
  - [ ] `initialize_tool_registry()` — register *allowed* tools including fs/todo/server/testing.
  - [ ] `load_system_prompt()` — include protocols (`<tool_call>{...}</tool_call>`, `<terminate>`), tool descriptions, high-level strategy; append `SystemPrompt` to history.
  - [ ] `initialize_instruction()` — read `.waa/instruction.md`, append `UserInstruction` to history.
  - [ ] `query_llm()` — call `self.llm.generate(messages)`, append `LLMResponse`, log query/response.
  - [ ] `execute_tool()` — validate args via `tool.schema.validate()`, execute, catch errors, append `ToolCallResult`.
  - [ ] `run()` — main loop with termination and tool-call handling; log termination.
- [ ] Pass: `python tests/test_server_mock_agent.py`

## 2) Part 2 — Tools
### 2.1 File System Tools `waa/tools/fs.py`
- [ ] Implement tools: `fs.write/read/edit/delete/mkdir/rmdir/ls/tree`
- [ ] Enforce security: (1) path within working dir; (2) protected files deny writes/edits/deletes.
- [ ] Pass: `python tests/test_fs_mock_agent.py`

### 2.2 TODO Tools `waa/tools/todo.py`
- [ ] Implement: `todo.add/list/complete/remove`, data at `.waa/todo.json`
- [ ] Item schema: `{id, description, status, created_at, completed_at?}`
- [ ] Pass: `python tests/test_todo_mock_agent.py`

## 3) Part 3 — Build Web Apps
- [ ] Personal website (`targets/personal_website/`) via `waa --working-dir ... --debug`
- [ ] Chat room (`targets/chat_room/`) — pass API (Supertest) + UI (Playwright) tests
- [ ] Creative app (`targets/<idea>/`) — scaffold `.waa/config.json` & `instruction.md`
- [ ] Report `report.pdf` with screenshots & notes

## 4) Logging & Rerun Hygiene
- [ ] Ensure logger calls: `log_system_prompt`, `log_user_instruction`, `log_llm_query`, `log_llm_response`, `log_tool_call`, `log_tool_result`, `log_termination`
- [ ] Delete `.waa/agent.log` before re-runs

## 5) Packaging
- [ ] Update `package_submission.sh` to include report & acknowledgements if needed
- [ ] Run to produce `submission.zip`

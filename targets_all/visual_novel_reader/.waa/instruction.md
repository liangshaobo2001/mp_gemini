# Visual Novel Reader — Build Instructions

Build a **single-page visual novel reader** using Node.js + Express (backend only for static hosting) and a static frontend (HTML/CSS/JS). The app displays one sentence at a time from a story, with a text box at the bottom. On click, it advances to the next sentence.

## Core requirements

- **Files & structure**
  - Backend: `index.js` (Express). Serve static files from `public/` and send `public/index.html` on `/`.
  - Frontend (in `public/`):
    - `index.html` — main page with a bottom text box UI.
    - `style.css` — simple, black & white, clean, planar design. Black background; white text.
    - `script.js` — logic to load sentences and handle input.
- **Story ingestion**
  - Read `.waa/story.txt` at build time (tool calls) and **embed** the parsed sentences into `public/script.js` as a JS array `const STORY = [...]`.
  - Sentence splitting: split on `.`, `!`, `?` (keep punctuation), trim whitespace, drop empty entries.
- **Interaction**
  - On first load, show the first sentence in a bottom “dialogue box”.
  - Clicking anywhere on the bottom box (or pressing `Space`/`Enter`) advances to the next sentence.
  - Provide a minimal top bar with: “Restart” button (go back to sentence 0).
  - If user reaches the end, show a subtle “The End. Restart?” prompt.
- **UI**
  - Full-viewport black background (no images needed).
  - Bottom dialogue box spans page width, ~30–35% viewport height, white text, generous line-height, slight rounded corners.
  - Keep typography clean; no fancy fonts required.
- **No tests are required** for this creative project; just build and run. (If you add tests, place them under `tests/`.)

## WAA Build Protocol (MANDATORY)

1) **Inspect workspace**
   - Use `fs.ls`/`fs.tree` to check for `public/` and required files.
   - If `public/*` already exists, **do not** overwrite using `fs.write`; use `fs.read` then `fs.edit`.

2) **Create missing files**
   - If `public/` is missing: `fs.mkdir` to create it.
   - Create `index.js` with an Express server:

     const express = require('express');
     const path = require('path');
     const app = express();
     const port = 3000;
     app.use(express.static(path.join(__dirname, 'public')));
     app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));
     app.listen(port, () => console.log(`Server is running on http://localhost:${port}`));

   - Create `public/index.html` with:
     * `<title>Visual Novel Reader</title>`
     * A top bar with a **Restart** button (id: `restart-btn`)
     * A main area (can be empty black)
     * A bottom dialogue box (id: `dialogue-box`) that shows the sentence text inside `<p id="line">...</p>`
     * Link `<link rel="stylesheet" href="style.css">` and `<script src="script.js"></script>`

   - Create `public/style.css` with black background and white text:
     * `body { background:#000; color:#fff; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin:0; }`
     * A top bar (id `topbar`) fixed, minimal height; a bottom box (id `dialogue-box`) fixed at bottom, 30–35vh, with padding, rounded corners, subtle border.
     * Make sure content remains readable at typical desktop sizes.

3) **Story ingestion → script.js**
   - `fs.read` `.waa/story.txt`, split into sentences, and generate:
     ```js
     const STORY = [ "Sentence 1.", "Sentence 2!", "Sentence 3?" ];
     ```
   - Add logic:
     * `let i = 0;` render function updates `#line` to `STORY[i]`.
     * Click on `#dialogue-box` or press `Space`/`Enter` → advance to next sentence if any; otherwise show “The End. Restart?”
     * `#restart-btn` → reset to i=0 and render.
     * Keyboard listeners should not scroll the page.
   - Make sure this runs after DOMContentLoaded.

4) **Run & verify**
   - Start server with `npm.start`.
   - If the server fails to start, check with `npm.logs`, fix, and retry.
   - Confirm that `http://localhost:3000` shows the app and clicking advances text.

5) **Safety**
   - Never write to files listed in `protected_files`.
   - When a file exists, prefer `fs.read` → `fs.edit` over `fs.write`.

## Acceptance checklist

- Visiting `/` serves `public/index.html`.
- Black background, white text, clean layout.
- Bottom dialogue box shows the first sentence on load.
- Clicking the box (or `Space`/`Enter`) advances one sentence at a time.
- `Restart` sets back to sentence 0.
- No external assets or frameworks are required.


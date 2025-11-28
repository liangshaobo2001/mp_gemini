# Visual Novel Reader — Build Instructions

Build a single-page visual novel reader that displays one sentence at a time at the bottom “dialogue bar.” 
On click/tap (or a “Next” button), show the next sentence. 
Use a **static background image for the whole experience**.

## Content
- Load the story from a local text file `story.txt` (UTF-8). 
- Split into sentences with a simple regex that handles `.`, `?`, `!` followed by whitespace/newline. 
- Trim whitespace; ignore empty fragments.

## Save / Continue
- **Save progress** (current sentence index) in `localStorage` under the key `vn_progress`.
- On page load:
  - If a saved index exists and is within range, show a “Continue” button that jumps to that sentence index.
  - Otherwise start at sentence 0.
- Provide a “Restart” button that clears `vn_progress` and returns to sentence 0.
- Persist progress every time the user advances.

## UI / UX
- Minimal, black & white, planar UI.
- Full-screen static background image (cover, fixed). 
- Dialogue bar pinned to bottom with the current sentence text and controls (Next / Continue / Restart).
- Use semantic HTML; styles in `public/style.css`; behavior in `public/script.js`.

## Background Image
- Put a text SVG at `public/assets/background.svg` (simple gradient or subtle pattern). 
- CSS should set: 
  `body { background: #000 url('/assets/background.svg') center / cover fixed no-repeat; }`
- If you add a gradient in CSS too, that’s fine as a fallback.

## Project Layout (must exist)
- `index.js` — Express server that serves static files from `public`, and `index.html` at `/`.
- `public/index.html` — page shell with a `<div id="dialogue">` for the text, and controls:
  - Buttons: `#btn-next`, `#btn-continue` (hidden if no save), `#btn-restart`
- `public/style.css` — minimal styling (black/white palette).
- `public/script.js` — loads `story.txt`, splits sentences, renders, and manages localStorage.
- `public/assets/background.svg` — static SVG background.
- `story.txt` — the story content (plain text).

## Server (`index.js`)
Use Express on port 3000:

```js
const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));
app.get('/', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => console.log(`Server is running on http://localhost:${port}`));

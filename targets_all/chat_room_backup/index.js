const express = require('express');
const { create } = require('express-handlebars');

const app = express();
const port = 3000;

const hbs = create({});

app.engine('handlebars', hbs.engine);
app.set('view engine', 'handlebars');
app.set('views', './views');

app.use(express.json());
app.use(express.static('public'));

let messages = [];
let nextId = 1;

app.get('/', (req, res) => {
  res.render('index', { messages });
});

// POST /api/message
app.post('/api/message', (req, res) => {
  const { username, text } = req.body;

  if (!username || !text) {
    return res.status(400).json({ error: 'Username and text are required' });
  }

  const newMessage = {
    id: nextId++,
    username,
    text,
    timestamp: new Date().toISOString(),
  };

  messages.push(newMessage);
  res.status(201).json(newMessage);
});

// GET /api/messages
app.get('/api/messages', (req, res) => {
  res.status(200).json(messages);
});

// DELETE /api/messages
app.delete('/api/messages', (req, res) => {
  messages = [];
  nextId = 1;
  res.status(204).send();
});

if (require.main === module) {
  app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
  });
}

module.exports = app;

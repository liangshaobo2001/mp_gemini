const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());
app.use(express.static('public'));

let messages = [];
let nextId = 1;

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

app.get('/api/messages', (req, res) => {
  res.json(messages);
});

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

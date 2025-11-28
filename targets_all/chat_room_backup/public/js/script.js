const messagesContainer = document.getElementById('messages-container');
const messageForm = document.getElementById('message-form');
const usernameInput = document.getElementById('username');
const messageInput = document.getElementById('message');
const refreshButton = document.getElementById('refresh-button');

const fetchMessages = async () => {
  try {
    const response = await fetch('/api/messages');
    const messages = await response.json();
    renderMessages(messages);
  } catch (error) {
    console.error('Error fetching messages:', error);
  }
};

const renderMessages = (messages) => {
  messagesContainer.innerHTML = '';
  messages.forEach(message => {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    const usernameElement = document.createElement('span');
    usernameElement.classList.add('username');
    usernameElement.textContent = message.username;

    const textElement = document.createElement('span');
        textElement.classList.add('text-content');
    textElement.textContent = message.text;

    const timestampElement = document.createElement('div');
    timestampElement.classList.add('timestamp');
    timestampElement.textContent = new Date(message.timestamp).toLocaleString();

    messageElement.appendChild(usernameElement);
    messageElement.appendChild(textElement);
    messageElement.appendChild(timestampElement);

    messagesContainer.appendChild(messageElement);
  });
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
};

const handleSubmit = async (event) => {
  event.preventDefault();

  const username = usernameInput.value;
  const text = messageInput.value;

  if (!username || !text) {
    return;
  }

  try {
    await fetch('/api/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, text }),
    });
    messageInput.value = '';
    fetchMessages();
  } catch (error) {
    console.error('Error sending message:', error);
  }
};

messageForm.addEventListener('submit', handleSubmit);
refreshButton.addEventListener('click', fetchMessages);

// Initial fetch and auto-refresh
fetchMessages();
setInterval(fetchMessages, 30000);

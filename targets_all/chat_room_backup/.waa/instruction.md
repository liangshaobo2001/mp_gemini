# Chat Room - Build Instructions

Build a public chat room application with RESTful API and dynamic frontend using Node.js, Express, and JavaScript.
The public chat room should have a single webpage (`index.html`) that is statically rendered using handlebars.
On the page, all the messages should be shown sequentially, with a form to submit a new message, by providing a username as well as a message content.
Each message's username, text, and time should be shown.
After the webpage is rendered, the page should automatically refresh the messages via Restful API calls (specified later) every 30 seconds.
There should also be a button to refresh the page manually.
Please be sure to make the website cool looking, clean, and modern.
The main design elements should be in black and white or other greyscale, while other colors can be used for clarity.
Please ensure that the webpage is easy to read
You should remember to create separate `.js` and `.css` files to manage styles and behaviors.

On the server side, there should be a Restful API to get messages (`GET /api/messages`) and one to publish a message (`POST /api/message`).
These messages should be stored in memory without utilizing files or databases, so everytime the server is restart, all the messages are wiped out and can be populated anew.
When a new message is posted, there should be a unique ID that is allocated to that message.
For testing, there should be a `DELETE /api/messages` API to remove all the messages.
The specifications on API endpoints are specified at the end of this document.

There are existing API test cases in `tests/api.test.js` and existing UI tests in `tests/ui.test.js`.
Please make sure to run those as you progress through the building of the website, and do not touch the content.
Note that for the UI test, make sure that the username and the text are in completely separate UI element under `<span>`, so that the UI tests can pass safely; do not use `::after` or `::before` for this purpose.
If you wish to create new test cases, create separate files under `tests/`.

### RESTful API Endpoints

#### POST /api/message

**Request Body:**

```json
{
  "username": "John",
  "text": "Hello, everyone!"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "username": "John",
  "text": "Hello, everyone!",
  "timestamp": "2025-10-10T12:00:00.000Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Username and text are required"
}
```

#### GET /api/messages

Retrieve all messages

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "John",
    "text": "Hello, everyone!",
    "timestamp": "2025-10-10T12:00:00.000Z"
  },
  {
    "id": 2,
    "username": "Alice",
    "text": "Hi John!",
    "timestamp": "2025-10-10T12:01:00.000Z"
  }
]
```

#### DELETE /api/messages

Deletes all the messages

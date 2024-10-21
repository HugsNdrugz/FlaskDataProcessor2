document.addEventListener('DOMContentLoaded', () => {
    fetchMessages();
    setupMessageForm();
});

function fetchMessages() {
    fetch(`/api/messages/${conversationId}`)
        .then(response => response.json())
        .then(messages => {
            const messageList = document.getElementById('message-list');
            messageList.innerHTML = '';
            messages.forEach(message => {
                const messageElement = createMessageElement(message);
                messageList.appendChild(messageElement);
            });
            scrollToBottom();
        })
        .catch(error => console.error('Error fetching messages:', error));
}

function createMessageElement(message) {
    const element = document.createElement('div');
    element.classList.add('message', message.sender_id === 1 ? 'sent' : 'received');
    
    const timestamp = new Date(message.timestamp);
    const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    element.innerHTML = `
        <p>${message.content}</p>
        <small>${formattedTime}</small>
    `;

    return element;
}

function setupMessageForm() {
    const form = document.getElementById('message-form');
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const content = document.getElementById('message-content').value.trim();
        if (content) {
            sendMessage(content);
        }
    });
}

function sendMessage(content) {
    fetch('/api/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: conversationId,
            sender_id: 1,  // Assuming user_id 1 for demonstration
            content: content
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('message-content').value = '';
            fetchMessages();
        }
    })
    .catch(error => console.error('Error sending message:', error));
}

function scrollToBottom() {
    const messageList = document.getElementById('message-list');
    messageList.scrollTop = messageList.scrollHeight;
}

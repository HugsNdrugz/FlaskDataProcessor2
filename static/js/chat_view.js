document.addEventListener('DOMContentLoaded', () => {
    fetchConversations();
    const form = document.getElementById('message-form');
    if (form) {
        setupMessageForm(form);
    }
});

function fetchConversations() {
    fetch('/api/conversations')
        .then(response => response.json())
        .then(conversations => {
            const conversationList = document.getElementById('conversation-list');
            conversationList.innerHTML = '';
            conversations.forEach(conversation => {
                const conversationElement = createConversationElement(conversation);
                conversationList.appendChild(conversationElement);
            });
        })
        .catch(error => console.error('Error fetching conversations:', error));
}

function createConversationElement(conversation) {
    const element = document.createElement('a');
    element.href = '#';
    element.classList.add('list-group-item', 'list-group-item-action');
    element.dataset.conversationId = conversation.id;
    
    const lastMessageTime = new Date(conversation.last_message_time);
    const formattedTime = lastMessageTime.toLocaleString([], { hour: '2-digit', minute: '2-digit' });

    element.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <h6 class="mb-1">${conversation.other_user}</h6>
            <small>${formattedTime}</small>
        </div>
    `;

    element.addEventListener('click', (event) => {
        event.preventDefault();
        loadConversation(conversation.id);
    });

    return element;
}

function loadConversation(conversationId) {
    document.querySelectorAll('#conversation-list a').forEach(el => el.classList.remove('active'));
    const selectedConv = document.querySelector(`#conversation-list a[data-conversation-id="${conversationId}"]`);
    if (selectedConv) {
        selectedConv.classList.add('active');
        document.getElementById('current-conversation').textContent = 
            selectedConv.querySelector('h6').textContent;
    }
    
    fetchMessages(conversationId);
    
    const messageInput = document.getElementById('message-content');
    const submitButton = document.querySelector('#message-form button[type="submit"]');
    const messageForm = document.getElementById('message-form');
    
    if (messageInput && submitButton && messageForm) {
        messageInput.disabled = false;
        submitButton.disabled = false;
        messageForm.dataset.conversationId = conversationId;
    }
}

function fetchMessages(conversationId) {
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
        <div class="message-content">
            <p class="mb-0">${message.content}</p>
        </div>
        <small class="message-time">${formattedTime}</small>
    `;

    return element;
}

function setupMessageForm(form) {
    const input = document.getElementById('message-content');
    if (!input) return;

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const content = input.value.trim();
        const conversationId = form.dataset.conversationId;
        if (content && conversationId) {
            sendMessage(conversationId, content);
            input.value = '';
        }
    });
}

function sendMessage(conversationId, content) {
    fetch('/api/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            conversation_id: conversationId,
            sender_id: 1, // Using user_id 1 for demonstration
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fetchMessages(conversationId);
        }
    })
    .catch(error => console.error('Error sending message:', error));
}

function scrollToBottom() {
    const messageList = document.getElementById('message-list');
    if (messageList) {
        messageList.scrollTop = messageList.scrollHeight;
    }
}

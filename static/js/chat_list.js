document.addEventListener('DOMContentLoaded', () => {
    fetchConversations();
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
    element.href = `/chat/${conversation.id}`;
    element.classList.add('list-group-item', 'list-group-item-action');
    
    const lastMessageTime = new Date(conversation.last_message_time);
    const formattedTime = lastMessageTime.toLocaleString();

    element.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1">${conversation.other_user}</h5>
            <small>${formattedTime}</small>
        </div>
    `;

    return element;
}

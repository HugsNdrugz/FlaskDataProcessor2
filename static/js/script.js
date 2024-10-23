document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements with proper null checks
    const elements = {
        darkModeToggler: document.querySelector('.messages-page__dark-mode-toogler'),
        chatSection: document.querySelector('.chat-section'),
        contactsList: document.querySelector('.contacts-list'),
        messageContainer: document.querySelector('.chat__content'),
        backButton: document.querySelector('.back-button'),
        contactItems: document.querySelectorAll('.contact-item'),
        chatHeader: document.querySelector('.chat-section .messages-page__header .messages-page__title')
    };

    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-bs-theme', savedTheme);

    // Mobile view state
    let isMobileView = window.innerWidth <= 768;

    // Screen resize handler
    function handleResize() {
        isMobileView = window.innerWidth <= 768;
        if (isMobileView) {
            document.body.classList.add('mobile-view');
            if (elements.chatSection) elements.chatSection.classList.add('d-none');
            if (elements.contactsList) elements.contactsList.classList.remove('d-none');
        } else {
            document.body.classList.remove('mobile-view');
            if (elements.chatSection) elements.chatSection.classList.remove('d-none');
            if (elements.contactsList) elements.contactsList.classList.remove('d-none');
        }
        adjustMessageContainer();
    }

    function adjustMessageContainer() {
        if (elements.messageContainer) {
            const header = document.querySelector('.messages-page__header');
            const input = document.querySelector('.message-input-container');
            if (header && input) {
                elements.messageContainer.style.height = `calc(100vh - ${header.offsetHeight}px - ${input.offsetHeight}px)`;
            }
        }
    }

    // Add resize listener
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    // Dark mode toggle
    if (elements.darkModeToggler) {
        elements.darkModeToggler.addEventListener('click', function() {
            const theme = document.body.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        });
    }

    // Contact item click handler
    if (elements.contactItems) {
        elements.contactItems.forEach(item => {
            if (item) {
                item.addEventListener('click', function() {
                    const contact = this.dataset.contact;
                    const contactName = this.querySelector('.contact-name')?.textContent || '';

                    // Update chat header
                    if (elements.chatHeader) {
                        elements.chatHeader.textContent = contactName;
                    }

                    // Show chat view on mobile
                    if (isMobileView) {
                        if (elements.contactsList) elements.contactsList.classList.add('d-none');
                        if (elements.chatSection) {
                            elements.chatSection.classList.remove('d-none');
                            elements.chatSection.classList.add('slide-in');
                        }
                    }

                    // Fetch messages
                    fetch(`/messages/${contact}`)
                        .then(response => response.json())
                        .then(messages => {
                            if (elements.messageContainer) {
                                elements.messageContainer.innerHTML = messages.map(msg => createMessageBubble(msg)).join('');
                                scrollToBottom();
                                updateMessageTimes();
                            }
                        })
                        .catch(error => console.error('Error fetching messages:', error));
                });
            }
        });
    }

    // Back button handler
    if (elements.backButton) {
        elements.backButton.addEventListener('click', function() {
            if (elements.chatSection) {
                elements.chatSection.classList.remove('slide-in');
                elements.chatSection.classList.add('slide-out');
                setTimeout(() => {
                    elements.chatSection.classList.add('d-none');
                    elements.chatSection.classList.remove('slide-out');
                    if (elements.contactsList) elements.contactsList.classList.remove('d-none');
                }, 300);
            }
        });
    }

    // Message bubble template
    function createMessageBubble(message) {
        const isOutgoing = message.sender === 'You';
        return `
            <div class="message-bubble ${isOutgoing ? 'message-bubble--outgoing' : 'message-bubble--incoming'}">
                <div class="message-header">
                    <span class="message-sender">${message.sender}</span>
                    <span class="message-time" data-time="${message.time}">${message.time}</span>
                </div>
                <div class="message-text">${message.text}</div>
                ${message.location ? `<div class="message-location">📍 ${message.location}</div>` : ''}
            </div>
        `;
    }

    // Message timestamps
    function updateMessageTimes() {
        document.querySelectorAll('.message-time').forEach(timestamp => {
            if (timestamp?.dataset?.time) {
                const time = new Date(timestamp.dataset.time);
                if (!isNaN(time)) {
                    timestamp.textContent = formatMessageTime(time);
                }
            }
        });
    }

    function formatMessageTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (minutes < 10080) return date.toLocaleDateString([], { weekday: 'short' });
        return date.toLocaleDateString();
    }

    // Scroll to bottom helper
    function scrollToBottom() {
        if (elements.messageContainer) {
            elements.messageContainer.scrollTop = elements.messageContainer.scrollHeight;
        }
    }

    // Update times periodically
    updateMessageTimes();
    setInterval(updateMessageTimes, 60000);

    // Initial setup
    handleResize();
    scrollToBottom();
});

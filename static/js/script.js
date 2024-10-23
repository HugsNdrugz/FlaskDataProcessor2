document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements with null checks
    const darkModeToggler = document.querySelector('.messages-page__dark-mode-toogler');
    const chatSection = document.querySelector('.chat-section');
    const contactsList = document.querySelector('.contacts-list');
    const messageContainer = document.querySelector('.chat__content');
    const backButton = document.querySelector('.back-button');
    const contactItems = document.querySelectorAll('.contact-item');
    const chatHeader = document.querySelector('.chat-section .messages-page__header .messages-page__title');

    // Mobile view state
    let isMobileView = window.innerWidth <= 768;

    // Screen resize handler
    function handleResize() {
        isMobileView = window.innerWidth <= 768;
        if (isMobileView) {
            document.body.classList.add('mobile-view');
            if (chatSection) chatSection.classList.add('d-none');
            if (contactsList) contactsList.classList.remove('d-none');
        } else {
            document.body.classList.remove('mobile-view');
            if (chatSection) chatSection.classList.remove('d-none');
            if (contactsList) contactsList.classList.remove('d-none');
        }
        adjustMessageContainer();
    }

    function adjustMessageContainer() {
        if (messageContainer) {
            const header = document.querySelector('.messages-page__header');
            const input = document.querySelector('.message-input-container');
            if (header && input) {
                messageContainer.style.height = `calc(100vh - ${header.offsetHeight}px - ${input.offsetHeight}px)`;
            }
        }
    }

    // Add resize listener
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    // Dark mode toggle with proper error handling
    if (darkModeToggler) {
        darkModeToggler.addEventListener('click', function() {
            const theme = document.body.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        });

        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-bs-theme', savedTheme);
    }

    // Contact item click handler
    contactItems.forEach(item => {
        if (item) {
            item.addEventListener('click', function() {
                const contact = this.dataset.contact;
                const contactName = this.querySelector('.contact-name').textContent;

                // Update chat header with contact name
                if (chatHeader) {
                    chatHeader.textContent = contactName;
                }

                // Show chat view on mobile
                if (isMobileView) {
                    if (contactsList) contactsList.classList.add('d-none');
                    if (chatSection) {
                        chatSection.classList.remove('d-none');
                        chatSection.classList.add('slide-in');
                    }
                }

                // Fetch messages for selected contact
                fetch(`/messages/${contact}`)
                    .then(response => response.json())
                    .then(messages => {
                        if (messageContainer) {
                            messageContainer.innerHTML = messages.map(msg => createMessageBubble(msg)).join('');
                            scrollToBottom();
                            updateMessageTimes();
                        }
                    })
                    .catch(error => console.error('Error fetching messages:', error));
            });
        }
    });

    // Back button handler
    if (backButton) {
        backButton.addEventListener('click', function() {
            if (chatSection) {
                chatSection.classList.remove('slide-in');
                chatSection.classList.add('slide-out');
                setTimeout(() => {
                    chatSection.classList.add('d-none');
                    chatSection.classList.remove('slide-out');
                    if (contactsList) contactsList.classList.remove('d-none');
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
            if (timestamp && timestamp.dataset.time) {
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
        if (messageContainer) {
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
    }

    // Update times periodically
    updateMessageTimes();
    setInterval(updateMessageTimes, 60000);

    // Initial setup
    handleResize();
    scrollToBottom();
});

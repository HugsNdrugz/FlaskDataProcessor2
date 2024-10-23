class ChatApp {
    constructor() {
        // Initialize empty elements object
        this.elements = {};
        this.isMobileView = false;
        this.currentContact = null;
        this.init();
    }

    init() {
        // Initialize DOM elements with null checks
        this.initializeElements();
        
        // Set initial theme
        this.initializeTheme();
        
        // Initialize mobile view state
        this.handleResize();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start periodic updates
        this.startPeriodicUpdates();
    }

    initializeElements() {
        // Cache all DOM elements with null checks
        const selectors = {
            darkModeToggler: '.messages-page__dark-mode-toogler',
            chatSection: '.chat-section',
            contactsList: '.contacts-list',
            messageContainer: '.chat__content',
            backButton: '.back-button',
            contactItems: '.contact-item',
            chatHeader: '.chat-section .messages-page__title',
            messageForm: '.message-input-container form',
            messageInput: '.message-input-container input[name="message"]'
        };

        // Safely query elements
        for (const [key, selector] of Object.entries(selectors)) {
            if (key === 'contactItems') {
                this.elements[key] = document.querySelectorAll(selector);
            } else {
                this.elements[key] = document.querySelector(selector);
            }
        }
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.body.setAttribute('data-bs-theme', savedTheme);
    }

    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.handleResize());

        // Dark mode toggle
        if (this.elements.darkModeToggler) {
            this.elements.darkModeToggler.addEventListener('click', () => this.toggleDarkMode());
        }

        // Contact selection
        if (this.elements.contactItems) {
            this.elements.contactItems.forEach(item => {
                if (item) {
                    item.addEventListener('click', (e) => this.handleContactSelection(e));
                }
            });
        }

        // Back button
        if (this.elements.backButton) {
            this.elements.backButton.addEventListener('click', () => this.handleBack());
        }

        // Message form
        if (this.elements.messageForm) {
            this.elements.messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }
    }

    handleResize() {
        this.isMobileView = window.innerWidth <= 768;
        
        if (this.isMobileView) {
            document.body.classList.add('mobile-view');
            if (this.elements.chatSection) {
                this.elements.chatSection.classList.add('d-none');
            }
            if (this.elements.contactsList) {
                this.elements.contactsList.classList.remove('d-none');
            }
        } else {
            document.body.classList.remove('mobile-view');
            if (this.elements.chatSection) {
                this.elements.chatSection.classList.remove('d-none');
            }
            if (this.elements.contactsList) {
                this.elements.contactsList.classList.remove('d-none');
            }
        }
        
        this.adjustMessageContainer();
    }

    adjustMessageContainer() {
        if (this.elements.messageContainer) {
            const header = document.querySelector('.messages-page__header');
            const input = document.querySelector('.message-input-container');
            if (header && input) {
                this.elements.messageContainer.style.height = 
                    `calc(100vh - ${header.offsetHeight}px - ${input.offsetHeight}px)`;
            }
        }
    }

    toggleDarkMode() {
        const currentTheme = document.body.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    async handleContactSelection(event) {
        const contactItem = event.currentTarget;
        if (!contactItem) return;

        const contact = contactItem.dataset.contact;
        const contactName = contactItem.querySelector('.contact-name')?.textContent || '';
        
        this.currentContact = contact;

        // Update chat header
        if (this.elements.chatHeader) {
            this.elements.chatHeader.textContent = contactName;
        }

        // Show chat view on mobile
        if (this.isMobileView) {
            if (this.elements.contactsList) {
                this.elements.contactsList.classList.add('d-none');
            }
            if (this.elements.chatSection) {
                this.elements.chatSection.classList.remove('d-none');
                this.elements.chatSection.classList.add('slide-in');
            }
        }

        try {
            // Fetch messages for selected contact
            const response = await fetch(`/messages/${contact}`);
            if (!response.ok) throw new Error('Failed to fetch messages');
            
            const messages = await response.json();
            
            if (this.elements.messageContainer) {
                this.elements.messageContainer.innerHTML = `
                    <div class="messages-list">
                        ${messages.map(msg => this.createMessageBubble(msg)).join('')}
                    </div>
                `;
                this.scrollToBottom();
                this.updateMessageTimes();
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
            // Show error message to user
            if (this.elements.messageContainer) {
                this.elements.messageContainer.innerHTML = `
                    <div class="alert alert-danger">
                        Failed to load messages. Please try again.
                    </div>
                `;
            }
        }
    }

    handleBack() {
        if (this.elements.chatSection) {
            this.elements.chatSection.classList.remove('slide-in');
            this.elements.chatSection.classList.add('slide-out');
            
            setTimeout(() => {
                this.elements.chatSection.classList.add('d-none');
                this.elements.chatSection.classList.remove('slide-out');
                if (this.elements.contactsList) {
                    this.elements.contactsList.classList.remove('d-none');
                }
            }, 300);
        }
    }

    async handleMessageSubmit(event) {
        event.preventDefault();
        if (!this.currentContact || !this.elements.messageInput) return;

        const messageText = this.elements.messageInput.value.trim();
        if (!messageText) return;

        try {
            const response = await fetch('/messages/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contact: this.currentContact,
                    message: messageText
                })
            });

            if (!response.ok) throw new Error('Failed to send message');

            // Clear input and refresh messages
            this.elements.messageInput.value = '';
            this.refreshMessages();
        } catch (error) {
            console.error('Error sending message:', error);
        }
    }

    createMessageBubble(message) {
        const isOutgoing = message.sender === 'You';
        return `
            <div class="message-bubble ${isOutgoing ? 'message-bubble--outgoing' : 'message-bubble--incoming'}">
                <div class="message-header">
                    <span class="message-sender">${message.sender}</span>
                    <span class="message-time" data-time="${message.time}">
                        ${this.formatMessageTime(new Date(message.time))}
                    </span>
                </div>
                <div class="message-text">${message.text}</div>
                ${message.location ? `<div class="message-location">📍 ${message.location}</div>` : ''}
            </div>
        `;
    }

    formatMessageTime(date) {
        if (!date || isNaN(date)) return '';
        
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (minutes < 10080) return date.toLocaleDateString([], { weekday: 'short' });
        return date.toLocaleDateString();
    }

    updateMessageTimes() {
        document.querySelectorAll('.message-time').forEach(timestamp => {
            if (timestamp?.dataset?.time) {
                const time = new Date(timestamp.dataset.time);
                if (!isNaN(time)) {
                    timestamp.textContent = this.formatMessageTime(time);
                }
            }
        });
    }

    scrollToBottom() {
        if (this.elements.messageContainer) {
            this.elements.messageContainer.scrollTop = this.elements.messageContainer.scrollHeight;
        }
    }

    async refreshMessages() {
        if (!this.currentContact) return;
        
        try {
            const response = await fetch(`/messages/${this.currentContact}`);
            if (!response.ok) throw new Error('Failed to refresh messages');
            
            const messages = await response.json();
            
            if (this.elements.messageContainer) {
                this.elements.messageContainer.innerHTML = `
                    <div class="messages-list">
                        ${messages.map(msg => this.createMessageBubble(msg)).join('')}
                    </div>
                `;
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Error refreshing messages:', error);
        }
    }

    startPeriodicUpdates() {
        // Update message times every minute
        this.updateMessageTimes();
        setInterval(() => this.updateMessageTimes(), 60000);

        // Refresh messages every 30 seconds if chat is open
        setInterval(() => {
            if (this.currentContact && !this.elements.chatSection?.classList.contains('d-none')) {
                this.refreshMessages();
            }
        }, 30000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});

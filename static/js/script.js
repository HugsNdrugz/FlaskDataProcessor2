class ChatInterface {
    constructor() {
        // Initialize properties
        this.currentContact = null;
        this.elements = {};
        
        // Initialize the interface
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        try {
            this.cacheElements();
            this.bindEvents();
            this.initializeTheme();
            this.startPeriodicUpdates();
        } catch (error) {
            console.error('Initialization error:', error);
        }
    }

    cacheElements() {
        // Cache DOM elements with error handling
        const selectors = {
            contactsView: '#contactsView',
            chatView: '#chatView',
            contacts: '.contact-item',
            backButton: '.back-button',
            themeToggle: '.theme-toggle',
            messageForm: '.message-form',
            messageInput: 'input[name="message"]',
            messagesList: '.messages-list',
            chatContactName: '#chatView .contact-name'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            const element = key === 'contacts' 
                ? document.querySelectorAll(selector)
                : document.querySelector(selector);
            
            if (!element && key !== 'contacts') {
                throw new Error(`Required element not found: ${selector}`);
            }
            
            this.elements[key] = element;
        }
    }

    bindEvents() {
        // Bind event listeners with error handling
        if (this.elements.contacts) {
            this.elements.contacts.forEach(contact => {
                contact.addEventListener('click', (e) => this.handleContactClick(e));
            });
        }

        if (this.elements.backButton) {
            this.elements.backButton.addEventListener('click', () => this.handleBack());
        }

        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        if (this.elements.messageForm) {
            this.elements.messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        }
    }

    async handleContactClick(event) {
        try {
            const contactElement = event.currentTarget;
            const contact = contactElement.dataset.contact;
            const contactName = contactElement.querySelector('.contact-name').textContent;

            this.currentContact = contact;
            
            // Update chat view header
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            // Show chat view
            this.elements.contactsView.classList.remove('active');
            this.elements.chatView.classList.add('active');

            // Load messages
            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
            this.showError('Failed to load messages');
        }
    }

    handleBack() {
        this.elements.chatView.classList.remove('active');
        this.elements.contactsView.classList.add('active');
        this.currentContact = null;
    }

    async loadMessages(contact) {
        try {
            const response = await fetch(`/messages/${contact}`);
            if (!response.ok) throw new Error('Failed to fetch messages');
            
            const messages = await response.json();
            this.renderMessages(messages);
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages');
        }
    }

    renderMessages(messages) {
        if (!this.elements.messagesList) return;

        this.elements.messagesList.innerHTML = messages
            .map(msg => this.createMessageElement(msg))
            .join('');

        this.scrollToBottom();
    }

    createMessageElement(message) {
        const isOutgoing = message.sender === 'You';
        const time = this.formatTime(new Date(message.time));
        
        return `
            <div class="message-bubble message-bubble--${isOutgoing ? 'outgoing' : 'incoming'}">
                <div class="message-content">${message.text}</div>
                <time class="message-time" datetime="${message.time}">${time}</time>
                ${message.location ? `<div class="message-location">📍 ${message.location}</div>` : ''}
            </div>
        `;
    }

    async handleMessageSubmit(event) {
        event.preventDefault();
        
        if (!this.currentContact || !this.elements.messageInput) return;

        const messageText = this.elements.messageInput.value.trim();
        if (!messageText) return;

        try {
            const response = await fetch('/messages/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contact: this.currentContact,
                    message: messageText
                })
            });

            if (!response.ok) throw new Error('Failed to send message');

            this.elements.messageInput.value = '';
            await this.loadMessages(this.currentContact);
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message');
        }
    }

    formatTime(date) {
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

    scrollToBottom() {
        if (this.elements.messagesList) {
            this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
        }
    }

    showError(message) {
        // Implement error toast or alert
        alert(message);
    }

    toggleTheme() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }

    startPeriodicUpdates() {
        // Update message times every minute
        setInterval(() => {
            document.querySelectorAll('.message-time').forEach(timeElement => {
                const datetime = timeElement.getAttribute('datetime');
                if (datetime) {
                    timeElement.textContent = this.formatTime(new Date(datetime));
                }
            });
        }, 60000);

        // Refresh messages every 30 seconds if chat is open
        setInterval(() => {
            if (this.currentContact) {
                this.loadMessages(this.currentContact);
            }
        }, 30000);
    }
}

// Initialize the chat interface
new ChatInterface();

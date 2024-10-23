'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.periodicUpdates = null;

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        try {
            await this.cacheElements();
            await this.initializeTheme();
            this.bindEvents();
            this.startPeriodicUpdates();
        } catch (error) {
            console.error('Error in init:', error);
        }
    }

    async cacheElements() {
        const selectors = {
            contactsView: '#contactsView',
            chatView: '#chatView',
            contacts: '.contact-item',
            backButton: '.back-button',
            themeToggle: '.theme-toggle',
            themeIcon: '.theme-toggle i',
            messageForm: '.message-form',
            messageInput: 'input[name="message"]',
            messagesList: '.messages-list',
            chatContactName: '#chatView .contact-name'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            try {
                this.elements[key] = key === 'contacts' 
                    ? document.querySelectorAll(selector)
                    : document.querySelector(selector);
            } catch (error) {
                console.warn(`Error caching element ${key}:`, error);
                this.elements[key] = null;
            }
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                if (contact) {
                    contact.addEventListener('click', this.handleContactClick.bind(this));
                }
            });
        }

        this.elements.backButton?.addEventListener('click', this.handleBack.bind(this));
        this.elements.themeToggle?.addEventListener('click', this.toggleTheme.bind(this));
        this.elements.messageForm?.addEventListener('submit', this.handleMessageSubmit.bind(this));
    }

    async initializeTheme() {
        try {
            let savedTheme = localStorage.getItem('theme') || 'dark';
            const html = document.documentElement;
            if (html) {
                html.setAttribute('data-bs-theme', savedTheme);
                await this.updateThemeIcon(savedTheme);
            }
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    async updateThemeIcon(theme) {
        const iconElement = this.elements.themeIcon;
        if (!iconElement) return;

        iconElement.classList.remove('bi-sun-fill', 'bi-moon-fill');
        iconElement.classList.add(theme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill');
    }

    async toggleTheme() {
        try {
            const html = document.documentElement;
            if (!html) return;

            const currentTheme = html.getAttribute('data-bs-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            await this.updateThemeIcon(newTheme);
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    async handleContactClick(event) {
        try {
            const contactElement = event.currentTarget;
            if (!contactElement) return;

            const contact = contactElement.dataset.contact;
            const contactNameElement = contactElement.querySelector('.contact-name');
            const contactName = contactNameElement?.textContent;

            if (!contact || !contactName) return;

            this.currentContact = contact;
            
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            this.elements.contactsView?.classList.remove('active');
            this.elements.chatView?.classList.add('active');

            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
        }
    }

    handleBack() {
        this.elements.chatView?.classList.remove('active');
        this.elements.contactsView?.classList.add('active');
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
        }
    }

    formatTime(date) {
        if (!date || isNaN(date.getTime())) return '';
        
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
                this.loadMessages(this.currentContact).catch(error => {
                    console.error('Error refreshing messages:', error);
                });
            }
        }, 30000);
    }
}

// Initialize the chat interface
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.chatInterface = new ChatInterface();
    } catch (error) {
        console.error('Error creating ChatInterface:', error);
    }
});

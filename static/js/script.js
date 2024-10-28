'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.socket = null;
        
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    async init() {
        try {
            await this.cacheElements();
            this.initializeSocket();
            this.bindEvents();
            this.initializeTheme();
        } catch (error) {
            console.error('Initialization error:', error);
        }
    }

    initializeSocket() {
        this.socket = io(window.location.origin, {
            transports: ['websocket'],
            upgrade: false
        });

        this.socket.on('connect', () => {
            console.log('Connected to WebSocket');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket');
        });

        this.socket.on('message_update', (data) => {
            if (this.currentContact && data.contact === this.currentContact) {
                this.loadMessages(this.currentContact);
            }
        });
    }

    async cacheElements() {
        this.elements = {
            contactsView: document.querySelector('#contactsView'),
            chatView: document.querySelector('#chatView'),
            contacts: document.querySelectorAll('.contact-item'),
            backButton: document.querySelector('.back-button'),
            themeToggle: document.querySelector('.theme-toggle'),
            themeIcon: document.querySelector('.theme-toggle i'),
            messagesList: document.querySelector('.messages-list'),
            chatContactName: document.querySelector('#chatView .contact-name')
        };
    }

    bindEvents() {
        this.elements.contacts?.forEach(contact => {
            contact?.addEventListener('click', (e) => this.handleContactClick(e));
        });

        this.elements.backButton?.addEventListener('click', () => this.handleBack());
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());
    }

    initializeTheme() {
        const theme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-bs-theme', theme);
        this.updateThemeIcon(theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        if (this.elements.themeIcon) {
            this.elements.themeIcon.className = theme === 'dark' 
                ? 'bi bi-sun-fill' 
                : 'bi bi-moon-fill';
        }
    }

    async handleContactClick(event) {
        const contactElement = event.currentTarget;
        const contactName = contactElement.dataset.contact;
        
        if (!contactName) return;

        if (this.currentContact) {
            this.socket.emit('leave', { contact: this.currentContact });
        }

        this.currentContact = contactName;
        this.socket.emit('join', { contact: contactName });
        
        if (this.elements.chatContactName) {
            this.elements.chatContactName.textContent = contactName;
        }
        
        this.elements.contactsView?.classList.add('d-none');
        this.elements.chatView?.classList.remove('d-none');
        
        try {
            await this.loadMessages(contactName);
        } catch (error) {
            console.error('Failed to load messages:', error);
            this.elements.messagesList.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load messages. Please try again.
                </div>
            `;
        }
    }

    handleBack() {
        if (this.currentContact) {
            this.socket.emit('leave', { contact: this.currentContact });
        }
        this.currentContact = null;
        this.elements.chatView?.classList.add('d-none');
        this.elements.contactsView?.classList.remove('d-none');
        this.elements.messagesList.innerHTML = '';
    }

    async loadMessages(contact) {
        try {
            const response = await fetch(`/messages/${contact}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            this.displayMessages(messages);
        } catch (error) {
            console.error('Error loading messages:', error);
            throw error;
        }
    }

    displayMessages(messages) {
        if (!this.elements.messagesList) return;
        
        this.elements.messagesList.innerHTML = '';
        messages.forEach(message => {
            const messageHTML = this.createMessageBubble(message);
            this.elements.messagesList.insertAdjacentHTML('beforeend', messageHTML);
        });
        
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.elements.messagesList) {
            this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
        }
    }

    createMessageBubble(message) {
        const formattedTime = new Date(message.time).toLocaleString();
        const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
        
        return `
            <div class="message-bubble message-bubble--${bubbleClass}">
                <div class="message-text">${this.escapeHtml(message.text || '')}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
            </div>
        `.trim();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chatInterface = new ChatInterface();
    });
} else {
    window.chatInterface = new ChatInterface();
}

'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.retryCount = 0;
        this.maxRetries = 3;
        this.socket = null;
        
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    handleError(error) {
        console.error('Error:', error);
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            console.log(`Retrying (${this.retryCount}/${this.maxRetries})...`);
            setTimeout(() => this.init(), 2000 * this.retryCount);
        } else {
            const messagesList = document.querySelector('.messages-list');
            if (messagesList) {
                messagesList.innerHTML = '<div class="alert alert-danger">Connection failed. Please refresh the page.</div>';
            }
        }
    }

    async init() {
        try {
            await this.cacheElements();
            await this.initializeTheme();
            this.bindEvents();
            this.retryCount = 0;
        } catch (error) {
            this.handleError(error);
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
            messagesList: '.messages-list',
            chatContactName: '#chatView .contact-name'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            this.elements[key] = key === 'contacts' 
                ? document.querySelectorAll(selector)
                : document.querySelector(selector);
            
            if (!this.elements[key] && key !== 'contacts') {
                console.warn(`Element not found: ${selector}`);
            }
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                contact?.addEventListener('click', (e) => this.handleContactClick(e));
            });
        }

        this.elements.backButton?.addEventListener('click', () => this.handleBack());
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());
    }

    async initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            await this.updateThemeIcon(savedTheme);
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
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
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
            const response = await fetch(`/messages/${encodeURIComponent(contact)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            
            if (this.elements.messagesList) {
                const messagesHTML = messages
                    .map(msg => this.createMessageBubble(msg))
                    .join('');
                this.elements.messagesList.innerHTML = messagesHTML;
                this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            if (this.elements.messagesList) {
                this.elements.messagesList.innerHTML = '<div class="alert alert-danger">Failed to load messages</div>';
            }
        }
    }

    createMessageBubble(message) {
        try {
            const formattedTime = new Date(message.time).toLocaleString();
            const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
            
            return `
                <div class="message-bubble message-bubble--${bubbleClass}">
                    <div class="message-text">${this.escapeHtml(message.text || '')}</div>
                    <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                </div>
            `.trim();
        } catch (error) {
            console.error('Error creating message bubble:', error);
            return '';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the chat interface
const initializeChat = () => {
    try {
        window.chatInterface = new ChatInterface();
    } catch (error) {
        console.error('Error creating ChatInterface:', error);
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChat);
} else {
    initializeChat();
}

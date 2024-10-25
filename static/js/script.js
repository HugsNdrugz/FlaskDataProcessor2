'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.retryCount = 0;
        this.maxRetries = 3;
        this.socket = null;
        this.messagesCursor = 0;
        this.contactsCursor = 0;
        this.limit = 20;
        this.isLoading = false;
        this.hasMoreMessages = true;
        this.hasMoreContacts = true;
        this.loadingThrottle = null;
        this.scrollThreshold = 100;
        this.loadingDelay = 500; // Increased from 300
        this.retryDelay = 2000;
        
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    async init() {
        try {
            await this.cacheElements();
            await this.initializeTheme();
            this.bindEvents();
            this.retryCount = 0;
            // Initial load of contacts
            await this.loadContacts();
        } catch (error) {
            this.handleError(error);
        }
    }

    async retryRequest(request) {
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                return await request();
            } catch (error) {
                console.error(`Request failed (attempt ${attempt}/${this.maxRetries}):`, error);
                if (attempt === this.maxRetries) throw error;
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
            }
        }
    }

    handleError(error) {
        console.error('Error:', error);
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            console.log(`Retrying (${this.retryCount}/${this.maxRetries})...`);
            setTimeout(() => this.init(), this.retryDelay * this.retryCount);
        } else {
            const messagesList = document.querySelector('.messages-list');
            if (messagesList) {
                messagesList.innerHTML = '<div class="alert alert-danger">Connection failed. Please refresh the page.</div>';
            }
        }
    }

    async cacheElements() {
        const selectors = {
            contactsView: '#contactsView',
            chatView: '#chatView',
            backButton: '.back-button',
            themeToggle: '.theme-toggle',
            themeIcon: '.theme-toggle i',
            messagesList: '.messages-list',
            contactsList: '.contacts-list',
            chatContactName: '#chatView .contact-name',
            messagesLoader: '.messages-loader',
            contactsLoader: '.contacts-loader'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            this.elements[key] = document.querySelector(selector);
            if (!this.elements[key]) {
                console.warn(`Element not found: ${selector}`);
            }
        }
    }

    bindEvents() {
        if (this.elements.contactsList) {
            this.elements.contactsList.addEventListener('scroll', this.throttle(() => this.handleContactScroll(), this.loadingDelay));
        }

        if (this.elements.messagesList) {
            this.elements.messagesList.addEventListener('scroll', this.throttle(() => this.handleMessageScroll(), this.loadingDelay));
        }

        this.elements.backButton?.addEventListener('click', () => this.handleBack());
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());

        this.bindContactClickEvents();
    }

    throttle(func, limit) {
        let inThrottle;
        return (...args) => {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    async handleContactScroll() {
        if (this.isLoading || !this.hasMoreContacts) return;

        const container = this.elements.contactsList;
        if (!container) return;

        const scrollPosition = container.scrollTop + container.clientHeight;
        const scrollThreshold = container.scrollHeight - this.scrollThreshold;

        if (scrollPosition >= scrollThreshold) {
            await this.loadContacts(true);
        }
    }

    async handleMessageScroll() {
        if (this.isLoading || !this.hasMoreMessages) return;

        const container = this.elements.messagesList;
        if (!container) return;

        const scrollPosition = container.scrollTop;

        if (scrollPosition <= this.scrollThreshold) {
            const prevScrollHeight = container.scrollHeight;
            await this.loadMessages(this.currentContact, true);
            
            if (container.scrollHeight > prevScrollHeight) {
                container.scrollTop = container.scrollHeight - prevScrollHeight;
            }
        }
    }

    async loadContacts(append = false) {
        if (this.isLoading) return;

        try {
            this.isLoading = true;
            this.toggleLoader('contacts', true);

            const response = await this.retryRequest(() => 
                fetch(`/contacts?cursor=${this.contactsCursor}&limit=${this.limit}`)
            );
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            if (!data.contacts || data.contacts.length === 0) {
                this.hasMoreContacts = false;
                return;
            }

            const contactsHTML = data.contacts.map(contact => this.createContactElement(contact)).join('');
            
            if (append) {
                this.elements.contactsList.insertAdjacentHTML('beforeend', contactsHTML);
            } else {
                this.elements.contactsList.innerHTML = contactsHTML;
            }

            if (data.contacts.length > 0) {
                this.contactsCursor = data.contacts[data.contacts.length - 1].cursor;
            }
            
            this.hasMoreContacts = data.has_more;
            this.bindContactClickEvents();

        } catch (error) {
            console.error('Error loading contacts:', error);
            this.showError('Failed to load contacts. Retrying...');
            await new Promise(resolve => setTimeout(resolve, this.retryDelay));
            await this.loadContacts(append);
        } finally {
            this.isLoading = false;
            this.toggleLoader('contacts', false);
        }
    }

    async loadMessages(contact, prepend = false) {
        if (this.isLoading || !contact) return;

        try {
            this.isLoading = true;
            this.toggleLoader('messages', true);

            const response = await this.retryRequest(() =>
                fetch(`/messages/${encodeURIComponent(contact)}?cursor=${this.messagesCursor}&limit=${this.limit}`)
            );
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            if (!data.messages || data.messages.length === 0) {
                this.hasMoreMessages = false;
                return;
            }

            const messagesHTML = data.messages.map(msg => this.createMessageBubble(msg)).join('');
            
            if (prepend) {
                this.elements.messagesList.insertAdjacentHTML('afterbegin', messagesHTML);
            } else {
                this.elements.messagesList.insertAdjacentHTML('beforeend', messagesHTML);
                this.scrollToBottom();
            }

            if (data.messages.length > 0) {
                this.messagesCursor = data.messages[data.messages.length - 1].cursor;
            }
            
            this.hasMoreMessages = data.has_more;

        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages. Retrying...');
            await new Promise(resolve => setTimeout(resolve, this.retryDelay));
            await this.loadMessages(contact, prepend);
        } finally {
            this.isLoading = false;
            this.toggleLoader('messages', false);
        }
    }

    createContactElement(contact) {
        return `
            <div class="contact-item" data-contact="${this.escapeHtml(contact.name)}" data-cursor="${contact.cursor}">
                <div class="contact-info">
                    <span class="contact-name">${this.escapeHtml(contact.name)}</span>
                    <span class="contact-last-message">${this.escapeHtml(contact.last_message || '')}</span>
                </div>
                <time class="contact-time" datetime="${contact.last_message_time || ''}">
                    ${contact.last_message_time ? new Date(contact.last_message_time).toLocaleString() : ''}
                </time>
            </div>
        `.trim();
    }

    createMessageBubble(message) {
        const formattedTime = new Date(message.time).toLocaleString();
        const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
        
        return `
            <div class="message-bubble message-bubble--${bubbleClass}" data-cursor="${message.cursor}">
                <div class="message-text">${this.escapeHtml(message.text || '')}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
            </div>
        `.trim();
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
            this.messagesCursor = 0;
            this.hasMoreMessages = true;
            
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            this.elements.contactsView?.classList.remove('active');
            this.elements.chatView?.classList.add('active');

            if (this.elements.messagesList) {
                this.elements.messagesList.innerHTML = '';
            }

            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
            this.showError('Failed to load chat. Please try again.');
        }
    }

    handleBack() {
        this.elements.chatView?.classList.remove('active');
        this.elements.contactsView?.classList.add('active');
        this.currentContact = null;
        this.messagesCursor = 0;
        this.hasMoreMessages = true;
    }

    bindContactClickEvents() {
        const contacts = document.querySelectorAll('.contact-item');
        contacts.forEach(contact => {
            contact.addEventListener('click', (e) => this.handleContactClick(e));
        });
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

    toggleLoader(type, show) {
        const loader = type === 'messages' ? this.elements.messagesLoader : this.elements.contactsLoader;
        if (loader) {
            loader.style.display = show ? 'flex' : 'none';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        
        const container = this.elements.messagesList || this.elements.contactsList;
        if (container) {
            container.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 3000);
        }
    }

    scrollToBottom() {
        if (this.elements.messagesList) {
            this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chat interface
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

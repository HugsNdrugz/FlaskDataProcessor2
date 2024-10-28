'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.messageCache = new Map();
        this.loadingStates = new Set();
        
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
            this.setupContactsList();
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
            messagesList: '.messages-list',
            chatContactName: '#chatView .contact-name',
            messagesContainer: '.messages-container'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            try {
                this.elements[key] = key === 'contacts' 
                    ? document.querySelectorAll(selector)
                    : document.querySelector(selector);
                    
                if (!this.elements[key] && key !== 'contacts') {
                    console.warn(`Element not found: ${selector}`);
                }
            } catch (error) {
                console.warn(`Error caching element ${key}:`, error);
                this.elements[key] = null;
            }
        }
    }

    setupContactsList() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                const avatar = contact.querySelector('.contact-avatar');
                if (avatar) {
                    const name = contact.querySelector('.contact-name')?.textContent;
                    if (name) {
                        avatar.textContent = name.charAt(0).toUpperCase();
                    }
                }
            });
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                contact?.addEventListener('click', (e) => this.handleContactClick(e));
            });
        }

        if (this.elements.backButton) {
            this.elements.backButton.addEventListener('click', () => this.handleBack());
        }

        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.addEventListener('scroll', () => this.handleScroll());
        }
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
        try {
            const iconElement = this.elements.themeIcon;
            if (!iconElement) return;

            iconElement.classList.remove('bi-sun-fill', 'bi-moon-fill');
            iconElement.classList.add(theme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill');
        } catch (error) {
            console.error('Error updating theme icon:', error);
        }
    }

    async toggleTheme() {
        try {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            await this.updateThemeIcon(newTheme);
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    setLoading(key, isLoading) {
        if (isLoading) {
            this.loadingStates.add(key);
        } else {
            this.loadingStates.delete(key);
        }

        const messagesList = this.elements.messagesList;
        if (!messagesList) return;

        const loadingElement = messagesList.querySelector('.loading');
        if (isLoading && !loadingElement) {
            const loader = document.createElement('div');
            loader.className = 'loading';
            loader.textContent = 'Loading messages';
            messagesList.appendChild(loader);
        } else if (!isLoading && loadingElement) {
            loadingElement.remove();
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

            // Remove active class from all contacts
            this.elements.contacts.forEach(c => c.classList.remove('active'));
            // Add active class to clicked contact
            contactElement.classList.add('active');

            this.currentContact = contact;
            
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            if (this.elements.contactsView) {
                this.elements.contactsView.classList.remove('active');
            }
            if (this.elements.chatView) {
                this.elements.chatView.classList.add('active');
            }

            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
        }
    }

    handleBack() {
        try {
            if (this.elements.chatView) {
                this.elements.chatView.classList.remove('active');
            }
            if (this.elements.contactsView) {
                this.elements.contactsView.classList.add('active');
            }
            // Remove active class from all contacts
            this.elements.contacts.forEach(c => c.classList.remove('active'));
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back:', error);
        }
    }

    handleScroll() {
        // Implement infinite scrolling or load more messages
        // when user scrolls to top of messages container
    }

    async loadMessages(contact) {
        try {
            this.setLoading(contact, true);

            const response = await fetch(`/messages/${contact}`);
            const messages = await response.json();
            
            this.messageCache.set(contact, messages);
            
            if (this.elements.messagesList && this.currentContact === contact) {
                const messagesHTML = messages
                    .map(msg => this.createMessageBubble(msg))
                    .join('');
                this.elements.messagesList.innerHTML = messagesHTML;
                this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        } finally {
            this.setLoading(contact, false);
        }
    }

    createMessageBubble(message) {
        const formattedTime = new Date(message.time).toLocaleString(undefined, {
            hour: 'numeric',
            minute: 'numeric',
            hour12: true,
            month: 'short',
            day: 'numeric',
        });
        
        const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
        
        return `
            <div class="message-bubble message-bubble--${bubbleClass}">
                <div class="message-text">${this.escapeHTML(message.text || '')}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
            </div>
        `.trim();
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
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

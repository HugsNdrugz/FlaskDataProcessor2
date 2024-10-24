'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        
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
            chatContactName: '#chatView .contact-name'
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
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back:', error);
        }
    }

    async loadMessages(contact) {
        try {
            const response = await fetch(`/messages/${contact}`);
            const messages = await response.json();
            
            if (this.elements.messagesList) {
                this.elements.messagesList.innerHTML = messages
                    .map(msg => this.createMessageBubble(msg))
                    .join('');
                this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    createMessageBubble(message) {
        const formattedTime = new Date(message.time).toLocaleString();
        return `
            <div class="message-bubble message-bubble--${message.sender === this.currentContact ? 'incoming' : 'outgoing'}">
                <div class="message-text">${message.text}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
            </div>
        `;
    }
}

// Initialize the chat interface
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        try {
            window.chatInterface = new ChatInterface();
        } catch (error) {
            console.error('Error creating ChatInterface:', error);
        }
    });
} else {
    try {
        window.chatInterface = new ChatInterface();
    } catch (error) {
        console.error('Error creating ChatInterface:', error);
    }
}

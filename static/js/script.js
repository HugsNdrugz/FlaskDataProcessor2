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
                const element = key === 'contacts' 
                    ? document.querySelectorAll(selector)
                    : document.querySelector(selector);
                    
                if (!element && key !== 'contacts') {
                    console.warn(`Element not found: ${selector}`);
                }
                
                this.elements[key] = element;
            } catch (error) {
                console.warn(`Error caching element ${key}:`, error);
                this.elements[key] = null;
            }
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            Array.from(this.elements.contacts).forEach(contact => {
                contact?.addEventListener('click', (e) => this.handleContactClick(e));
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

    async initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            const html = document.documentElement;
            
            if (html) {
                html.setAttribute('data-theme', savedTheme);
                await this.updateThemeIcon(savedTheme);
            }
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
            const html = document.documentElement;
            if (!html) return;

            const currentTheme = html.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
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
        try {
            this.elements.chatView?.classList.remove('active');
            this.elements.contactsView?.classList.add('active');
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back:', error);
        }
    }

    startPeriodicUpdates() {
        if (this.currentContact) {
            setInterval(() => {
                this.loadMessages(this.currentContact);
            }, 30000);
        }
    }
}

// Initialize the chat interface
const initChatInterface = () => {
    try {
        window.chatInterface = new ChatInterface();
    } catch (error) {
        console.error('Error creating ChatInterface:', error);
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatInterface);
} else {
    initChatInterface();
}

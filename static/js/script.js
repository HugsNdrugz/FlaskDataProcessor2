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
                console.error(`Error caching element ${key}:`, error);
                this.elements[key] = null;
            }
        }
    }

    bindEvents() {
        try {
            // Bind contacts click events
            if (this.elements.contacts && this.elements.contacts.length > 0) {
                this.elements.contacts.forEach(contact => {
                    try {
                        contact.addEventListener('click', (e) => this.handleContactClick(e));
                    } catch (error) {
                        console.error('Error binding contact click:', error);
                    }
                });
            }

            // Bind back button
            if (this.elements.backButton) {
                this.elements.backButton.addEventListener('click', () => this.handleBack());
            }

            // Bind theme toggle
            if (this.elements.themeToggle) {
                this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
            }

            // Bind message form
            if (this.elements.messageForm) {
                this.elements.messageForm.addEventListener('submit', (e) => this.handleMessageSubmit(e));
            }
        } catch (error) {
            console.error('Error binding events:', error);
        }
    }

    async handleContactClick(event) {
        try {
            const contactElement = event.currentTarget;
            const contact = contactElement.dataset.contact;
            const contactName = contactElement.querySelector('.contact-name')?.textContent;

            if (!contact || !contactName) {
                throw new Error('Invalid contact data');
            }

            this.currentContact = contact;
            
            // Update chat view header
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            // Show chat view
            this.elements.contactsView?.classList.remove('active');
            this.elements.chatView?.classList.add('active');

            // Load messages
            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
            this.showError('Failed to load messages');
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

    toggleTheme() {
        try {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-bs-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Update theme
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            // Update icon
            if (this.elements.themeIcon) {
                const iconElement = this.elements.themeIcon;
                if (newTheme === 'dark') {
                    iconElement.classList.remove('bi-sun-fill');
                    iconElement.classList.add('bi-moon-fill');
                } else {
                    iconElement.classList.remove('bi-moon-fill');
                    iconElement.classList.add('bi-sun-fill');
                }
            }
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            
            // Update initial icon state
            if (this.elements.themeIcon) {
                const iconElement = this.elements.themeIcon;
                if (savedTheme === 'dark') {
                    iconElement.classList.remove('bi-sun-fill');
                    iconElement.classList.add('bi-moon-fill');
                } else {
                    iconElement.classList.remove('bi-moon-fill');
                    iconElement.classList.add('bi-sun-fill');
                }
            }
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    // ... rest of the class methods remain the same ...
}

// Initialize the chat interface
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});

class ChatInterface {
    constructor() {
        // Defer initialization to async init method
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.asyncInit());
        } else {
            this.asyncInit();
        }
    }

    async asyncInit() {
        try {
            this.currentContact = null;
            this.elements = {};
            
            await this.cacheElements();
            await this.initializeTheme();
            this.bindEvents();
            this.startPeriodicUpdates();
        } catch (error) {
            console.error('Initialization error:', error);
        }
    }

    async cacheElements() {
        return new Promise((resolve) => {
            try {
                // Define selectors map
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

                // Cache elements with proper error handling
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
                resolve();
            } catch (error) {
                console.error('Error in cacheElements:', error);
                this.elements = {};
                resolve();
            }
        });
    }

    bindEvents() {
        try {
            // Bind contact click events with optional chaining
            if (this.elements.contacts?.length > 0) {
                this.elements.contacts.forEach(contact => {
                    contact?.addEventListener('click', (e) => this.handleContactClick(e));
                });
            }

            // Bind back button with optional chaining
            this.elements.backButton?.addEventListener('click', () => this.handleBack());

            // Bind theme toggle with optional chaining
            this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());

            // Bind message form with optional chaining
            this.elements.messageForm?.addEventListener('submit', (e) => this.handleMessageSubmit(e));
        } catch (error) {
            console.error('Error binding events:', error);
        }
    }

    async initializeTheme() {
        try {
            // Get saved theme from localStorage with error handling
            let savedTheme = 'dark';
            try {
                const stored = localStorage.getItem('theme');
                if (stored) {
                    savedTheme = stored;
                }
            } catch (error) {
                console.warn('Error accessing localStorage:', error);
            }

            // Apply theme to document
            document.documentElement?.setAttribute('data-bs-theme', savedTheme);
            
            // Update theme icon
            await this.updateThemeIcon(savedTheme);
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    async updateThemeIcon(theme) {
        try {
            const iconElement = this.elements.themeIcon;
            if (!iconElement) return;

            // Remove existing classes
            iconElement.classList.remove('bi-sun-fill', 'bi-moon-fill');
            
            // Add appropriate icon class
            iconElement.classList.add(theme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill');
        } catch (error) {
            console.error('Error updating theme icon:', error);
        }
    }

    async toggleTheme() {
        try {
            const html = document.documentElement;
            if (!html) return;

            const currentTheme = html.getAttribute('data-bs-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Update theme
            html.setAttribute('data-bs-theme', newTheme);
            
            // Save theme preference with error handling
            try {
                localStorage.setItem('theme', newTheme);
            } catch (error) {
                console.warn('Error saving theme preference:', error);
            }

            // Update icon
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

            if (!contact || !contactName) {
                throw new Error('Invalid contact data');
            }

            this.currentContact = contact;
            
            // Update chat view header with optional chaining
            this.elements.chatContactName?.textContent = contactName;

            // Show chat view with optional chaining
            this.elements.contactsView?.classList.remove('active');
            this.elements.chatView?.classList.add('active');

            // Load messages
            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
        }
    }

    handleBack() {
        try {
            // Use optional chaining for classList operations
            this.elements.chatView?.classList.remove('active');
            this.elements.contactsView?.classList.add('active');
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back:', error);
        }
    }

    // Add other necessary methods here...
}

// Initialize the chat interface
document.addEventListener('DOMContentLoaded', () => {
    try {
        new ChatInterface();
    } catch (error) {
        console.error('Error creating ChatInterface:', error);
    }
});

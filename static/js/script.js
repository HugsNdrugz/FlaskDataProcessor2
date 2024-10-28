'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.messageCache = new Map();
        this.loadingStates = new Set();
        this.isLoadingMore = false;
        this.pageSize = 20;
        this.currentPage = 1;

        // Bind methods in constructor
        this.handleScroll = this.handleScroll.bind(this);
        this.handleContactClick = this.handleContactClick.bind(this);
        this.handleBack = this.handleBack.bind(this);
        this.toggleTheme = this.toggleTheme.bind(this);
        
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
            this.initializeSearch();
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
            messagesContainer: '.messages-container',
            searchInput: '.search-input',
            contactList: '.contact-list',
            emptyState: '.empty-state'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            this.elements[key] = key === 'contacts' 
                ? document.querySelectorAll(selector)
                : document.querySelector(selector);
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                contact?.addEventListener('click', this.handleContactClick);
            });
        }

        if (this.elements.backButton) {
            this.elements.backButton.addEventListener('click', this.handleBack);
        }

        if (this.elements.themeToggle) {
            this.elements.themeToggle.addEventListener('click', this.toggleTheme);
        }

        // Add scroll event listener with bound handler
        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.addEventListener('scroll', this.handleScroll);
        }
    }

    handleScroll() {
        if (!this.elements.messagesContainer || this.isLoadingMore) return;

        const { scrollTop, scrollHeight, clientHeight } = this.elements.messagesContainer;
        
        // Load more messages when scrolled near top
        if (scrollTop <= 100 && this.currentContact) {
            this.loadMoreMessages();
        }
    }

    groupMessagesByDate(messages) {
        const groups = new Map();
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        messages.forEach(msg => {
            try {
                const date = new Date(msg.time);
                
                // Validate date
                if (isNaN(date.getTime())) {
                    console.warn('Invalid date encountered:', msg.time);
                    return;
                }

                let dateStr = '';
                if (date.toDateString() === today.toDateString()) {
                    dateStr = 'Today';
                } else if (date.toDateString() === yesterday.toDateString()) {
                    dateStr = 'Yesterday';
                } else {
                    dateStr = date.toLocaleDateString(undefined, {
                        month: 'long',
                        day: 'numeric',
                        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
                    });
                }

                if (!groups.has(dateStr)) {
                    groups.set(dateStr, []);
                }
                groups.get(dateStr).push(msg);
            } catch (error) {
                console.warn('Error processing message date:', error);
            }
        });

        return groups;
    }

    createMessageBubble(message) {
        let formattedTime;
        try {
            const date = new Date(message.time);
            if (isNaN(date.getTime())) {
                formattedTime = 'Invalid Date';
                console.warn('Invalid message time:', message.time);
            } else {
                formattedTime = date.toLocaleString(undefined, {
                    hour: 'numeric',
                    minute: 'numeric',
                    hour12: true
                });
            }
        } catch (error) {
            console.warn('Error formatting message time:', error);
            formattedTime = 'Unknown Time';
        }
        
        const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
        
        return `
            <div class="message-bubble message-bubble--${bubbleClass}">
                <div class="message-text">${this.escapeHTML(message.text || '')}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                ${bubbleClass === 'outgoing' ? '<div class="message-status">Sent</div>' : ''}
            </div>
        `.trim();
    }

    // ... Rest of the class implementation remains the same ...
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

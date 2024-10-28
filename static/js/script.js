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

    initializeSearch() {
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                const contacts = this.elements.contactList.querySelectorAll('.contact-item');
                let hasResults = false;

                contacts.forEach(contact => {
                    const name = contact.querySelector('.contact-name').textContent.toLowerCase();
                    const preview = contact.querySelector('.contact-preview')?.textContent.toLowerCase() || '';
                    const isVisible = name.includes(query) || preview.includes(query);
                    contact.style.display = isVisible ? '' : 'none';
                    if (isVisible) hasResults = true;
                });

                this.toggleEmptyState(!hasResults, 'No contacts found');
            });
        }
    }

    toggleEmptyState(show, message) {
        let emptyState = this.elements.emptyState;
        if (!emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <i class="bi bi-chat-left-text"></i>
                <p class="empty-state-text"></p>
            `;
            this.elements.contactList.appendChild(emptyState);
            this.elements.emptyState = emptyState;
        }

        emptyState.style.display = show ? 'flex' : 'none';
        emptyState.querySelector('.empty-state-text').textContent = message;
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
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        await this.updateThemeIcon(savedTheme);
    }

    async updateThemeIcon(theme) {
        const iconElement = this.elements.themeIcon;
        if (iconElement) {
            iconElement.classList.remove('bi-sun-fill', 'bi-moon-fill');
            iconElement.classList.add(theme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill');
        }
    }

    async toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        await this.updateThemeIcon(newTheme);
    }

    setLoading(key, isLoading) {
        if (!this.elements.messagesList) return;

        if (isLoading) {
            const loader = document.createElement('div');
            loader.className = 'loading-spinner';
            loader.innerHTML = `
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            this.elements.messagesList.appendChild(loader);
        } else {
            const loader = this.elements.messagesList.querySelector('.loading-spinner');
            if (loader) loader.remove();
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

            this.elements.contacts.forEach(c => c.classList.remove('active'));
            contactElement.classList.add('active');

            this.currentContact = contact;
            
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            if (this.elements.contactsView) {
                this.elements.contactsView.classList.add('hidden');
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
        if (this.elements.chatView) {
            this.elements.chatView.classList.remove('active');
        }
        if (this.elements.contactsView) {
            this.elements.contactsView.classList.remove('hidden');
        }
        this.elements.contacts.forEach(c => c.classList.remove('active'));
        this.currentContact = null;
    }

    groupMessagesByDate(messages) {
        const groups = new Map();
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        messages.forEach(msg => {
            const date = new Date(msg.time);
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
        });

        return groups;
    }

    async loadMessages(contact) {
        try {
            this.setLoading(contact, true);

            const response = await fetch(`/messages/${contact}`);
            const messages = await response.json();
            
            if (!messages || messages.length === 0) {
                this.showEmptyMessages();
                return;
            }

            this.messageCache.set(contact, messages);
            
            if (this.elements.messagesList && this.currentContact === contact) {
                const messageGroups = this.groupMessagesByDate(messages);
                let html = '';

                for (const [date, msgs] of messageGroups) {
                    html += `<div class="date-header">${date}</div>`;
                    html += msgs.map(msg => this.createMessageBubble(msg)).join('');
                }

                this.elements.messagesList.innerHTML = html;
                this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showErrorState('Could not load messages');
        } finally {
            this.setLoading(contact, false);
        }
    }

    showEmptyMessages() {
        if (this.elements.messagesList) {
            this.elements.messagesList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-chat-left"></i>
                    <p>No messages yet</p>
                </div>
            `;
        }
    }

    showErrorState(message) {
        if (this.elements.messagesList) {
            this.elements.messagesList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-exclamation-circle"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    createMessageBubble(message) {
        const formattedTime = new Date(message.time).toLocaleString(undefined, {
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        });
        
        const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
        
        return `
            <div class="message-bubble message-bubble--${bubbleClass}">
                <div class="message-text">${this.escapeHTML(message.text || '')}</div>
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                ${bubbleClass === 'outgoing' ? '<div class="message-status">Sent</div>' : ''}
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

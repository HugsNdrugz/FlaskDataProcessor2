'use strict';

class ChatInterface {
    constructor() {
        // Initialize properties
        this.currentContact = null;
        this.elements = {};
        this.messageCache = new Map();
        this.isLoadingMore = false;

        // Bind methods
        this.handleScroll = this.handleScroll.bind(this);
        this.handleContactClick = this.handleContactClick.bind(this);
        this.handleBack = this.handleBack.bind(this);
        this.toggleTheme = this.toggleTheme.bind(this);
        this.parseTimestamp = this.parseTimestamp.bind(this);
        this.formatMessageTime = this.formatMessageTime.bind(this);
        this.createMessageBubble = this.createMessageBubble.bind(this);
        this.loadMessages = this.loadMessages.bind(this);
        this.escapeHTML = this.escapeHTML.bind(this);
        this.initializeSearch = this.initializeSearch.bind(this);

        // Initialize on DOM load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.initializeTheme();
        this.initializeSearch();
    }

    cacheElements() {
        const selectors = {
            contactsView: '#contactsView',
            chatView: '#chatView',
            contacts: '.contact-item',
            backButton: '.back-button',
            themeToggle: '.theme-toggle',
            messagesList: '.messages-list',
            messagesContainer: '.messages-container',
            searchInput: '.search-input',
            chatHeader: '.chat-header .contact-name'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            this.elements[key] = key === 'contacts' 
                ? document.querySelectorAll(selector)
                : document.querySelector(selector);
        }
    }

    parseTimestamp(timeStr) {
        try {
            if (!timeStr) return null;

            // Handle time-only format (HH:MM AM/PM)
            const timeOnlyRegex = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i;
            const timeOnlyMatch = timeStr.match(timeOnlyRegex);
            if (timeOnlyMatch) {
                const [_, hours, minutes, period] = timeOnlyMatch;
                const date = new Date();
                let hour = parseInt(hours, 10);
                
                if (period.toLowerCase() === 'pm' && hour < 12) {
                    hour += 12;
                } else if (period.toLowerCase() === 'am' && hour === 12) {
                    hour = 0;
                }
                
                date.setHours(hour, parseInt(minutes, 10), 0);
                return date;
            }

            // Handle date with time format
            const dateTimeRegex = /^([A-Za-z]+\s+\d{1,2}),\s*(\d{1,2}):(\d{2})\s*(AM|PM)$/i;
            const match = timeStr.match(dateTimeRegex);
            if (match) {
                const [_, dateStr, hours, minutes, period] = match;
                const currentYear = new Date().getFullYear();
                const fullDateStr = `${dateStr}, ${currentYear} ${hours}:${minutes} ${period}`;
                const parsedDate = new Date(fullDateStr);
                if (!isNaN(parsedDate.getTime())) {
                    return parsedDate;
                }
            }

            const parsedDate = new Date(timeStr);
            if (!isNaN(parsedDate.getTime())) {
                return parsedDate;
            }

            return new Date();
        } catch (error) {
            console.error('Error parsing timestamp:', error);
            return new Date();
        }
    }

    formatMessageTime(timestamp) {
        const date = this.parseTimestamp(timestamp);
        if (!date) return '';

        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === now.toDateString()) {
            return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday ' + date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
        } else {
            return date.toLocaleDateString([], { 
                month: 'short', 
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
        }
    }

    handleScroll() {
        if (!this.elements.messagesContainer || this.isLoadingMore) return;

        const { scrollTop } = this.elements.messagesContainer;
        if (scrollTop <= 100 && this.currentContact) {
            this.loadMoreMessages();
        }
    }

    loadMoreMessages() {
        if (this.isLoadingMore || !this.currentContact) return;
        this.isLoadingMore = true;

        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-spinner';
        loadingIndicator.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
        this.elements.messagesList.insertBefore(loadingIndicator, this.elements.messagesList.firstChild);

        fetch(`/messages/${this.currentContact}?before=${this.oldestMessageTime}`)
            .then(response => response.json())
            .then(messages => {
                loadingIndicator.remove();
                if (messages && messages.length > 0) {
                    messages.forEach(message => {
                        const bubble = this.createMessageBubble(message);
                        this.elements.messagesList.insertBefore(bubble, this.elements.messagesList.firstChild);
                    });
                    this.oldestMessageTime = messages[0].time;
                }
            })
            .catch(error => {
                console.error('Error loading more messages:', error);
                loadingIndicator.remove();
            })
            .finally(() => {
                this.isLoadingMore = false;
            });
    }

    loadMessages(contact) {
        if (!this.elements.messagesList) return;

        this.elements.messagesList.innerHTML = `
            <div class="loading-spinner">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;

        fetch(`/messages/${contact}`)
            .then(response => response.json())
            .then(messages => {
                this.elements.messagesList.innerHTML = '';
                if (!messages || messages.length === 0) {
                    this.elements.messagesList.innerHTML = '<div class="no-messages">No messages yet</div>';
                    return;
                }

                messages.forEach(message => {
                    const bubble = this.createMessageBubble(message);
                    this.elements.messagesList.appendChild(bubble);
                });
                this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
                this.oldestMessageTime = messages[0].time;
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                this.elements.messagesList.innerHTML = '<div class="error">Error loading messages</div>';
            });
    }

    createMessageBubble(message) {
        const bubble = document.createElement('div');
        const isSender = message.sender === this.currentContact;
        bubble.className = `message-bubble message-bubble--${isSender ? 'incoming' : 'outgoing'}`;
        
        const formattedTime = this.formatMessageTime(message.time);
        bubble.innerHTML = `
            <div class="message-text">${this.escapeHTML(message.text)}</div>
            <time class="message-time" datetime="${message.time}">${formattedTime}</time>
            ${!isSender ? '<div class="message-status">Sent</div>' : ''}
        `;
        
        return bubble;
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    handleContactClick(event) {
        const contactElement = event.currentTarget;
        const contact = contactElement.dataset.contact;
        if (!contact) return;

        this.elements.contacts?.forEach(c => c.classList.remove('active'));
        contactElement.classList.add('active');
        this.currentContact = contact;
        
        if (this.elements.chatHeader) {
            this.elements.chatHeader.textContent = contactElement.querySelector('.contact-name').textContent;
        }

        this.elements.contactsView?.classList.add('hidden');
        this.elements.chatView?.classList.add('active');
        
        this.loadMessages(contact);
    }

    handleBack() {
        this.elements.chatView?.classList.remove('active');
        this.elements.contactsView?.classList.remove('hidden');
        this.elements.contacts?.forEach(c => c.classList.remove('active'));
        this.currentContact = null;
    }

    initializeSearch() {
        if (!this.elements.searchInput) return;

        let searchTimeout;
        this.elements.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = e.target.value.toLowerCase();
                this.elements.contacts?.forEach(contact => {
                    const name = contact.querySelector('.contact-name')?.textContent.toLowerCase() || '';
                    const preview = contact.querySelector('.contact-preview')?.textContent.toLowerCase() || '';
                    contact.style.display = name.includes(query) || preview.includes(query) ? '' : 'none';
                });
            }, 300);
        });
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        const icon = this.elements.themeToggle?.querySelector('i');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
        }
    }

    bindEvents() {
        this.elements.contacts?.forEach(contact => {
            contact.addEventListener('click', this.handleContactClick);
        });

        this.elements.backButton?.addEventListener('click', this.handleBack);
        this.elements.themeToggle?.addEventListener('click', this.toggleTheme);
        this.elements.messagesContainer?.addEventListener('scroll', this.handleScroll);
    }
}

// Initialize the chat interface
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});

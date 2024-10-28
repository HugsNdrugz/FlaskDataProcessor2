'use strict';

class ChatInterface {
    constructor() {
        try {
            // Initialize properties
            this.currentContact = null;
            this.elements = {};
            this.messageCache = new Map();
            this.loadingStates = new Set();
            this.isLoadingMore = false;
            this.pageSize = 20;
            this.currentPage = 1;

            // Define all methods first
            this.handleScroll = this.handleScroll.bind(this);
            this.handleContactClick = this.handleContactClick.bind(this);
            this.handleBack = this.handleBack.bind(this);
            this.toggleTheme = this.toggleTheme.bind(this);
            this.initializeSearch = this.initializeSearch.bind(this);
            this.setupContactsList = this.setupContactsList.bind(this);
            this.loadMessages = this.loadMessages.bind(this);
            this.loadMoreMessages = this.loadMoreMessages.bind(this);
            this.groupMessagesByDate = this.groupMessagesByDate.bind(this);
            this.createMessageBubble = this.createMessageBubble.bind(this);
            this.escapeHTML = this.escapeHTML.bind(this);
            this.toggleEmptyState = this.toggleEmptyState.bind(this);
            this.updateThemeIcon = this.updateThemeIcon.bind(this);
            this.initializeTheme = this.initializeTheme.bind(this);
            this.cacheElements = this.cacheElements.bind(this);

            // Initialize chat interface
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
            } else {
                this.init();
            }
        } catch (error) {
            console.error('Error in ChatInterface constructor:', error);
            throw error;
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
            throw error;
        }
    }

    async cacheElements() {
        try {
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
        } catch (error) {
            console.error('Error caching elements:', error);
            throw error;
        }
    }

    async initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme');
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            const theme = savedTheme || systemTheme;

            document.documentElement.setAttribute('data-theme', theme);
            this.updateThemeIcon(theme);

            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    document.documentElement.setAttribute('data-theme', newTheme);
                    this.updateThemeIcon(newTheme);
                }
            });
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    updateThemeIcon(theme) {
        try {
            if (this.elements.themeIcon) {
                this.elements.themeIcon.className = theme === 'dark' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
            }
        } catch (error) {
            console.error('Error updating theme icon:', error);
        }
    }

    toggleTheme() {
        try {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.updateThemeIcon(newTheme);
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    setupContactsList() {
        try {
            if (!this.elements.contacts) return;

            this.elements.contacts.forEach(contact => {
                const avatar = contact.querySelector('.contact-avatar');
                const nameElement = contact.querySelector('.contact-name');
                if (avatar && nameElement) {
                    const name = nameElement.textContent.trim();
                    avatar.textContent = name.charAt(0).toUpperCase();
                }

                contact.addEventListener('click', () => {
                    contact.classList.add('loading');
                    setTimeout(() => contact.classList.remove('loading'), 1000);
                });
            });
        } catch (error) {
            console.error('Error setting up contacts list:', error);
        }
    }

    initializeSearch() {
        try {
            if (!this.elements.searchInput || !this.elements.contacts) return;

            let searchTimeout;
            const debounceDelay = 300;

            this.elements.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    const query = e.target.value.toLowerCase();
                    let hasResults = false;

                    this.elements.contacts.forEach(contact => {
                        const name = contact.querySelector('.contact-name')?.textContent.toLowerCase() || '';
                        const preview = contact.querySelector('.contact-preview')?.textContent.toLowerCase() || '';
                        const isVisible = name.includes(query) || preview.includes(query);
                        contact.style.display = isVisible ? '' : 'none';
                        if (isVisible) hasResults = true;
                    });

                    this.toggleEmptyState(!hasResults, 'No contacts found');
                }, debounceDelay);
            });
        } catch (error) {
            console.error('Error initializing search:', error);
        }
    }

    toggleEmptyState(show, message) {
        try {
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
        } catch (error) {
            console.error('Error toggling empty state:', error);
        }
    }

    parseTimestamp(timeStr) {
        try {
            if (!timeStr) return null;

            const timeRegex = /(\d{1,2}):(\d{2})\s*(AM|PM)/i;
            const match = timeStr.match(timeRegex);
            
            if (match) {
                const [_, hours, minutes, period] = match;
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

            const parsedDate = new Date(timeStr);
            if (!isNaN(parsedDate.getTime())) {
                return parsedDate;
            }

            const currentDate = new Date();
            currentDate.setHours(0, 0, 0, 0);
            return currentDate;

        } catch (error) {
            console.error('Error parsing timestamp:', error);
            return new Date();
        }
    }

    formatMessageTime(timestamp) {
        try {
            const date = this.parseTimestamp(timestamp);
            if (!date) return 'Invalid time';

            return date.toLocaleString(undefined, {
                hour: 'numeric',
                minute: 'numeric',
                hour12: true
            });
        } catch (error) {
            console.error('Error formatting message time:', error);
            return 'Unknown time';
        }
    }

    async loadMoreMessages() {
        if (this.isLoadingMore || !this.currentContact) return;

        try {
            this.isLoadingMore = true;
            const oldScrollHeight = this.elements.messagesContainer.scrollHeight;

            const loader = document.createElement('div');
            loader.className = 'loading-spinner top';
            loader.innerHTML = `
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            `;
            this.elements.messagesList.insertBefore(loader, this.elements.messagesList.firstChild);

            const response = await fetch(`/messages/${this.currentContact}?page=${++this.currentPage}&size=${this.pageSize}`);
            const messages = await response.json();

            if (messages && messages.length > 0) {
                const messageGroups = this.groupMessagesByDate(messages);
                let html = '';
                
                for (const [date, msgs] of messageGroups) {
                    html += `<div class="date-header">${date}</div>`;
                    html += msgs.map(msg => this.createMessageBubble(msg)).join('');
                }

                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                while (tempDiv.firstChild) {
                    this.elements.messagesList.insertBefore(tempDiv.firstChild, this.elements.messagesList.firstChild);
                }

                const newScrollHeight = this.elements.messagesContainer.scrollHeight;
                this.elements.messagesContainer.scrollTop = newScrollHeight - oldScrollHeight;
            }
        } catch (error) {
            console.error('Error loading more messages:', error);
        } finally {
            this.isLoadingMore = false;
            const loader = this.elements.messagesList.querySelector('.loading-spinner.top');
            if (loader) loader.remove();
        }
    }

    escapeHTML(str) {
        try {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        } catch (error) {
            console.error('Error escaping HTML:', error);
            return '';
        }
    }

    handleBack() {
        try {
            if (this.elements.chatView) {
                this.elements.chatView.classList.remove('active');
            }
            if (this.elements.contactsView) {
                this.elements.contactsView.classList.remove('hidden');
            }
            this.elements.contacts?.forEach(c => c.classList.remove('active'));
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back action:', error);
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

            this.elements.contacts?.forEach(c => c.classList.remove('active'));
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

    async loadMessages(contact) {
        try {
            if (!this.elements.messagesList) return;

            this.elements.messagesList.innerHTML = `
                <div class="loading-spinner">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            `;

            const response = await fetch(`/messages/${contact}`);
            const messages = await response.json();

            if (!messages || messages.length === 0) {
                this.toggleEmptyState(true, 'No messages yet');
                return;
            }

            this.messageCache.set(contact, messages);
            
            if (this.currentContact === contact) {
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
            this.toggleEmptyState(true, 'Could not load messages');
        }
    }

    bindEvents() {
        try {
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

            if (this.elements.messagesContainer) {
                this.elements.messagesContainer.addEventListener('scroll', this.handleScroll);
            }
        } catch (error) {
            console.error('Error binding events:', error);
        }
    }

    handleScroll() {
        try {
            if (!this.elements.messagesContainer || this.isLoadingMore) return;

            const { scrollTop, scrollHeight, clientHeight } = this.elements.messagesContainer;
            
            if (scrollTop <= 100 && this.currentContact) {
                this.loadMoreMessages();
            }
        } catch (error) {
            console.error('Error handling scroll:', error);
        }
    }

    groupMessagesByDate(messages) {
        try {
            const groups = new Map();
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);

            messages.forEach(msg => {
                try {
                    const date = this.parseTimestamp(msg.time);
                    
                    if (!date) {
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
                            weekday: 'long',
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
        } catch (error) {
            console.error('Error grouping messages by date:', error);
            return new Map();
        }
    }

    createMessageBubble(message) {
        try {
            const formattedTime = this.formatMessageTime(message.time);
            const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
            
            return `
                <div class="message-bubble message-bubble--${bubbleClass}">
                    <div class="message-text">${this.escapeHTML(message.text || '')}</div>
                    <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                    ${bubbleClass === 'outgoing' ? '<div class="message-status">Sent</div>' : ''}
                </div>
            `.trim();
        } catch (error) {
            console.error('Error creating message bubble:', error);
            return `
                <div class="message-bubble message-bubble--error">
                    <div class="message-text">Error displaying message</div>
                </div>
            `;
        }
    }
}

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
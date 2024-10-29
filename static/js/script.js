'use strict';

class ChatInterface {
    constructor() {
        // Initialize properties
        this.currentContact = null;
        this.messageCache = new Map();
        this.isLoadingMore = false;
        this.oldestMessageTime = null;
        this.messageGroups = new Map();
        
        // Bind methods to preserve context
        this.handleScroll = this.handleScroll.bind(this);
        this.handleContactClick = this.handleContactClick.bind(this);
        this.handleBack = this.handleBack.bind(this);
        this.toggleTheme = this.toggleTheme.bind(this);
        this.parseTimestamp = this.parseTimestamp.bind(this);
        this.formatMessageTime = this.formatMessageTime.bind(this);
        this.createMessageBubble = this.createMessageBubble.bind(this);
        this.loadMessages = this.loadMessages.bind(this);
        this.initializeElements = this.initializeElements.bind(this);
        this.updateOnlineStatus = this.updateOnlineStatus.bind(this);
        
        // Initialize on DOM load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        this.initializeElements();
        this.bindEvents();
        this.initializeTheme();
        this.updateOnlineStatus();
        setInterval(this.updateOnlineStatus, 60000); // Update online status every minute
    }

    initializeElements() {
        this.elements = {
            contactsView: document.querySelector('#contactsView'),
            chatView: document.querySelector('#chatView'),
            contacts: document.querySelectorAll('.contact-item'),
            backButton: document.querySelector('.back-button'),
            themeToggle: document.querySelector('.theme-toggle'),
            messagesList: document.querySelector('.messages-list'),
            messagesContainer: document.querySelector('.messages-container'),
            searchInput: document.querySelector('.search-input'),
            chatHeader: document.querySelector('.chat-header .contact-name'),
            onlineStatus: document.querySelector('.online-status')
        };
    }

    parseTimestamp(timeStr) {
        if (!timeStr) return null;
        try {
            const date = new Date(timeStr);
            return isNaN(date.getTime()) ? new Date() : date;
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
        
        const timeOptions = { hour: 'numeric', minute: '2-digit', hour12: true };
        
        if (date.toDateString() === now.toDateString()) {
            return date.toLocaleTimeString([], timeOptions);
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday ' + date.toLocaleTimeString([], timeOptions);
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

    createMessageGroup(messages) {
        const groups = [];
        let currentGroup = [];
        let lastSender = null;
        let lastTime = null;

        messages.forEach(message => {
            const messageTime = this.parseTimestamp(message.time);
            const timeDiff = lastTime ? (messageTime - lastTime) / 1000 / 60 : 0;

            if (lastSender !== message.sender || timeDiff > 2) {
                if (currentGroup.length > 0) {
                    groups.push(currentGroup);
                }
                currentGroup = [message];
            } else {
                currentGroup.push(message);
            }

            lastSender = message.sender;
            lastTime = messageTime;
        });

        if (currentGroup.length > 0) {
            groups.push(currentGroup);
        }

        return groups;
    }

    createMessageBubble(message, isFirstInGroup, isLastInGroup) {
        const bubble = document.createElement('div');
        const isSender = message.sender === this.currentContact;
        bubble.className = `message-bubble message-bubble--${isSender ? 'incoming' : 'outgoing'}`;
        
        if (isFirstInGroup) bubble.classList.add('first-in-group');
        if (isLastInGroup) bubble.classList.add('last-in-group');

        const formattedTime = this.formatMessageTime(message.time);
        
        bubble.innerHTML = `
            <div class="message-text">${this.escapeHTML(message.text)}</div>
            ${isLastInGroup ? `
                <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                ${!isSender ? '<div class="message-status">Sent · Delivered · Read</div>' : ''}
            ` : ''}
        `;

        return bubble;
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

                const messageGroups = this.createMessageGroup(messages);
                const fragment = document.createDocumentFragment();

                messageGroups.forEach(group => {
                    const groupDiv = document.createElement('div');
                    groupDiv.className = 'message-group';

                    group.forEach((message, index) => {
                        const bubble = this.createMessageBubble(
                            message,
                            index === 0,
                            index === group.length - 1
                        );
                        groupDiv.appendChild(bubble);
                    });

                    fragment.appendChild(groupDiv);
                });

                this.elements.messagesList.appendChild(fragment);
                this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
                this.oldestMessageTime = messages[0].time;
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                this.elements.messagesList.innerHTML = '<div class="error">Error loading messages</div>';
            });
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
        this.currentContact = null;
    }

    handleScroll() {
        if (!this.elements.messagesContainer || this.isLoadingMore) return;

        const { scrollTop } = this.elements.messagesContainer;
        if (scrollTop <= 100 && this.currentContact) {
            this.loadMoreMessages();
        }
    }

    updateOnlineStatus() {
        if (!this.elements.onlineStatus) return;
        const randomStatus = Math.random() > 0.5;
        this.elements.onlineStatus.textContent = randomStatus ? 'Active Now' : 'Active 2m ago';
        this.elements.onlineStatus.className = `online-status ${randomStatus ? 'active' : ''}`;
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

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    bindEvents() {
        this.elements.contacts?.forEach(contact => {
            contact.addEventListener('click', this.handleContactClick);
        });

        this.elements.backButton?.addEventListener('click', this.handleBack);
        this.elements.themeToggle?.addEventListener('click', this.toggleTheme);
        this.elements.messagesContainer?.addEventListener('scroll', this.handleScroll);

        if (this.elements.searchInput) {
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
    }
}

// Initialize the chat interface
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});

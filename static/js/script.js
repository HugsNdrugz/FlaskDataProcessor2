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
        this.formatMessageTime = this.formatMessageTime.bind(this);
        this.createMessageBubble = this.createMessageBubble.bind(this);
        this.loadMessages = this.loadMessages.bind(this);
        this.loadMoreMessages = this.loadMoreMessages.bind(this);
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
            onlineStatus: document.querySelector('.online-status'),
            loadingSpinner: document.querySelector('.loading-spinner')
        };
    }

    loadMoreMessages() {
        if (this.isLoadingMore || !this.currentContact || !this.oldestMessageTime) return;
        
        this.isLoadingMore = true;
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'loading-spinner';
        loadingSpinner.innerHTML = `
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        
        this.elements.messagesList.insertBefore(loadingSpinner, this.elements.messagesList.firstChild);
        
        const scrollHeight = this.elements.messagesContainer.scrollHeight;
        
        fetch(`/messages/${encodeURIComponent(this.currentContact)}?before=${this.oldestMessageTime}`)
            .then(response => {
                if (!response.ok) throw new Error('Failed to load messages');
                return response.json();
            })
            .then(messages => {
                loadingSpinner.remove();
                if (messages && messages.length > 0) {
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
                    
                    this.elements.messagesList.insertBefore(fragment, this.elements.messagesList.firstChild);
                    this.oldestMessageTime = messages[0].time;
                    
                    // Maintain scroll position
                    const newScrollHeight = this.elements.messagesContainer.scrollHeight;
                    this.elements.messagesContainer.scrollTop = newScrollHeight - scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error loading more messages:', error);
                loadingSpinner.remove();
                // Show error toast
                const errorToast = document.createElement('div');
                errorToast.className = 'error-toast';
                errorToast.textContent = 'Failed to load messages';
                document.body.appendChild(errorToast);
                setTimeout(() => errorToast.remove(), 3000);
            })
            .finally(() => {
                this.isLoadingMore = false;
            });
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

    formatMessageTime(timeStr) {
        const date = this.parseTimestamp(timeStr);
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
        if (!contact) return;
        
        this.elements.messagesList.innerHTML = '';
        this.elements.chatHeader.textContent = contact;
        this.elements.messagesContainer.scrollTop = 0;
        this.oldestMessageTime = null;
        this.isLoadingMore = false;

        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'loading-spinner centered';
        loadingSpinner.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
        this.elements.messagesList.appendChild(loadingSpinner);

        fetch(`/messages/${encodeURIComponent(contact)}`)
            .then(response => {
                if (!response.ok) throw new Error('Failed to load messages');
                return response.json();
            })
            .then(messages => {
                loadingSpinner.remove();
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
                loadingSpinner.remove();
                this.elements.messagesList.innerHTML = '<div class="error-message">Failed to load messages</div>';
            });
    }

    handleContactClick(event) {
        const contactElement = event.currentTarget;
        const contact = contactElement.dataset.contact;
        
        if (contact === this.currentContact) return;
        
        this.currentContact = contact;
        this.elements.chatView?.classList.add('active');
        this.elements.contactsView?.classList.add('hidden');
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
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
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
new ChatInterface();

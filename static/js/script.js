class ChatInterface {
    constructor() {
        try {
            console.log('Initializing ChatInterface...');
            
            // Bind all methods
            this.init = this.init.bind(this);
            this.initializeElements = this.initializeElements.bind(this);
            this.bindEvents = this.bindEvents.bind(this);
            this.handleContactClick = this.handleContactClick.bind(this);
            this.handleBack = this.handleBack.bind(this);
            this.handleScroll = this.handleScroll.bind(this);
            this.toggleTheme = this.toggleTheme.bind(this);
            this.loadMessages = this.loadMessages.bind(this);
            this.loadMoreMessages = this.loadMoreMessages.bind(this);
            this.createMessageBubble = this.createMessageBubble.bind(this);
            this.createMessageGroup = this.createMessageGroup.bind(this);
            this.formatMessageTime = this.formatMessageTime.bind(this);
            this.parseTimestamp = this.parseTimestamp.bind(this);
            this.updateOnlineStatus = this.updateOnlineStatus.bind(this);
            this.escapeHTML = this.escapeHTML.bind(this);

            // Initialize state
            this.currentContact = null;
            this.isLoadingMore = false;
            this.oldestMessageTime = null;

            // Initialize on DOM load
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', this.init);
            } else {
                this.init();
            }

            console.log('ChatInterface constructor completed successfully');
        } catch (error) {
            console.error('Error in ChatInterface constructor:', error);
            throw error;
        }
    }

    init() {
        try {
            console.log('Initializing chat interface...');
            this.initializeElements();
            this.bindEvents();
            this.initializeTheme();
            this.updateOnlineStatus();
            setInterval(this.updateOnlineStatus, 60000);
            console.log('Chat interface initialized successfully');
        } catch (error) {
            console.error('Error initializing chat interface:', error);
        }
    }

    initializeElements() {
        try {
            console.log('Initializing DOM elements...');
            this.elements = {
                contactsView: document.querySelector('.contacts-view'),
                chatView: document.querySelector('.chat-view'),
                backButton: document.querySelector('.back-button'),
                themeToggle: document.querySelector('.theme-toggle'),
                contacts: Array.from(document.querySelectorAll('.contact-item')),
                messagesList: document.querySelector('.messages-list'),
                messagesContainer: document.querySelector('.messages-container'),
                searchInput: document.querySelector('.search-input'),
                chatHeader: document.querySelector('.chat-header .contact-name'),
                onlineStatus: document.querySelector('.online-status'),
                tabButtons: document.querySelectorAll('.nav-link'),
                loadingSpinner: document.querySelector('.loading-spinner')
            };

            // Debug log element initialization
            Object.entries(this.elements).forEach(([key, element]) => {
                if (element === null) {
                    console.warn(`Element "${key}" not found in DOM`);
                } else {
                    console.log(`Element "${key}" initialized successfully`);
                }
            });
        } catch (error) {
            console.error('Error initializing elements:', error);
            throw error;
        }
    }

    bindEvents() {
        try {
            console.log('Binding events...');
            
            // Contact clicks
            this.elements.contacts?.forEach(contact => {
                contact.addEventListener('click', this.handleContactClick);
            });

            // Navigation
            this.elements.backButton?.addEventListener('click', this.handleBack);
            this.elements.themeToggle?.addEventListener('click', this.toggleTheme);
            this.elements.messagesContainer?.addEventListener('scroll', this.handleScroll);

            // Tab navigation
            this.elements.tabButtons?.forEach(button => {
                button.addEventListener('click', (e) => {
                    this.elements.tabButtons.forEach(btn => btn.classList.remove('active'));
                    e.target.classList.add('active');
                });
            });

            // Search functionality
            if (this.elements.searchInput) {
                let searchTimeout;
                this.elements.searchInput.addEventListener('input', (e) => {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        const query = e.target.value.toLowerCase();
                        this.elements.contacts?.forEach(contact => {
                            const name = contact.querySelector('.contact-name')?.textContent.toLowerCase() || '';
                            const preview = contact.querySelector('.message-preview')?.textContent.toLowerCase() || '';
                            contact.style.display = name.includes(query) || preview.includes(query) ? '' : 'none';
                        });
                    }, 300);
                });
            }

            console.log('Events bound successfully');
        } catch (error) {
            console.error('Error binding events:', error);
        }
    }

    handleContactClick(event) {
        try {
            const contactElement = event.currentTarget;
            const contact = contactElement.dataset.contact;
            
            if (!contact || contact === this.currentContact) return;
            
            console.log('Switching to contact:', contact);
            this.currentContact = contact;
            
            // Update UI
            this.elements.chatView?.classList.add('active');
            this.elements.contactsView?.classList.add('hidden');
            this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
        }
    }

    handleBack() {
        try {
            console.log('Navigating back to contacts view');
            this.elements.chatView?.classList.remove('active');
            this.elements.contactsView?.classList.remove('hidden');
            this.currentContact = null;
        } catch (error) {
            console.error('Error handling back navigation:', error);
        }
    }

    handleScroll() {
        try {
            if (!this.elements.messagesContainer || this.isLoadingMore) {
                return;
            }

            const { scrollTop } = this.elements.messagesContainer;
            if (scrollTop <= 100 && this.currentContact) {
                console.log('Loading more messages...');
                this.loadMoreMessages();
            }
        } catch (error) {
            console.error('Error handling scroll:', error);
        }
    }

    loadMoreMessages() {
        if (this.isLoadingMore || !this.currentContact || !this.oldestMessageTime) {
            console.log('Skipping loadMoreMessages - conditions not met');
            return;
        }

        console.log('Loading more messages for:', this.currentContact);
        this.isLoadingMore = true;

        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'loading-spinner';
        loadingSpinner.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
        this.elements.messagesList.insertBefore(loadingSpinner, this.elements.messagesList.firstChild);

        const scrollHeight = this.elements.messagesContainer.scrollHeight;

        fetch(`/messages/${encodeURIComponent(this.currentContact)}?before=${this.oldestMessageTime}`)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
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
                            const bubble = this.createMessageBubble(message, index === 0, index === group.length - 1);
                            groupDiv.appendChild(bubble);
                        });

                        fragment.appendChild(groupDiv);
                    });

                    this.elements.messagesList.insertBefore(fragment, this.elements.messagesList.firstChild);
                    this.oldestMessageTime = messages[0].time;

                    const newScrollHeight = this.elements.messagesContainer.scrollHeight;
                    this.elements.messagesContainer.scrollTop = newScrollHeight - scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error loading more messages:', error);
                loadingSpinner.remove();
                this.showError('Failed to load messages');
            })
            .finally(() => {
                this.isLoadingMore = false;
            });
    }

    showError(message) {
        const errorToast = document.createElement('div');
        errorToast.className = 'error-toast';
        errorToast.textContent = message;
        document.body.appendChild(errorToast);
        setTimeout(() => errorToast.remove(), 3000);
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
        if (!contact) return;
        
        console.log('Loading messages for contact:', contact);
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

    updateOnlineStatus() {
        try {
            if (!this.elements.onlineStatus) return;
            const randomStatus = Math.random() > 0.5;
            this.elements.onlineStatus.textContent = randomStatus ? 'Active Now' : 'Active 2m ago';
            this.elements.onlineStatus.className = `online-status ${randomStatus ? 'active' : ''}`;
        } catch (error) {
            console.error('Error updating online status:', error);
        }
    }

    initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    toggleTheme() {
        try {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        } catch (error) {
            console.error('Error toggling theme:', error);
        }
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize the chat interface with proper error handling
try {
    console.log('Creating new ChatInterface instance');
    window.chatInterface = new ChatInterface();
} catch (error) {
    console.error('Error initializing ChatInterface:', error);
}

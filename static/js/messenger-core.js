class ChatInterface {
    constructor() {
        console.log("Creating new ChatInterface instance");
        this.initialize();
    }

    initialize() {
        console.log("Initializing ChatInterface...");
        this.initializeDOM();
        this.bindEvents();
        this.loadContacts();
        console.log("Chat interface initialized successfully");
    }

    initializeDOM() {
        console.log("Initializing DOM elements...");
        
        // Views
        this.contactsView = document.querySelector('.contacts-view');
        console.log('Element "contactsView" initialized successfully');
        
        this.chatView = document.querySelector('.chat-view');
        console.log('Element "chatView" initialized successfully');
        
        // Buttons and Controls
        this.backButton = document.querySelector('.back-button');
        console.log('Element "backButton" initialized successfully');
        
        this.themeToggle = document.querySelector('.theme-toggle');
        console.log('Element "themeToggle" initialized successfully');
        
        // Lists and Containers
        this.contacts = document.querySelector('.contacts-list');
        console.log('Element "contacts" initialized successfully');
        
        this.messagesList = document.querySelector('.messages-list');
        console.log('Element "messagesList" initialized successfully');
        
        this.messagesContainer = document.querySelector('.messages-container');
        console.log('Element "messagesContainer" initialized successfully');
        
        // Input Elements
        this.searchInput = document.querySelector('.search-input');
        console.log('Element "searchInput" initialized successfully');
        
        // Headers and Status
        this.chatHeader = document.querySelector('.chat-header .contact-name');
        console.log('Element "chatHeader" initialized successfully');
        
        this.onlineStatus = document.querySelector('.online-status');
        console.log('Element "onlineStatus" initialized successfully');
        
        // Tabs
        this.tabButtons = document.querySelectorAll('.nav-link');
        console.log('Element "tabButtons" initialized successfully');
        
        // Loading States
        this.loadingSpinner = this.createLoadingSpinner();
        console.log('Element "loadingSpinner" initialized successfully');
    }

    createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        return spinner;
    }

    bindEvents() {
        console.log("Binding events...");
        
        // Theme Toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Back Button
        this.backButton.addEventListener('click', () => this.showContactsView());
        
        // Search
        this.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        
        // Tab Navigation
        this.tabButtons.forEach(button => {
            button.addEventListener('click', () => this.handleTabClick(button));
        });
        
        console.log("Events bound successfully");
    }

    toggleTheme() {
        const body = document.body;
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    showContactsView() {
        this.contactsView.classList.remove('hidden');
        this.chatView.classList.remove('active');
    }

    showChatView(contact) {
        this.contactsView.classList.add('hidden');
        this.chatView.classList.add('active');
        this.chatHeader.textContent = contact.name;
        this.loadMessages(contact.id);
    }

    handleSearch(query) {
        query = query.toLowerCase();
        const items = this.contacts.querySelectorAll('.contact-item');
        
        items.forEach(item => {
            const name = item.querySelector('.contact-name').textContent.toLowerCase();
            const preview = item.querySelector('.message-preview').textContent.toLowerCase();
            
            if (name.includes(query) || preview.includes(query)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    handleTabClick(clickedTab) {
        this.tabButtons.forEach(tab => {
            tab.classList.remove('active');
        });
        clickedTab.classList.add('active');
    }

    async loadContacts() {
        try {
            const response = await fetch('/api/contacts');
            const contacts = await response.json();
            this.renderContacts(contacts);
        } catch (error) {
            console.error('Error loading contacts:', error);
            this.showError('Failed to load contacts');
        }
    }

    async loadMessages(contactId) {
        try {
            const response = await fetch(`/api/messages/${contactId}`);
            const messages = await response.json();
            this.renderMessages(messages);
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Failed to load messages');
        }
    }

    renderContacts(contacts) {
        this.contacts.innerHTML = '';
        contacts.forEach(contact => {
            const contactElement = this.createContactElement(contact);
            this.contacts.appendChild(contactElement);
        });
    }

    renderMessages(messages) {
        this.messagesList.innerHTML = '';
        let currentGroup = null;
        
        messages.forEach(message => {
            if (!currentGroup || currentGroup.sender !== message.sender) {
                currentGroup = this.createMessageGroup(message.sender);
                this.messagesList.appendChild(currentGroup);
            }
            
            const messageElement = this.createMessageElement(message);
            currentGroup.querySelector('.message-group-content').appendChild(messageElement);
        });
        
        this.scrollToBottom();
    }

    createContactElement(contact) {
        const element = document.createElement('div');
        element.className = 'contact-item';
        element.innerHTML = `
            <div class="avatar">
                <img src="${contact.avatar || '/static/images/default-avatar.png'}" alt="${contact.name}">
                ${contact.online ? '<div class="online-indicator"></div>' : ''}
            </div>
            <div class="contact-info">
                <div class="contact-name">${contact.name}</div>
                <div class="message-preview">${contact.lastMessage || ''}</div>
            </div>
        `;
        
        element.addEventListener('click', () => this.showChatView(contact));
        return element;
    }

    createMessageGroup(sender) {
        const group = document.createElement('div');
        group.className = 'message-group';
        group.innerHTML = `
            <div class="message-group-content"></div>
        `;
        group.sender = sender;
        return group;
    }

    createMessageElement(message) {
        const element = document.createElement('div');
        element.className = `message-bubble message-bubble--${message.outgoing ? 'outgoing' : 'incoming'}`;
        element.textContent = message.content;
        return element;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    showError(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    showLoading(container) {
        container.appendChild(this.loadingSpinner.cloneNode(true));
    }

    hideLoading(container) {
        const spinner = container.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Initialize the chat interface when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});

'use strict';

class ChatInterface {
    constructor() {
        this.currentContact = null;
        this.elements = {};
        this.retryCount = 0;
        this.maxRetries = 3;
        this.socket = null;
        
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    handleError(error) {
        console.error('Error:', error);
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            console.log(`Retrying (${this.retryCount}/${this.maxRetries})...`);
            setTimeout(() => this.init(), 2000 * this.retryCount);
        } else {
            const messagesList = document.querySelector('.messages-list');
            if (messagesList) {
                messagesList.innerHTML = '<div class="alert alert-danger">Connection failed. Please refresh the page.</div>';
            }
        }
    }

    async init() {
        try {
            await this.cacheElements();
            await this.initializeTheme();
            this.bindEvents();
            this.initializeUpload();
            this.retryCount = 0;
        } catch (error) {
            this.handleError(error);
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
            fileUpload: '#fileUpload',
            uploadButton: '#uploadButton',
            uploadForm: '#uploadForm',
            uploadModal: '#uploadModal',
            errorModal: '#errorModal',
            errorMessage: '#errorMessage'
        };

        for (const [key, selector] of Object.entries(selectors)) {
            this.elements[key] = key === 'contacts' 
                ? document.querySelectorAll(selector)
                : document.querySelector(selector);
            
            if (!this.elements[key] && key !== 'contacts') {
                console.warn(`Element not found: ${selector}`);
            }
        }
    }

    bindEvents() {
        if (this.elements.contacts?.length) {
            this.elements.contacts.forEach(contact => {
                contact?.addEventListener('click', (e) => this.handleContactClick(e));
            });
        }

        this.elements.backButton?.addEventListener('click', () => this.handleBack());
        this.elements.themeToggle?.addEventListener('click', () => this.toggleTheme());
    }

    initializeUpload() {
        if (this.elements.uploadButton && this.elements.fileUpload) {
            // Show upload button only in contacts view
            this.elements.uploadForm.style.display = 
                this.elements.contactsView.classList.contains('active') ? 'inline-block' : 'none';

            this.elements.uploadButton.addEventListener('click', () => {
                this.elements.fileUpload.click();
            });

            this.elements.fileUpload.addEventListener('change', async (e) => {
                await this.handleFileUpload(e);
            });
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.match(/\.(csv|xlsx)$/i)) {
            this.showError('Please select a CSV or Excel file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Show upload modal with loading state
            const uploadModal = new bootstrap.Modal(this.elements.uploadModal);
            uploadModal.show();

            // Disable upload button during upload
            this.elements.uploadButton.disabled = true;
            this.elements.uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Uploading...';

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Upload failed');
            }

            // Reload the page to show new data
            window.location.reload();
        } catch (error) {
            this.showError(error.message || 'Failed to upload file');
        } finally {
            // Reset file input and button state
            this.elements.fileUpload.value = '';
            this.elements.uploadButton.disabled = false;
            this.elements.uploadButton.innerHTML = '<i class="bi bi-upload me-1"></i> Import Data';
            
            // Hide upload modal
            const uploadModal = bootstrap.Modal.getInstance(this.elements.uploadModal);
            if (uploadModal) {
                uploadModal.hide();
            }
        }
    }

    showError(message) {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.textContent = message;
            const errorModal = new bootstrap.Modal(this.elements.errorModal);
            errorModal.show();
        }
    }

    async initializeTheme() {
        try {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            await this.updateThemeIcon(savedTheme);
        } catch (error) {
            console.error('Error initializing theme:', error);
        }
    }

    async updateThemeIcon(theme) {
        const iconElement = this.elements.themeIcon;
        if (!iconElement) return;

        iconElement.classList.remove('bi-sun-fill', 'bi-moon-fill');
        iconElement.classList.add(theme === 'dark' ? 'bi-moon-fill' : 'bi-sun-fill');
    }

    async toggleTheme() {
        try {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
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

            if (!contact || !contactName) return;

            this.currentContact = contact;
            
            if (this.elements.chatContactName) {
                this.elements.chatContactName.textContent = contactName;
            }

            // Hide upload button in chat view
            if (this.elements.uploadForm) {
                this.elements.uploadForm.style.display = 'none';
            }

            this.elements.contactsView?.classList.remove('active');
            this.elements.chatView?.classList.add('active');

            await this.loadMessages(contact);
        } catch (error) {
            console.error('Error handling contact click:', error);
        }
    }

    handleBack() {
        // Show upload button when returning to contacts view
        if (this.elements.uploadForm) {
            this.elements.uploadForm.style.display = 'inline-block';
        }

        this.elements.chatView?.classList.remove('active');
        this.elements.contactsView?.classList.add('active');
        this.currentContact = null;
    }

    async loadMessages(contact) {
        try {
            const response = await fetch(`/messages/${encodeURIComponent(contact)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const messages = await response.json();
            
            if (this.elements.messagesList) {
                const messagesHTML = messages
                    .map(msg => this.createMessageBubble(msg))
                    .join('');
                this.elements.messagesList.innerHTML = messagesHTML;
                this.elements.messagesList.scrollTop = this.elements.messagesList.scrollHeight;
            }
        } catch (error) {
            console.error('Error loading messages:', error);
            if (this.elements.messagesList) {
                this.elements.messagesList.innerHTML = '<div class="alert alert-danger">Failed to load messages</div>';
            }
        }
    }

    createMessageBubble(message) {
        try {
            const formattedTime = new Date(message.time).toLocaleString();
            const bubbleClass = message.sender === this.currentContact ? 'incoming' : 'outgoing';
            
            return `
                <div class="message-bubble message-bubble--${bubbleClass}">
                    <div class="message-text">${this.escapeHtml(message.text || '')}</div>
                    <time class="message-time" datetime="${message.time}">${formattedTime}</time>
                </div>
            `.trim();
        } catch (error) {
            console.error('Error creating message bubble:', error);
            return '';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
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

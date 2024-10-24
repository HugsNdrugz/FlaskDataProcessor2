// Theme management
const THEME_KEY = 'messenger_theme';
const DARK_THEME = 'dark';
const LIGHT_THEME = 'light';

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    setupMessageHandling();
});

function initializeTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY) || DARK_THEME;
    applyTheme(savedTheme);
    
    // Setup theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = localStorage.getItem(THEME_KEY) || DARK_THEME;
            const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
            applyTheme(newTheme);
        });
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    
    // Update toggle button text/icon if it exists
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === DARK_THEME ? 
            '<i class="bi bi-sun"></i> Light Mode' : 
            '<i class="bi bi-moon"></i> Dark Mode';
    }
}

function setupMessageHandling() {
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const messageInput = document.getElementById('messageInput');
            if (messageInput && messageInput.value.trim()) {
                sendMessage(messageInput.value);
                messageInput.value = '';
            }
        });
    }
}

function sendMessage(message) {
    try {
        const messageContainer = document.getElementById('messages');
        if (!messageContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = 'message sent';
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
                <small class="timestamp">${new Date().toLocaleTimeString()}</small>
            </div>
        `;
        
        messageContainer.appendChild(messageElement);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Contact list handling
function loadContacts() {
    try {
        const contactList = document.getElementById('contactList');
        if (!contactList) return;

        fetch('/contacts')
            .then(response => response.json())
            .then(contacts => {
                contactList.innerHTML = contacts.map(contact => `
                    <div class="contact" onclick="selectContact('${escapeHtml(contact.name)}')">
                        <div class="contact-info">
                            <h5>${escapeHtml(contact.name)}</h5>
                            <p class="text-muted">${escapeHtml(contact.phone || '')}</p>
                        </div>
                    </div>
                `).join('');
            })
            .catch(error => console.error('Error loading contacts:', error));
    } catch (error) {
        console.error('Error in loadContacts:', error);
    }
}

function selectContact(contactName) {
    try {
        const chatHeader = document.getElementById('chatHeader');
        if (chatHeader) {
            chatHeader.textContent = contactName;
        }
        
        // Load messages for selected contact
        fetch(`/messages/${encodeURIComponent(contactName)}`)
            .then(response => response.json())
            .then(messages => displayMessages(messages))
            .catch(error => console.error('Error loading messages:', error));
    } catch (error) {
        console.error('Error in selectContact:', error);
    }
}

function displayMessages(messages) {
    try {
        const messageContainer = document.getElementById('messages');
        if (!messageContainer) return;

        messageContainer.innerHTML = messages.map(msg => `
            <div class="message ${msg.is_sent ? 'sent' : 'received'}">
                <div class="message-content">
                    <p>${escapeHtml(msg.message)}</p>
                    <small class="timestamp">${new Date(msg.timestamp).toLocaleTimeString()}</small>
                </div>
            </div>
        `).join('');
        
        messageContainer.scrollTop = messageContainer.scrollHeight;
    } catch (error) {
        console.error('Error displaying messages:', error);
    }
}

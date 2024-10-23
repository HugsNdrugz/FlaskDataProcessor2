document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements with null checks
    const darkModeToggler = document.querySelector(".messages-page__dark-mode-toogler");
    const messageContainer = document.querySelector(".chat__content");
    const messagesPage = document.querySelector(".messages-page");
    const messageForm = document.querySelector(".message-form");
    
    // Initialize touch events for mobile
    let touchStartY = 0;
    let touchEndY = 0;
    
    // Screen resize handler
    function handleResize() {
        if (window.innerWidth <= 768) {
            document.body.classList.add('mobile-view');
        } else {
            document.body.classList.remove('mobile-view');
        }
    }

    // Add resize listener
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    // Dark mode toggle with localStorage
    if (darkModeToggler) {
        darkModeToggler.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            // Save dark mode preference
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });

        // Check for saved dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }

    // Mobile touch events
    if (messageContainer) {
        messageContainer.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        messageContainer.addEventListener('touchmove', (e) => {
            touchEndY = e.touches[0].clientY;
            const deltaY = touchEndY - touchStartY;
            
            if (Math.abs(deltaY) > 10) {
                e.preventDefault();
                messageContainer.scrollTop -= deltaY;
            }
        }, { passive: false });
    }

    // Message timestamps
    function updateMessageTimes() {
        const timestamps = document.querySelectorAll('.message-time');
        timestamps.forEach(timestamp => {
            if (timestamp && timestamp.dataset.time) {
                const time = new Date(timestamp.dataset.time);
                timestamp.textContent = formatMessageTime(time);
            }
        });
    }

    function formatMessageTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return `${Math.floor(minutes/60)}h ago`;
        if (minutes < 10080) return date.toLocaleString('en-US', { weekday: 'short' }); // Within a week
        return date.toLocaleDateString();
    }

    // Handle message form submission
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = this.querySelector('input[name="message"]');
            if (input && input.value.trim()) {
                // Here we would typically send the message to the server
                // For now, just clear the input
                input.value = '';
            }
        });
    }

    // Auto-scroll to bottom on new messages
    function scrollToBottom() {
        if (messageContainer) {
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
    }

    // Initial scroll to bottom
    scrollToBottom();

    // Update times initially and every minute
    updateMessageTimes();
    setInterval(updateMessageTimes, 60000);
});

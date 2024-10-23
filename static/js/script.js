document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements with null checks
    const darkModeToggler = document.querySelector(".messages-page__dark-mode-toogler");
    const messageContainer = document.querySelector(".chat__content");
    const messageForm = document.querySelector(".message-form");
    
    // Initialize touch events for mobile
    let touchStartY = 0;
    let touchEndY = 0;
    
    // Screen resize handler
    function handleResize() {
        if (window.innerWidth <= 768) {
            document.body.classList.add('mobile-view');
            if (messageContainer) {
                messageContainer.style.height = `calc(100vh - ${document.querySelector('.messages-page__header').offsetHeight}px - ${document.querySelector('.message-input-container').offsetHeight}px)`;
            }
        } else {
            document.body.classList.remove('mobile-view');
            if (messageContainer) {
                messageContainer.style.height = '';
            }
        }
    }

    // Add resize listener
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    // Dark mode toggle with localStorage and proper error handling
    if (darkModeToggler) {
        darkModeToggler.addEventListener("click", () => {
            const theme = document.body.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            document.body.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
        });

        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.setAttribute('data-bs-theme', savedTheme);
    }

    // Mobile touch events with proper error handling
    if (messageContainer) {
        messageContainer.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });

        messageContainer.addEventListener('touchmove', (e) => {
            if (!messageContainer.scrollHeight) return;
            
            touchEndY = e.touches[0].clientY;
            const deltaY = touchEndY - touchStartY;
            
            // Only prevent default if we're at the bounds
            const isAtTop = messageContainer.scrollTop <= 0 && deltaY > 0;
            const isAtBottom = messageContainer.scrollTop + messageContainer.clientHeight >= messageContainer.scrollHeight && deltaY < 0;
            
            if (isAtTop || isAtBottom) {
                e.preventDefault();
            }
            
            messageContainer.scrollTop -= deltaY;
            touchStartY = touchEndY;
        }, { passive: false });
    }

    // Message timestamps with proper error handling
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
        if (!date || !(date instanceof Date) || isNaN(date)) return '';
        
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (minutes < 1440) return `${Math.floor(minutes/60)}h ago`;
        if (minutes < 10080) return date.toLocaleString('en-US', { weekday: 'short' }); // Within a week
        return date.toLocaleDateString();
    }

    // Handle message form submission with proper error handling
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = this.querySelector('input[name="message"]');
            if (input && input.value.trim()) {
                // Here we would typically send the message to the server
                // For now, just clear the input
                input.value = '';
                scrollToBottom();
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

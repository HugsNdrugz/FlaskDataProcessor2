// UI Enhancement Functions
class MessengerUI {
    static enhanceScrollBehavior() {
        const containers = document.querySelectorAll('.messages-container, .contacts-list');
        containers.forEach(container => {
            let isScrolling = false;
            let scrollTimeout;

            container.addEventListener('scroll', () => {
                if (!isScrolling) {
                    container.classList.add('is-scrolling');
                    isScrolling = true;
                }

                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    container.classList.remove('is-scrolling');
                    isScrolling = false;
                }, 150);
            });
        });
    }

    static setupRippleEffect() {
        const buttons = document.querySelectorAll('.btn-icon, .nav-link');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const rect = button.getBoundingClientRect();
                const ripple = document.createElement('div');
                ripple.className = 'ripple';
                ripple.style.left = `${e.clientX - rect.left}px`;
                ripple.style.top = `${e.clientY - rect.top}px`;
                button.appendChild(ripple);

                setTimeout(() => ripple.remove(), 1000);
            });
        });
    }

    static enhanceSearchInteraction() {
        const searchInput = document.querySelector('.search-input');
        const searchBar = searchInput.closest('.search-bar');

        searchInput.addEventListener('focus', () => {
            searchBar.classList.add('is-focused');
        });

        searchInput.addEventListener('blur', () => {
            searchBar.classList.remove('is-focused');
        });
    }

    static setupMessageAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.message-bubble').forEach(message => {
            observer.observe(message);
        });
    }

    static enhanceContactInteractions() {
        document.querySelectorAll('.contact-item').forEach(contact => {
            contact.addEventListener('touchstart', () => {
                contact.classList.add('touch-active');
            });

            contact.addEventListener('touchend', () => {
                contact.classList.remove('touch-active');
            });
        });
    }

    static setupTabTransitions() {
        const tabButtons = document.querySelectorAll('.nav-link');
        const indicator = document.createElement('div');
        indicator.className = 'tab-indicator';
        document.querySelector('.nav-tabs').appendChild(indicator);

        function updateIndicator(button) {
            const rect = button.getBoundingClientRect();
            const containerRect = button.parentElement.getBoundingClientRect();

            indicator.style.width = `${rect.width}px`;
            indicator.style.left = `${rect.left - containerRect.left}px`;
        }

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                updateIndicator(button);
            });
        });

        // Initialize indicator position
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab) {
            updateIndicator(activeTab);
        }
    }

    static init() {
        this.enhanceScrollBehavior();
        this.setupRippleEffect();
        this.enhanceSearchInteraction();
        this.setupMessageAnimations();
        this.enhanceContactInteractions();
        this.setupTabTransitions();
    }
}

// Initialize UI enhancements when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    MessengerUI.init();
});

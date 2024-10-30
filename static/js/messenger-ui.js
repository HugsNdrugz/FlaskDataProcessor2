class ChatInterface {
  constructor() {
    console.log("Creating new ChatInterface instance");
    this.initialize();
  }

  initialize() {
    console.log("Initializing ChatInterface...");
    this.initializeDOM();
    this.bindEvents();
  }

  initializeDOM() {
    console.log("Initializing DOM elements...");
    this.contactsView = document.querySelector('.contacts-view');
    this.chatView = document.querySelector('.chat-view');
    this.backButton = document.querySelector('.back-button');
    this.themeToggle = document.querySelector('#themeToggle');
    this.contacts = document.querySelector('.contacts-list');
    this.messagesList = document.querySelector('.messages-list');
    this.messagesContainer = document.querySelector('.messages-container');
    this.searchInput = document.querySelector('.search-input');
    this.chatHeader = document.querySelector('.chat-header');
    this.onlineStatus = document.querySelector('.online-status');
    this.tabButtons = document.querySelectorAll('.nav-link');
    this.loadingSpinner = document.querySelector('.loading-spinner');

    // Log successful initialization for each element
    [
      ['contactsView', this.contactsView],
      ['chatView', this.chatView],
      ['backButton', this.backButton],
      ['themeToggle', this.themeToggle],
      ['contacts', this.contacts],
      ['messagesList', this.messagesList],
      ['messagesContainer', this.messagesContainer],
      ['searchInput', this.searchInput],
      ['chatHeader', this.chatHeader],
      ['onlineStatus', this.onlineStatus],
      ['tabButtons', this.tabButtons],
      ['loadingSpinner', this.loadingSpinner]
    ].forEach(([name, element]) => {
      console.log(`Element "${name}" initialized ${element ? 'successfully' : 'failed'}`);
    });
  }

  bindEvents() {
    console.log("Binding events...");
    
    // Ripple effect for clickable elements
    document.querySelectorAll('.contact-item, .btn-icon, .nav-link').forEach(element => {
      element.addEventListener('click', this.createRippleEffect.bind(this));
    });

    // Long press handling for messages
    if (this.messagesList) {
      this.messagesList.addEventListener('touchstart', this.handleTouchStart.bind(this));
      this.messagesList.addEventListener('touchend', this.handleTouchEnd.bind(this));
      this.messagesList.addEventListener('touchmove', this.handleTouchMove.bind(this));
    }

    // Swipe handling for mobile view
    if (this.contactsView && this.chatView) {
      this.contactsView.addEventListener('touchstart', this.handleSwipeStart.bind(this));
      this.contactsView.addEventListener('touchmove', this.handleSwipeMove.bind(this));
      this.contactsView.addEventListener('touchend', this.handleSwipeEnd.bind(this));
    }

    // Theme toggle
    if (this.themeToggle) {
      this.themeToggle.addEventListener('change', this.handleThemeToggle.bind(this));
    }

    console.log("Events bound successfully");
  }

  createRippleEffect(event) {
    const element = event.currentTarget;
    const ripple = element.querySelector('.ripple');
    
    if (ripple) {
      ripple.remove();
    }

    element.classList.add('ripple');
    setTimeout(() => {
      element.classList.remove('ripple');
    }, 600);
  }

  handleTouchStart(event) {
    if (!event.target.closest('.message-bubble')) return;
    
    this.touchStartTime = Date.now();
    this.touchStartY = event.touches[0].clientY;
    this.touchStartX = event.touches[0].clientX;
    this.longPressTimer = setTimeout(() => {
      this.handleLongPress(event.target.closest('.message-bubble'));
    }, 500);
  }

  handleTouchMove(event) {
    if (!this.touchStartY) return;
    
    const deltaY = Math.abs(event.touches[0].clientY - this.touchStartY);
    const deltaX = Math.abs(event.touches[0].clientX - this.touchStartX);
    
    if (deltaY > 10 || deltaX > 10) {
      clearTimeout(this.longPressTimer);
      this.touchStartY = null;
      this.touchStartX = null;
    }
  }

  handleTouchEnd() {
    clearTimeout(this.longPressTimer);
    this.touchStartY = null;
    this.touchStartX = null;
  }

  handleLongPress(messageBubble) {
    messageBubble.classList.add('show-options');
    
    const removeOptions = (event) => {
      if (!messageBubble.contains(event.target)) {
        messageBubble.classList.remove('show-options');
        document.removeEventListener('click', removeOptions);
      }
    };
    
    document.addEventListener('click', removeOptions);
  }

  handleSwipeStart(event) {
    this.swipeStartX = event.touches[0].clientX;
  }

  handleSwipeMove(event) {
    if (!this.swipeStartX) return;
    
    const currentX = event.touches[0].clientX;
    const diff = this.swipeStartX - currentX;
    
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        this.contactsView.classList.add('slide-left');
        this.chatView.classList.remove('slide-right');
      } else {
        this.chatView.classList.add('slide-right');
        this.contactsView.classList.remove('slide-left');
      }
    }
  }

  handleSwipeEnd() {
    this.swipeStartX = null;
  }

  handleThemeToggle(event) {
    document.body.setAttribute('data-theme', event.target.checked ? 'dark' : 'light');
    localStorage.setItem('theme', event.target.checked ? 'dark' : 'light');
  }
}

// Initialize the chat interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const chat = new ChatInterface();
});

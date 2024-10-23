document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggler = document.querySelector(".messages-page__dark-mode-toogler");
    
    // Dark mode toggle
    if (darkModeToggler) {
        darkModeToggler.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
        });
    }
});

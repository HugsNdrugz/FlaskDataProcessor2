// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const $chat = document.querySelector(".chat");
    const $profile = document.querySelector(".user-profile");
    const $darkModeToggler = document.querySelector(".messages-page__dark-mode-toogler");
    
    /* Screen resize handler */
    function handleDeviceChange(e) {
        if (e.matches && $chat) {
            $chat.classList.add("chat--mobile");
        } else if ($chat) {
            $chat.classList.remove("chat--mobile");
        }
    }

    function handleLargeScreenChange(e) {
        if (e.matches && $profile) {
            $profile.classList.add("user-profile--large");
        } else if ($profile) {
            $profile.classList.remove("user-profile--large");
        }
    }

    // Add media query listeners
    const smallDevice = window.matchMedia("(max-width: 767px)");
    const largeScreen = window.matchMedia("(max-width: 1199px)");
    
    try {
        // Modern browsers
        smallDevice.addEventListener("change", handleDeviceChange);
        largeScreen.addEventListener("change", handleLargeScreenChange);
    } catch (e1) {
        try {
            // Fallback for older browsers
            smallDevice.addListener(handleDeviceChange);
            largeScreen.addListener(handleLargeScreenChange);
        } catch (e2) {
            console.warn('Media queries not fully supported');
        }
    }

    // Initial check
    handleDeviceChange(smallDevice);
    handleLargeScreenChange(largeScreen);

    /* Click event handlers */
    document.querySelectorAll(".messaging-member").forEach(member => {
        member.addEventListener("click", () => {
            if ($chat) {
                $chat.style.display = 'block';
                $chat.classList.add("chat--show");
            }
        });
    });

    document.querySelectorAll(".chat__previous").forEach(btn => {
        btn.addEventListener("click", () => {
            if ($chat) {
                $chat.classList.remove("chat--show");
            }
        });
    });

    // Dark mode toggle
    if ($darkModeToggler) {
        $darkModeToggler.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
        });
    }
});

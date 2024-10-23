document.addEventListener('DOMContentLoaded', function() {
    const chat = document.querySelector(".chat");
    const profile = document.querySelector(".user-profile");
    const darkModeToggler = document.querySelector(".messages-page__dark-mode-toogler");
    
    /* Screen resize handler */
    function handleDeviceChange(e) {
        if (chat && e.matches) {
            chat.classList.add("chat--mobile");
        } else if (chat) {
            chat.classList.remove("chat--mobile");
        }
    }

    function handleLargeScreenChange(e) {
        if (profile && e.matches) {
            profile.classList.add("user-profile--large");
        } else if (profile) {
            profile.classList.remove("user-profile--large");
        }
    }

    // Add media query listeners
    const smallDevice = window.matchMedia("(max-width: 767px)");
    const largeScreen = window.matchMedia("(max-width: 1199px)");
    
    if (smallDevice) {
        if (smallDevice.addEventListener) {
            smallDevice.addEventListener("change", handleDeviceChange);
        } else {
            // Fallback for older browsers
            smallDevice.addListener(handleDeviceChange);
        }
        handleDeviceChange(smallDevice);
    }
    
    if (largeScreen) {
        if (largeScreen.addEventListener) {
            largeScreen.addEventListener("change", handleLargeScreenChange);
        } else {
            // Fallback for older browsers
            largeScreen.addListener(handleLargeScreenChange);
        }
        handleLargeScreenChange(largeScreen);
    }

    // Dark mode toggle
    if (darkModeToggler) {
        darkModeToggler.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
        });
    }
});

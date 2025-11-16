// Use CSS hover with smart positioning to ensure dropdown is always visible
document.addEventListener('DOMContentLoaded', function() {
    // Close all menus when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.more-actions-dropdown')) {
            const menus = document.querySelectorAll('.more-actions-menu');
            menus.forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });
    
    // Position dropdowns to ensure they're fully visible
    function positionDropdown(dropdown) {
        const menu = dropdown.querySelector('.more-actions-menu');
        if (!menu) return;
        
        const dropdownRect = dropdown.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        // Reset position
        menu.style.left = 'auto';
        menu.style.right = 'auto';
        menu.style.top = 'auto';
        menu.style.bottom = 'auto';
        
        // Check if menu would overflow on the right
        if (dropdownRect.left + menuRect.width > windowWidth - 10) {
            // Position from right edge instead
            menu.style.left = 'auto';
            menu.style.right = '0';
        } else {
            // Position from left edge (default)
            menu.style.left = '0';
            menu.style.right = 'auto';
        }
        
        // Check if menu would overflow on the bottom
        if (dropdownRect.bottom + menuRect.height > windowHeight - 10) {
            // Position above the button instead
            menu.style.top = 'auto';
            menu.style.bottom = '100%';
            menu.style.marginTop = '0';
            menu.style.marginBottom = '4px';
        } else {
            // Position below the button (default)
            menu.style.top = '100%';
            menu.style.bottom = 'auto';
            menu.style.marginTop = '4px';
            menu.style.marginBottom = '0';
        }
    }
    
    // Ensure dropdown stays open when hovering over it
    const dropdowns = document.querySelectorAll('.more-actions-dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('mouseenter', function() {
            const menu = this.querySelector('.more-actions-menu');
            if (menu) {
                // Position the menu before showing
                positionDropdown(this);
                menu.style.display = 'block';
                // Reposition after display to get accurate measurements
                setTimeout(() => positionDropdown(this), 0);
            }
        });
        
        dropdown.addEventListener('mouseleave', function(e) {
            const menu = this.querySelector('.more-actions-menu');
            // Check if mouse is moving to the menu
            if (menu && !menu.contains(e.relatedTarget)) {
                menu.style.display = 'none';
            }
        });
        
        // Keep menu open when hovering over it
        const menu = dropdown.querySelector('.more-actions-menu');
        if (menu) {
            menu.addEventListener('mouseenter', function() {
                this.style.display = 'block';
            });
            
            menu.addEventListener('mouseleave', function() {
                this.style.display = 'none';
            });
        }
    });
    
    // Reposition on window resize
    window.addEventListener('resize', function() {
        dropdowns.forEach(dropdown => {
            const menu = dropdown.querySelector('.more-actions-menu');
            if (menu && menu.style.display === 'block') {
                positionDropdown(dropdown);
            }
        });
    });
});


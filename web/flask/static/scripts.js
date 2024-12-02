document.addEventListener('DOMContentLoaded', () => {
    // menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            
            if (navMenu.classList.contains('show')) {
                // start slide-out animation
                navMenu.classList.remove('show');
                navMenu.classList.add('hide');
                
                // after animation ends, hide the menu
                navMenu.addEventListener('animationend', function handler() {
                    navMenu.style.display = 'none';
                    navMenu.classList.remove('hide');
                    navMenu.removeEventListener('animationend', handler);
                });
            } else {
                // display menu and start slide-in animation
                navMenu.style.display = 'flex';
                navMenu.classList.add('show');
            }
        });
    }

    // TODO:dont really work, need to fix
    // page transitions
    const overlay = document.querySelector('.page-overlay');
    
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', e => {
            // only handle internal links
            if (link.hostname === window.location.hostname) {
                e.preventDefault();
                overlay.style.opacity = '1';
                
                setTimeout(() => {
                    window.location.href = link.href;
                }, 300);
            }
        });
    });

    // fade in on page load
    window.addEventListener('pageshow', () => {
        overlay.style.opacity = '0';
    });
});
